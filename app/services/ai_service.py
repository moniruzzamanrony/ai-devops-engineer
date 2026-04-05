import shutil
import sys

from app.config.hugging_face_client import call_hf
from collections import deque
import json
import re
from app.tools.run_cmd import run_command
import datetime

from app.utils.prompt_text import generate_result_analysis_prompt
from click import prompt

ai_instruction_queue = deque()


def log(message: str):
    """Simple logger with timestamp"""
    print(f"[{datetime.datetime.now()}] {message}")


def ask_devops(prompt: str):
    """
    DevOps AI pipeline with full logging and safety
    """

    log("=== START DEVOPS PIPELINE ===")

    # -----------------------------
    # Step 1: Call AI
    # -----------------------------
    log("Sending prompt to AI...")
    res = call_hf(prompt)

    # Detect truncation
    finish_reason = res.get("choices", [{}])[0].get("finish_reason")
    if finish_reason == "length":
        log("⚠️ Warning: AI response was truncated")
    try:
        content = res["choices"][0]["message"]["content"]
    except Exception:
        content = str(res)

    # -----------------------------
    # Step 2: Parse instructions
    # -----------------------------
    instructions = parse_ai_instructions(content)

    log(f"Parsed instructions count: {len(instructions)}")

    # -----------------------------
    # Step 3: Queue instructions
    # -----------------------------
    for instruction in instructions:
        ai_instruction_queue.append(instruction)


    # -----------------------------
    # Step 4: Execute instructions
    # -----------------------------
    while ai_instruction_queue:
        cmd = ai_instruction_queue.popleft()
        try:
            log(f": {cmd}")
            if is_valid_command(cmd):
                result = execute_cmd(cmd,ai_instruction_queue)
                log(f"Command success: {result}\n\n")
            else:
                log("Invalid suggestion from model")
                sys.exit(1)
        except Exception as e:
            log(f"Command execution failed: {e}")

    log("=== DEVOPS PIPELINE COMPLETED ===")
    return True


def execute_cmd(cmd : str,ai_instruction_queue):
    ai_sub_instruction_queue = deque()
    res = run_command(cmd)
    log(f"Command execute response: {res}")
    prompt = generate_result_analysis_prompt(res,ai_instruction_queue)
    aiRes = call_hf(prompt)
    print(aiRes)
    try:
        content = aiRes["choices"][0]["message"]["content"]
    except Exception:
        content = str(aiRes)
    instructions = parse_ai_instructions(content)

    for instruction in instructions:
        ai_sub_instruction_queue.append(instruction)

    while ai_sub_instruction_queue:
        sub_instruction = ai_sub_instruction_queue.popleft()
        print(f'Is valid cmd: {is_valid_command(sub_instruction)}')
        if is_valid_command(sub_instruction):
            log(f"Run For Fixing:  : {sub_instruction}")
            execute_cmd(sub_instruction,ai_sub_instruction_queue)
        else:
            sys.exit(1)
# ============================================================
# INSTRUCTION PARSER
# ============================================================

def parse_ai_instructions(content: str):
    """
    Robust JSON parser with fallback extraction and escape fixing.
    Returns a list of commands.
    """

    if not content:
        log("No AI content received")
        return []

    # -----------------------------
    # Clean markdown/code fences
    # -----------------------------
    cleaned = re.sub(r"```json|```", "", content).strip()

    # -----------------------------
    # Fix invalid JSON escapes
    # -----------------------------
    cleaned = fix_invalid_json_escapes(cleaned)

    # -----------------------------
    # Step 1: Direct JSON parse
    # -----------------------------
    try:
        data = json.loads(cleaned)
        log("Direct JSON parsed successfully")

        return normalize_output(data)

    except Exception as e:
        log(f"Direct JSON parse failed: {e}")
        log(f"Cleaned content: {cleaned}")

    # -----------------------------
    # Step 2: Extract JSON array fallback
    # -----------------------------
    try:
        start = cleaned.find('[')
        end = cleaned.rfind(']')

        if start == -1 or end == -1 or end <= start:
            log("No valid JSON array found")
            return []

        json_str = cleaned[start:end + 1]

        # Normalize whitespace
        json_str = json_str.replace("\r", "").strip()

        # Fix trailing commas
        json_str = re.sub(r",\s*}", "}", json_str)
        json_str = re.sub(r",\s*]", "]", json_str)

        # Parse again
        data = json.loads(json_str)

        log("Fallback JSON parsed successfully")

        return normalize_output(data)

    except Exception as e:
        log(f"Fallback parsing failed: {e}")

    return []


# ============================================================
# NORMALIZER
# ============================================================

def normalize_output(data):
    """
    Ensures the output is always a list
    """

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
    """
    Fix invalid backslashes that break JSON parsing
    """

    if not text:
        return text

    # Escape invalid backslashes (but keep valid JSON escapes intact)
    text = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)

    return text


def is_valid_command(cmd: str) -> bool:
    print(cmd)
    parts = cmd.strip().split()
    if not parts:
        return False

    command_name = parts[0]
    return shutil.which(command_name) is not None