import json
import os

FILE_PATH = "temp_credential.json"


def save_json(data: dict, file_path: str = FILE_PATH):
    """
    Save dictionary as JSON to a file.
    Creates the file if it does not exist.
    """

    # Ensure directory exists (if any)
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    # Write JSON
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

    return True


def get_value(key: str, file_path: str = FILE_PATH):
    """
    Get value by key from JSON file
    """
    if not os.path.exists(file_path):
        return None

    with open(file_path, "r") as f:
        data = json.load(f)

    return data.get(key)


def remove_json(file_path: str = FILE_PATH):
    """
    Remove the JSON file
    """
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False