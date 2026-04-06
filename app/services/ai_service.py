import shutil
import sys
import datetime
import json
import re
import time
from collections import deque

from app.config.hugging_face_client import call_hf
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

def ask_devops(prompt: str):
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
        log("⚠️ AI response truncated", "WARN")

    try:
        content = res["choices"][0]["message"]["content"]
    except Exception:
        content = str(res)

    # -----------------------------
    # Step 2: Parse Instructions
    # -----------------------------
    instructions = parse_ai_instructions(content)
    log(f"Parsed instructions count: {len(instructions)}", "INFO")

    if len(instructions) == 0:
        log("Instructions count is 0: Retrying", "ERROR")
        ask_devops(prompt_temp)
        return None

    # -----------------------------
    # Step 3: Queue Instructions
    # -----------------------------
    for instruction in instructions:
        log(f"Queued command: {instruction}", "QUEUE")
        ai_instruction_queue.append(instruction)

    # -----------------------------
    # Step 4: Execute Instructions
    # -----------------------------
    while ai_instruction_queue:
        cmd = ai_instruction_queue.popleft()

        try:
            log(f"\n\nExecuting command: {cmd}", "CMD")

            if is_valid_command(cmd):
                result = run_command(cmd)
                if result.get('error') is not "":
                    error_block.append({
                        "run_cmd":cmd,
                        "error": result.get('error')
                    })
                log(f"Command success: {result.get('output')}", "RESULT")
            else:
                log("Invalid command from model", "ERROR")
                sys.exit(1)

            # Delay between commands
            time.sleep(COMMAND_DELAY_SECONDS)

        except Exception as e:
            log(f"Command execution failed: {e}", "ERROR")

    log("=== DEVOPS PIPELINE COMPLETED ===", "END")

    if error_block:
        error_block_prompt = generate_error_fix_prompt(error_block)
        ask_devops(error_block_prompt)
    return True

# # ============================================================
# # EXECUTION ENGINE
# # ============================================================
#
# import time
#
# def execute_cmd(cmd: str, depth=0):
#     indent = depth
#
#     log(f"Executing command: {cmd}", "CMD", indent)
#
#     try:
#         res = run_command(cmd)
#
#         if not res or not isinstance(res, dict):
#             log("Command returned invalid or empty result", "ERROR", indent)
#             return {
#                 "output": "",
#                 "error": "Invalid command result",
#                 "exit_status": -1
#             }
#
#         log(f"Command output: {res}", "RESULT", indent)
#
#         # Success
#         if res.get("error") == "":
#             return {
#                 "output": res.get("output", ""),
#                 "error": "",
#                 "exit_status": 0
#             }
#
#         # Error case
#         return {
#             "output": res.get("output", ""),
#             "error": res.get("error", ""),
#             "exit_status": res.get("exit_status", -1)
#         }
#
#     except Exception as e:
#         log(f"Exception while executing command: {str(e)}", "ERROR", indent)
#         return {
#             "output": "",
#             "error": str(e),
#             "exit_status": -1
#         }

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

def parse_ai_instructions(content: str, max_retries=3):
    if not content:
        log("No AI content received", "WARN")
        return []

    log(f"Requested content: {content}", "INFO")

    cleaned = re.sub(r"```json|```", "", content).strip()
    cleaned = fix_invalid_json_escapes(cleaned)

    for attempt in range(max_retries):

        # ------------------------
        # 1. Direct JSON parse
        # ------------------------
        try:
            data = json.loads(cleaned)
            log("Direct JSON parsed successfully", "INFO")
            return normalize_output(data)

        except Exception as e:
            log(f"Direct JSON parse failed (attempt {attempt+1}): {e}", "ERROR")

        # ------------------------
        # 2. Fallback extraction
        # ------------------------
        try:
            start = cleaned.find('[')
            end = cleaned.rfind(']')

            if start != -1 and end != -1 and end > start:
                json_str = cleaned[start:end + 1]
                json_str = json_str.replace("\r", "").strip()

                json_str = re.sub(r",\s*}", "}", json_str)
                json_str = re.sub(r",\s*]", "]", json_str)

                data = json.loads(json_str)
                log("Fallback JSON parsed successfully", "INFO")
                return normalize_output(data)

        except Exception as e:
            log(f"Fallback parsing failed: {e}", "ERROR")

        # ------------------------
        # 3. Retry via AI
        # ------------------------
        log("Re-prompting AI for valid JSON...", "WARN")

        retry_prompt = f"""
            Your previous response was invalid or incomplete JSON.
            
            You MUST return ONLY a valid JSON array of strings.
            
            Rules:
            - No markdown
            - No explanations
            - No extra text
            - No truncation
            - Output must start with [ and end with ]
            
            Fix and return ONLY valid JSON.
            
            Previous response:
            {cleaned}
            """

        res = call_hf(retry_prompt)

        try:
            cleaned = res["choices"][0]["message"]["content"]
        except Exception:
            cleaned = str(res)

        cleaned = re.sub(r"```json|```", "", cleaned).strip()

        finish_reason = res.get("choices", [{}])[0].get("finish_reason")
        if finish_reason == "length":
            log("⚠️ AI response truncated", "WARN")

    log("All parsing attempts failed", "ERROR")
    return []

# ============================================================
# NORMALIZER
# ============================================================

def normalize_output(data):
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
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
