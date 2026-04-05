from app.tools.input_validator import get_non_empty_input
from app.utils import prompt_text
import os

def config():
    print(prompt_text.get_banner())
    print("\n\n")
    print("Please select which you want to config?")
    print("1. Git")
    print("2. server")
    res = get_non_empty_input("Enter Number:")
    if res == 1:
        git_username = get_non_empty_input("Enter git username: ")
        update_env('GIT_USERNAME', git_username)

        git_token = get_non_empty_input("Enter access token: ")
        update_env('GIT_ACCESS_TOKEN', git_token)

    elif res == 2:
        server_name = get_non_empty_input("Enter server name: ")
        server_host = get_non_empty_input("Enter server host: ")
        server_port = get_non_empty_input("Enter server port: ")
        server_username = get_non_empty_input("Enter server username: ")
        server_password = get_non_empty_input("Enter server password: ")

        update_env(f'SERVER_NAME_{server_name}', server_name)
        update_env(f'SERVER_HOST_{server_name}', server_host)
        update_env(f'SERVER_PORT_{server_name}', server_port)
        update_env(f'SERVER_USERNAME_{server_name}', server_username)
        update_env(f'SERVER_PASSWORD_{server_name}', server_password)



def get_env_path(file_name=".env"):
    # Gets current working directory (project root when script runs from root)
    return os.path.join(os.getcwd(), file_name)


def update_env(key, value, file_path=None):
    if file_path is None:
        file_path = get_env_path()

    lines = []
    key_found = False

    with open(file_path, "r") as f:
        for line in f:
            if line.startswith(f"{key}="):
                lines.append(f"{key}={value}\n")
                key_found = True
            else:
                lines.append(line)

    if not key_found:
        lines.append(f"{key}={value}\n")

    with open(file_path, "w") as f:
        f.writelines(lines)


# Usage (no path needed → defaults to root .env)
update_env("DB_NAME", "my_database")