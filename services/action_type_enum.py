from enum import Enum

class ActionTypes(str, Enum):
    CMD = "cmd"
    FILE = "file"
    WEB_SEARCH = "web_search"
    CODE_EXECUTION = "code_execution"