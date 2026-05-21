import shutil
import sys
import datetime
import json
import re
import time
from collections import deque

from app.config.hugging_face_client import call_hf
from app.dto.deployment_step import DeploymentStep, parse_steps, ValidationError
from app.tools.run_cmd import run_command
from app.utils.prompt_text import generate_result_analysis_prompt, generate_error_fix_prompt, get_valid_json_response

prompt_temp = None
error_block =[]
# ============================================================
# CONFIG
# ============================================================

COMMAND_DELAY_SECONDS = 2  # delay between commands

# ============================================================
# LOGGER
# ============================================================

def log(message: str, level: str = "INFO", indent: int = 0):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = "  " * indent

    level_icons = {
        "START": "🚀",
        "END": "🏁",
        "INFO": "ℹ️",
        "WARN": "⚠️",
        "ERROR": "❌",
        "CMD": "💻",
        "RESULT": "📦",
        "QUEUE": "📥",
        "FIX": "🔧"
    }

    icon = level_icons.get(level, "•")

    print(f"{prefix}{icon} [{timestamp}] [{level}] {message}")

# ============================================================
# GLOBAL QUEUE
# ============================================================

ai_instruction_queue = deque()

# ============================================================
# MAIN PIPELINE
# ============================================================

def do_it(prompt: str):
    log("=== START DEVOPS PROCESS ===", "START")

    global prompt_temp
    prompt_temp = prompt

    # -----------------------------
    # Step 1: Call AI
    # -----------------------------
    log("Sending prompt to AI...", "INFO")
    res = call_hf(prompt)

    finish_reason = res.get("choices", [{}])[0].get("finish_reason")
    if finish_reason == "length":
        log("AI response truncated", "WARN")

    try:
        content = res["choices"][0]["message"]["content"]
    except Exception:
        content = str(res)

    # -----------------------------
    # Step 2: Parse + validate against DeploymentStep schema (retries inside)
    # -----------------------------
    steps = parse_ai_instructions(content)
    log(f"Validated steps: {len(steps)}", "INFO")

    if not steps:
        log("No valid steps returned by AI after retries", "ERROR")
        return False

    # -----------------------------
    # Step 3: Queue steps
    # -----------------------------
    for step in steps:
        log(f"Queued step: {step.label} ({len(step.cmd)} cmd, verify={'yes' if step.verify_cmd else 'no'})", "QUEUE")
        ai_instruction_queue.append(step)
    log("\n\n")

    # -----------------------------
    # Step 4: Execute steps
    # -----------------------------
    while ai_instruction_queue:
        step: DeploymentStep = ai_instruction_queue.popleft()
        log(f"--- Running step: {step.label} ---", "CMD")

        for cmd in step.cmd:
            _run_one(cmd, step.label, phase="cmd")

        if step.verify_cmd:
            _run_one(step.verify_cmd, step.label, phase="verify")

    log("=== DEVOPS PIPELINE COMPLETED ===", "END")

    # -----------------------------
    # Step 5: Loop back to AI with any errors
    # -----------------------------
    if error_block:
        local_errors = list(error_block)
        error_block.clear()
        log(f"Triggering fix cycle for {len(local_errors)} error(s)...", "FIX")
        fix_prompt = generate_error_fix_prompt(local_errors)
        do_it(fix_prompt)

    return True


def _run_one(cmd: str, step_label: str, phase: str):
    """Execute one command, recording any failure into the module-level error_block."""
    try:
        log(f"Executing ({phase}): {cmd}", "CMD")
        if not is_valid_command(cmd):
            log(f"Invalid command from model: {cmd}", "ERROR")
            error_block.append({
                "step": step_label,
                "phase": phase,
                "run_cmd": cmd,
                "error": "Local executable not found",
            })
            return

        result = run_command(cmd)
        if result.get('error'):
            error_block.append({
                "step": step_label,
                "phase": phase,
                "run_cmd": cmd,
                "error": result.get('error'),
            })
        log(f"Output: {result.get('output')}", "RESULT")
    except Exception as e:
        log(f"Execution failed: {e}", "ERROR")
        error_block.append({
            "step": step_label,
            "phase": phase,
            "run_cmd": cmd,
            "error": str(e),
        })
    finally:
        time.sleep(COMMAND_DELAY_SECONDS)

# ============================================================
# COMMAND VALIDATION
# ============================================================

def is_valid_command(cmd: str) -> bool:
    parts = cmd.strip().split()
    if not parts:
        return False

    command_name = parts[0]
    return shutil.which(command_name) is not None

# ============================================================
# PARSER
# ============================================================

import json
import re

def parse_ai_instructions(content: str, max_retries: int = 5):
    """Parse + validate AI content against the DeploymentStep schema.

    Re-prompts the AI up to `max_retries` times when the response is invalid JSON or
    fails DeploymentStep validation. Returns a list[DeploymentStep] on success, or []
    when the retry budget is exhausted.
    """
    if not content:
        log("No AI content received", "WARN")
        return []

    cleaned = re.sub(r"```json|```", "", content).strip()
    cleaned = fix_invalid_json_escapes(cleaned)

    for attempt in range(1, max_retries + 1):
        # 1. Try direct parse + DTO validation
        steps = _try_parse_steps(cleaned)
        if steps is not None:
            log(f"DeploymentStep schema satisfied on attempt {attempt} ({len(steps)} steps)", "INFO")
            return steps

        # 2. Fallback: extract the outer [...] substring and retry validation
        start, end = cleaned.find('['), cleaned.rfind(']')
        if start != -1 and end != -1 and end > start:
            candidate = cleaned[start:end + 1].replace("\r", "").strip()
            candidate = re.sub(r",\s*}", "}", candidate)
            candidate = re.sub(r",\s*]", "]", candidate)
            steps = _try_parse_steps(candidate)
            if steps is not None:
                log(f"DeploymentStep schema satisfied via fallback on attempt {attempt} ({len(steps)} steps)", "INFO")
                return steps

        if attempt == max_retries:
            break

        # 3. Re-prompt with the schema spelled out
        log(f"Re-prompting AI for DeploymentStep schema (attempt {attempt}/{max_retries})...", "WARN")
        retry_prompt = _build_schema_retry_prompt(cleaned)
        res = call_hf(retry_prompt)

        try:
            cleaned = res["choices"][0]["message"]["content"]
        except Exception:
            cleaned = str(res)
        cleaned = re.sub(r"```json|```", "", cleaned).strip()
        cleaned = fix_invalid_json_escapes(cleaned)

        finish_reason = res.get("choices", [{}])[0].get("finish_reason")
        if finish_reason == "length":
            log("AI response truncated", "WARN")

    log(f"Failed to obtain valid DeploymentStep[] after {max_retries} attempts", "ERROR")
    return []


def _try_parse_steps(text: str):
    """Return a list[DeploymentStep] on success, or None on parse/validation failure."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        log(f"JSON parse failed: {e}", "ERROR")
        return None

    data = normalize_output(data)

    try:
        return parse_steps(data)
    except (ValidationError, ValueError) as e:
        log(f"DTO validation failed: {e}", "ERROR")
        return None


def _build_schema_retry_prompt(previous: str) -> str:
    return f"""
Your previous response did not match the required schema.

You MUST return ONLY a JSON array whose elements match this exact schema:

[
  {{
    "label": "<short human-readable name>",
    "cmd": ["<command1>", "<command2>"],
    "verify_cmd": "<command that confirms the step succeeded>"
  }}
]

Constraints:
- "label" must be a non-empty string
- "cmd" must be a non-empty array of strings
- "verify_cmd" must be a string
- No markdown, no explanations, no extra text
- Response must start with [ and end with ]

Fix your previous response and return ONLY the valid JSON array.

Previous response:
{previous}
"""

# ============================================================
# NORMALIZER
# ============================================================

def normalize_output(data):
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        # A single step object (has the DTO keys) -> wrap it in a list.
        if "label" in data and "cmd" in data:
            return [data]
        # A wrapper object like {"steps": [...]} -> unwrap the first list value.
        for value in data.values():
            if isinstance(value, list):
                return value
        return [data]

    return []

# ============================================================
# ESCAPE FIXER
# ============================================================

def fix_invalid_json_escapes(text: str):
    if not text:
        return text

    text = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)
    return text
