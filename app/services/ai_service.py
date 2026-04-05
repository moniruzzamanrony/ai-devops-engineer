from app.config.hugging_face_client import call_hf
from collections import deque
import json
import re
from app.tools.run_cmd import run_command
import datetime

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

    log(f"Raw AI response: {res}")

    # Detect truncation
    finish_reason = res.get("choices", [{}])[0].get("finish_reason")
    if finish_reason == "length":
        log("⚠️ Warning: AI response was truncated")

    try:
        content = res["choices"][0]["message"]["content"]
    except Exception:
        content = str(res)

    log(f"Extracted AI content:\n{content}")

    # -----------------------------
    # Step 2: Parse instructions
    # -----------------------------
    log("Parsing AI instructions...")
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
    log("Executing queued instructions...")

    while ai_instruction_queue:
        instruction = ai_instruction_queue.popleft()

        # Validate instruction structure
        if not isinstance(instruction, dict):
            log(f"Skipping invalid instruction (not dict): {instruction}")
            continue

        cmd = instruction.get("cmd")
        desc = instruction.get("desc", "No description")

        if not cmd:
            log(f"Skipping instruction with no cmd: {instruction}")
            continue

        log(f"Executing: {desc}")
        log(f"CMD: {cmd}")

        try:
            result = run_command(cmd)
            log(f"Command result: {result}")
        except Exception as e:
            log(f"Command execution failed: {e}")

    log("=== DEVOPS PIPELINE COMPLETED ===")

    return {
        "response": res,
        "instructions": instructions
    }


# ============================================================
# INSTRUCTION PARSER
# ============================================================

def parse_ai_instructions(content: str):

    if not content:
        log("No AI content received")
        return []

    log("Cleaning AI content...")

    cleaned = re.sub(r"```json|```", "", content).strip()

    log(f"Cleaned content:\n{cleaned}")

    # ✅ NEW: fix escape issues BEFORE parsing
    cleaned = fix_invalid_json_escapes(cleaned)

    log("After fixing invalid escapes:")
    log(cleaned)

    # Step 1: Try direct parsing
    try:
        data = json.loads(cleaned)
        log(f"Direct JSON parsed successfully: {data}")

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            for value in data.values():
                if isinstance(value, list):
                    return value
            return [data]

    except Exception as e:
        log(f"Direct JSON parse failed: {e}")
    """
    Robust JSON parser with logging and fallback handling
    """

    if not content:
        log("No AI content received")
        return []

    log("Cleaning AI content...")

    cleaned = re.sub(r"```json|```", "", content).strip()

    log(f"Cleaned content:\n{cleaned}")

    # -----------------------------
    # Step 1: Direct JSON parse
    # -----------------------------
    try:
        data = json.loads(cleaned)

        log("Direct JSON parsed successfully")

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            for value in data.values():
                if isinstance(value, list):
                    return value
            return [data]

    except Exception as e:
        log(f"Direct JSON parse failed: {e}")

    # -----------------------------
    # Step 2: Fallback extraction
    # -----------------------------
    try:
        log("Trying fallback JSON extraction...")

        start = cleaned.find('[')
        end = cleaned.rfind(']')

        if start == -1 or end == -1:
            log("No JSON array found in content")
            return []

        json_str = cleaned[start:end + 1]

        log(f"Extracted JSON string:\n{json_str}")

        # Normalize
        json_str = json_str.replace("\r", "").strip()

        # Fix trailing commas
        json_str = re.sub(r",\s*}", "}", json_str)
        json_str = re.sub(r",\s*]", "]", json_str)

        data = json.loads(json_str)

        log("Fallback JSON parsed successfully")

        return data

    except Exception as e:
        log(f"Fallback parsing failed: {e}")
        log(f"Raw content:\n{content}")

    return []


# ============================================================
# OPTIONAL ESCAPE FIXER
# ============================================================

def fix_invalid_json_escapes(text: str):
    if not text:
        return text

    # Fix invalid backslashes like \n, \namespace, etc.
    text = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)

    return text