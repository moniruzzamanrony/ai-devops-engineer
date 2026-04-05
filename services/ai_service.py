from config.hugging_face_client import call_hf
from collections import deque
from dto.dev_ops_request import DevOpsRequest
import json
import re
from services.action_type_enum import ActionTypes

ai_instruction_queue = deque()


def ask_devops(request: DevOpsRequest):
    """
    Main DevOps AI pipeline:
    1. Get AI response
    2. Extract action types
    3. Parse instructions
    4. Queue instructions
    """

    # -----------------------------
    # Step 1: Get AI response
    # -----------------------------
    res = call_hf(request.prompt)

    try:
        content = res["choices"][0]["message"]["content"]
    except Exception:
        content = str(res)

    # -----------------------------
    # Step 2: Extract action types
    # -----------------------------
    action_prompt = f"""
    You are an action classifier.

    Analyze the user request and decide whether it requires:
    - executing terminal commands (cmd)
    - or just a normal text response (text)

    Return STRICT JSON ONLY.

    Rules:
    - Return only a JSON array with a single value
    - No explanation
    - No extra text
    - No markdown

    Output format examples:
    ["cmd"]
    ["text"]

    Decision rules:
    - Return "cmd" if the request involves:
    - Docker setup
    - Server deployment
    - Running shell commands
    - Installing software
    - System configuration
    - DevOps / automation tasks

    - Return "text" if the request involves:
    - Questions
    - Explanations
    - Information lookup
    - General conversation
    - No system/terminal execution required

    User Request:
    {request.prompt}

    retunn the action type as a JSON array with a single value, either "cmd" or "text".
    """

    action_res = call_hf(action_prompt)

    try:
        action_content = action_res["choices"][0]["message"]["content"]
    except Exception:
        action_content = str(action_res)

    action_types = extract_action_types(action_content)

    print("Detected Action Types:", action_types)

    # -----------------------------
    # Step 3: Parse instructions
    # -----------------------------
    instructions = parse_ai_instructions(content)

    # -----------------------------
    # Step 4: Queue instructions
    # -----------------------------
    for instruction in instructions:
        ai_instruction_queue.append(instruction)

    # -----------------------------
    # Step 5: Example execution trigger
    # -----------------------------
    if action_types and ActionTypes.CMD.value in action_types:
        if ai_instruction_queue:
            print("Executing instruction:", ai_instruction_queue.popleft())

    return {
        "response": res,
        "action_types": action_types,
        "instructions": instructions
    }


# ============================================================
# ACTION TYPE EXTRACTION (ROBUST)
# ============================================================

def extract_action_types(ai_response: str):
    """
    Extract a single action type from AI response safely.

    Returns:
        str | None
    """

    print("Extracting action types from response:", ai_response)

    if not ai_response:
        return None

    try:
        # -----------------------------
        # Step 1: Clean markdown
        # -----------------------------
        cleaned = re.sub(r"```json|```", "", ai_response).strip()

        # -----------------------------
        # Step 2: Try direct JSON parse
        # -----------------------------
        try:
            data = json.loads(cleaned)

            # OpenAI-style response
            if isinstance(data, dict) and "choices" in data:
                content = data["choices"][0]["message"]["content"]
                return extract_action_types(content)

            if isinstance(data, list) and len(data) > 0:
                return str(data[0])

        except Exception:
            pass

        # -----------------------------
        # Step 3: Extract JSON array fallback
        # -----------------------------
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            json_str = match.group(0)

            json_str = json_str.replace("\r", "")
            json_str = fix_invalid_json_escapes(json_str)

            json_str = re.sub(r",\s*}", "}", json_str)
            json_str = re.sub(r",\s*]", "]", json_str)

            data = json.loads(json_str)

            if isinstance(data, list) and len(data) > 0:
                return str(data[0])

        # -----------------------------
        # Step 4: Extract quoted values
        # -----------------------------
        matches = re.findall(
            r"'(cmd|file|web_search|code_execution)'|\"(cmd|file|web_search|code_execution)\"",
            ai_response
        )

        extracted = []
        for m in matches:
            extracted.extend([x for x in m if x])

        if extracted:
            return extracted[0]

        # -----------------------------
        # Step 5: Keyword fallback
        # -----------------------------
        keywords = ["cmd", "file", "web_search", "code_execution"]
        lower_text = ai_response.lower()

        for kw in keywords:
            if kw in lower_text:
                return kw

    except Exception as e:
        print("Action extraction error:", str(e))
        print("Raw response:", ai_response)

    return None


# ============================================================
# INSTRUCTION PARSER
# ============================================================

def parse_ai_instructions(content: str):
    """
    Robust JSON parser for AI output with auto-repair for broken JSON.
    """

    if not content:
        return []

    # Step 1: Remove markdown
    cleaned = re.sub(r"```json|```", "", content).strip()

    # Step 2: Try direct parsing
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Step 3: Extract JSON array block
    try:
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if not match:
            return []

        json_str = match.group(0)

        # Step 4: Normalize whitespace
        json_str = json_str.replace("\r", "").strip()

        # Step 5: FIX broken newlines inside cmd strings
        # Convert raw newlines inside JSON strings into escaped \n
        json_str = re.sub(
            r'("cmd"\s*:\s*")([^"]*?)\n([^"]*?)(")',
            lambda m: m.group(1) + m.group(2) + "\\n" + m.group(3) + m.group(4),
            json_str,
            flags=re.DOTALL
        )

        # Step 6: Escape unescaped $ (common in nginx configs)
        json_str = json_str.replace("$", "\\$")

        # Step 7: Fix trailing commas
        json_str = re.sub(r",\s*}", "}", json_str)
        json_str = re.sub(r",\s*]", "]", json_str)

        return json.loads(json_str)

    except Exception as e:
        print("Parsing failed:", str(e))
        print("Raw content:", content)

    return []


    """
    Robust JSON parser for AI instruction output
    Handles:
    - markdown code blocks
    - invalid escape sequences
    - malformed JSON
    """

    if not content:
        return []

    try:
        # Step 1: Clean markdown
        cleaned = re.sub(r"```json|```", "", content).strip()

        # Step 2: Fix escapes
        cleaned = fix_invalid_json_escapes(cleaned)

        # Step 3: Direct parse
        return json.loads(cleaned)

    except Exception:
        try:
            # Step 4: Extract JSON array fallback
            match = re.search(r"\[.*\]", content, re.DOTALL)
            if not match:
                return []

            json_str = match.group(0)

            json_str = json_str.replace("\r", "")
            json_str = fix_invalid_json_escapes(json_str)

            json_str = re.sub(r",\s*}", "}", json_str)
            json_str = re.sub(r",\s*]", "]", json_str)

            return json.loads(json_str)

        except Exception as e:
            print("Parsing failed:", str(e))
            print("Raw content:", content)

    return []


# ============================================================
# ESCAPE FIXER
# ============================================================

def fix_invalid_json_escapes(text: str):
    """
    Fix invalid escape sequences in LLM outputs.
    """

    # Prevent broken escape sequences
    text = text.replace("\\$", "\\\\$")
    text = text.replace("\\'", "'")

    # Fix stray backslashes not part of valid escapes
    text = re.sub(r'\\(?!["\\/bfnrt])', r"\\\\", text)

    return text     