from config.hugging_face_client import call_hf
from collections import deque
from dto.dev_ops_request import DevOpsRequest
import json
import re
from services.action_type_enum import ActionTypes

ai_instraction_queue = deque()


def ask_devops(request: DevOpsRequest):

    # Step 1: Get main AI response
    res = call_hf(request.prompt)
    print("AI Response:", res)

    try:
        content = res["choices"][0]["message"]["content"]
    except Exception:
        content = str(res)

    # Step 2: Extract action type
    action_prompt = f"""
        Extract the action type from the following user request.

        User Request:
        {request.prompt}

        Allowed action types:
        {[a.value for a in ActionTypes]}

        Return ONLY a JSON array of action types.
        Example:
        ["cmd"]
        """

    action_res = call_hf(action_prompt)

    try:
        action_content = action_res["choices"][0]["message"]["content"]
        action_types = json.loads(action_content)
    except Exception:
        action_types = []


    # Step 3: Parse instructions
    instructions = parse_ai_instructions(content)
    print(instructions)

    for instruction in instructions:
        ai_instraction_queue.append(instruction)

    if action_types[0] == ActionTypes.CMD.value:
        process_cmd_instructions(ai_instraction_queue)

    # Step 4: Process commands
    while ai_instraction_queue:
        item = ai_instraction_queue.popleft()
        print(item.get("cmd"))

    return {
        "response": res,
        "action_types": action_types,
        "instructions": instructions
    }

def process_cmd_instructions(ai_instraction_queue):
    for instruction in ai_instraction_queue:
        if instruction.get("type") == ActionTypes.CMD.value:
            cmd = instruction.get("cmd")
            print(f"Executing command: {cmd}")
            # Here you would add the logic to execute the command on the server

def parse_ai_instructions(content: str):
    try:
        return json.loads(content)

    except Exception:
        try:
            match = re.search(r"\[.*\]", content, re.DOTALL)
            if match:
                json_str = match.group(0)

                # Clean escape issues
                json_str = json_str.replace("\\n", "\n")
                json_str = json_str.replace("\\t", "\t")

                return json.loads(json_str)

        except Exception as e:
            print("Parsing failed:", str(e))
            print("Raw content:", content)

    return []