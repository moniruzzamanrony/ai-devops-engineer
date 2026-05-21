import shutil
import sys
import datetime
import json
import re
import time
from collections import deque

from app.config.hugging_face_client import call_hf_messages
from app.core.config import SERVER_HOST, SERVER_PORT, SERVER_USERNAME, SERVER_PASSWORD
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
        "FIX": "🔧",
        "OK": "✅",
    }

    icon = level_icons.get(level, "•")

    print(f"{prefix}{icon} [{timestamp}] [{level}] {message}")

# ============================================================
# GLOBAL QUEUE
# ============================================================

ai_instruction_queue = deque()

# ============================================================
# AI CALL WITH CHUNKED CONTINUATION
# ============================================================

MAX_CONTINUATION_CHUNKS = 6  # safety cap on follow-up calls

def call_with_continuation(prompt: str):
    """Call the model and auto-continue when finish_reason == 'length'.

    Each request keeps the original max_tokens budget; we stitch together
    multiple responses by feeding the partial reply back as the assistant
    turn and asking the model to continue from where it stopped.

    Returns (concatenated_content, last_finish_reason).
    """
    messages = [{"role": "user", "content": prompt}]
    accumulated = ""

    for chunk_idx in range(MAX_CONTINUATION_CHUNKS):
        res = call_hf_messages(messages)

        try:
            piece = res["choices"][0]["message"]["content"] or ""
        except Exception:
            log(f"Unexpected AI response shape: {res}", "ERROR")
            return accumulated, "error"

        accumulated += piece
        finish_reason = res.get("choices", [{}])[0].get("finish_reason")

        if finish_reason != "length":
            if chunk_idx > 0:
                log(f"Stitched {chunk_idx + 1} chunks into a complete response", "INFO")
            return accumulated, finish_reason

        log(f"Chunk {chunk_idx + 1} hit token cap, requesting continuation...", "WARN")
        messages.append({"role": "assistant", "content": piece})
        messages.append({
            "role": "user",
            "content": (
                "Your previous reply was cut off mid-output. "
                "Continue from EXACTLY the character where you stopped. "
                "Do NOT repeat any earlier text, do NOT add a preface, do NOT wrap in markdown. "
                "Output only the remaining characters so that concatenating your previous reply "
                "and this reply yields a single valid JSON array."
            ),
        })

    return accumulated, "length"

# ============================================================
# MAIN PIPELINE
# ============================================================

MAX_FIX_DEPTH = 5  # safety cap on fix-cycle recursion


# Errors that no fix cycle can repair — the operator must change config / credentials.
# A match here short-circuits the fix cycle with an actionable message instead of
# burning retries on something the AI cannot solve.
UNFIXABLE_PATTERNS = [
    ("Invalid username or token",            "GitHub credentials are invalid. Update GIT_ACCESS_TOKEN in .env with a fresh personal access token."),
    ("Password authentication is not supported", "GitHub requires a personal access token. Update GIT_ACCESS_TOKEN in .env."),
    ("Authentication failed for 'https://github.com", "GitHub auth failed. Update GIT_ACCESS_TOKEN in .env."),
    ("could not read Username for",          "GitHub credentials missing or malformed in .env (GIT_USERNAME / GIT_ACCESS_TOKEN)."),
    ("Permission denied (publickey)",        "SSH key auth rejected by the remote. Add your key to the server or check .env."),
    ("Permission denied, please try again",  "SSH password rejected. Check SERVER_PASSWORD in .env."),
    ("ssh: connect to host",                 "Cannot reach the deploy server. Check SERVER_HOST / SERVER_PORT in .env and network connectivity."),
    ("Could not resolve host",               "DNS lookup failed. Check the host value in .env and the network."),
    ("Connection refused",                   "The target host refused the connection. Check that SSH is running on SERVER_PORT."),
    ("Host key verification failed",         "Remote host key mismatch. Remove the stale entry from ~/.ssh/known_hosts or trust the new host."),
]


def _classify_unfixable(errors):
    """Return an operator-facing message if any error matches an unfixable pattern."""
    for item in errors:
        err = item.get("error") or ""
        for pattern, advice in UNFIXABLE_PATTERNS:
            if pattern in err:
                return advice, item
    return None, None


def do_it(prompt: str, deferred_steps=None, depth: int = 0):
    """Run a deploy plan from the AI.

    deferred_steps: steps preserved from a previous run that failed partway through.
        These are appended AFTER the AI's freshly returned steps and executed once
        the current plan finishes — so a fix cycle's repair runs first, then the
        original work resumes.
    depth: fix-cycle recursion depth. Capped by MAX_FIX_DEPTH to avoid loops
        where the fix keeps failing.
    """
    log("=== START DEVOPS PROCESS ===", "START")

    global prompt_temp
    prompt_temp = prompt

    # -----------------------------
    # Step 1: Call AI (with chunked continuation on truncation)
    # -----------------------------
    log("Sending prompt to AI...", "INFO")
    content, finish_reason = call_with_continuation(prompt)
    if finish_reason == "length":
        log("AI response still truncated after continuation budget", "WARN")

    # -----------------------------
    # Step 2: Parse + validate against DeploymentStep schema (retries inside)
    # -----------------------------
    steps = parse_ai_instructions(content)
    log(f"Validated steps: {len(steps)}", "INFO")

    if not steps and not deferred_steps:
        log("No valid steps returned by AI and no deferred work", "ERROR")
        return False

    # -----------------------------
    # Step 3: Queue AI steps, then deferred steps from prior failure
    # -----------------------------
    for step in steps:
        log(f"Queued step: {step.label} ({len(step.cmd)} cmd, verify={'yes' if step.verify_cmd else 'no'})", "QUEUE")
        ai_instruction_queue.append(step)
    if deferred_steps:
        log(f"Re-queueing {len(deferred_steps)} deferred step(s) to resume after this plan", "QUEUE")
        for step in deferred_steps:
            log(f"Queued (deferred): {step.label} ({len(step.cmd)} cmd, verify={'yes' if step.verify_cmd else 'no'})", "QUEUE")
            ai_instruction_queue.append(step)
    log("\n\n")

    # -----------------------------
    # Step 4: Execute steps sequentially; on first failure, save the rest
    # for replay AFTER the fix cycle, then halt this run. Each step must
    # SUCCEED (exit 0) before the next is dispatched.
    # -----------------------------
    remaining_after_failure = []
    total_steps = len(ai_instruction_queue)
    step_index = 0
    while ai_instruction_queue:
        step: DeploymentStep = ai_instruction_queue.popleft()
        step_index += 1
        log(f"--- Running step {step_index}/{total_steps}: {step.label} ---", "CMD")

        step_ok = True
        for cmd in step.cmd:
            if not _run_one(cmd, step.label, phase="cmd"):
                step_ok = False
                break

        if step_ok and step.verify_cmd:
            if not _run_one(step.verify_cmd, step.label, phase="verify"):
                step_ok = False

        if not step_ok:
            remaining_after_failure = list(ai_instruction_queue)
            ai_instruction_queue.clear()
            log(
                f"Pausing pipeline at step {step_index}/{total_steps} '{step.label}'. "
                f"Deferring {len(remaining_after_failure)} remaining step(s) — they will resume after the fix cycle.",
                "ERROR",
            )
            break

        # Explicit success gate — only reached when every cmd (and verify_cmd) in the
        # step returned exit 0. Makes the sequential success-gating visible in the log.
        log(f"Step {step_index}/{total_steps} '{step.label}' completed; advancing to next step", "OK")

    log("=== DEVOPS PIPELINE COMPLETED ===", "END")

    # -----------------------------
    # Step 5: If there were errors, run a fix cycle. The deferred remaining
    # steps are carried forward so they execute once the fix completes.
    # -----------------------------
    if error_block:
        local_errors = list(error_block)
        error_block.clear()

        # Short-circuit on errors the AI cannot fix (bad credentials, network, host
        # key, etc). Burning 5 fix attempts on these wastes time and api budget.
        advice, offending = _classify_unfixable(local_errors)
        if advice:
            log(f"Unfixable error in step '{offending.get('step')}': {offending.get('error', '').splitlines()[0] if offending.get('error') else ''}", "ERROR")
            log(f"ACTION REQUIRED: {advice}", "ERROR")
            log(f"Abandoning {len(remaining_after_failure)} deferred step(s) — they cannot proceed until this is resolved.", "ERROR")
            return False

        if depth >= MAX_FIX_DEPTH:
            log(
                f"Max fix-cycle depth ({MAX_FIX_DEPTH}) reached; abandoning "
                f"{len(remaining_after_failure)} deferred step(s).",
                "ERROR",
            )
            return False

        log(f"Triggering fix cycle for {len(local_errors)} error(s) "
            f"(depth {depth + 1}/{MAX_FIX_DEPTH})...", "FIX")
        fix_prompt = generate_error_fix_prompt(local_errors)
        do_it(fix_prompt, deferred_steps=remaining_after_failure, depth=depth + 1)
    elif remaining_after_failure:
        # Failure happened but nothing landed in error_block (rare).
        # Skip the AI and just re-run the queue with the deferred steps.
        log(f"Resuming {len(remaining_after_failure)} deferred step(s) without fix cycle", "INFO")
        for s in remaining_after_failure:
            ai_instruction_queue.append(s)
        _execute_queue(depth=depth + 1)

    return True


def _execute_queue(depth: int = 0):
    """Drain the instruction queue with the same halt-and-defer semantics as do_it,
    but without calling the AI. Used to resume deferred work when no fix cycle
    is needed.
    """
    remaining_after_failure = []
    total_steps = len(ai_instruction_queue)
    step_index = 0
    while ai_instruction_queue:
        step: DeploymentStep = ai_instruction_queue.popleft()
        step_index += 1
        log(f"--- Running step {step_index}/{total_steps}: {step.label} ---", "CMD")
        step_ok = True
        for cmd in step.cmd:
            if not _run_one(cmd, step.label, phase="cmd"):
                step_ok = False
                break
        if step_ok and step.verify_cmd:
            if not _run_one(step.verify_cmd, step.label, phase="verify"):
                step_ok = False
        if not step_ok:
            remaining_after_failure = list(ai_instruction_queue)
            ai_instruction_queue.clear()
            log(
                f"Pausing pipeline at step {step_index}/{total_steps} '{step.label}'. "
                f"Deferring {len(remaining_after_failure)} remaining step(s) — they will resume after the fix cycle.",
                "ERROR",
            )
            break
        log(f"Step {step_index}/{total_steps} '{step.label}' completed; advancing to next step", "OK")

    if error_block and depth < MAX_FIX_DEPTH:
        local_errors = list(error_block)
        error_block.clear()
        log(f"Triggering fix cycle for {len(local_errors)} error(s) "
            f"(depth {depth + 1}/{MAX_FIX_DEPTH})...", "FIX")
        fix_prompt = generate_error_fix_prompt(local_errors)
        do_it(fix_prompt, deferred_steps=remaining_after_failure, depth=depth + 1)


def _ensure_ssh_wrapped(cmd: str) -> str:
    """The model emits only the REMOTE shell command. This wraps it with sshpass+ssh
    for transport. Single quotes around the remote payload prevent the LOCAL shell
    from expanding $VAR / $(...) — those must reach the server unevaluated.

    Literal single quotes inside the payload are escaped via the close-escape-reopen
    dance ('\\''). A model output that already starts with `sshpass` is passed
    through unchanged.

    Also normalises `\\$` -> `$`: the 7B model occasionally over-defensively
    escapes dollar signs (e.g. emits `\\$PORT` instead of `$PORT`). The single-
    quote wrapping already preserves `$` from local-shell expansion, so the
    backslash is unwanted noise — and worse, on the remote it makes the `$` literal,
    breaking variable references like `-p \\$PORT:\\$PORT` (docker sees the
    raw string and fails).
    """
    if cmd.lstrip().startswith("sshpass"):
        return cmd
    cmd = cmd.replace("\\$", "$")
    escaped = cmd.replace("'", "'\\''")
    return (
        f"sshpass -p '{SERVER_PASSWORD}' ssh -o StrictHostKeyChecking=no "
        f"-p {SERVER_PORT} {SERVER_USERNAME}@{SERVER_HOST} '{escaped}'"
    )


def _run_one(cmd: str, step_label: str, phase: str) -> bool:
    """Execute one command. Returns True on success (exit 0), False on failure.

    Failure is decided by the process exit code — NOT by the presence of stderr
    output, because docker/git/nginx/certbot routinely emit progress on stderr
    during a successful run. On failure, the error is appended to error_block
    for the downstream fix cycle.
    """
    try:
        cmd = _ensure_ssh_wrapped(cmd)
        log(f"Executing ({phase}): {cmd}", "CMD")
        if not is_valid_command(cmd):
            log(f"Invalid command from model: {cmd}", "ERROR")
            error_block.append({
                "step": step_label,
                "phase": phase,
                "run_cmd": cmd,
                "error": "Local executable not found",
            })
            return False

        result = run_command(cmd)
        if result.get('exit_status') != 0:
            log(f"Step failed (exit {result.get('exit_status')}): {result.get('error')}", "ERROR")
            error_block.append({
                "step": step_label,
                "phase": phase,
                "run_cmd": cmd,
                "error": result.get('error'),
            })
            return False

        log(f"Output: {result.get('output')}", "RESULT")
        return True
    except Exception as e:
        log(f"Execution failed: {e}", "ERROR")
        error_block.append({
            "step": step_label,
            "phase": phase,
            "run_cmd": cmd,
            "error": str(e),
        })
        return False
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

        # 3. Re-prompt with the schema spelled out (chunked continuation on truncation)
        log(f"Re-prompting AI for DeploymentStep schema (attempt {attempt}/{max_retries})...", "WARN")
        retry_prompt = _build_schema_retry_prompt(cleaned)
        cleaned, finish_reason = call_with_continuation(retry_prompt)
        cleaned = re.sub(r"```json|```", "", cleaned).strip()
        cleaned = fix_invalid_json_escapes(cleaned)

        if finish_reason == "length":
            log("AI response still truncated after continuation budget", "WARN")

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
