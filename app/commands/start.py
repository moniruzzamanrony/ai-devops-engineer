import typer
from app.core.config import GIT_USERNAME, GIT_ACCESS_TOKEN, get_server_credential
from app.tools.temp_credential import save_json
from app.utils import prompt_text
from app.services.ai_service import ask_devops

def start():
    """Start the application"""
    print(prompt_text.get_banner())
    print("\n\n")
    user_interaction()
    print("[*] Starting application...")

def user_interaction():
    print("How can I assist you today?")
    print("1. Server setup and deployment")
    print("2. Issue diagnosis and troubleshooting")
    input_choice = input("Please enter the number corresponding to your choice: ")

    def is_empty(value):
        return value is None or str(value).strip() == ""

    if input_choice == "1":
        print("\n---Server setup and deployment---")

        repo_link = input("Enter your git repository link: ").strip()
        repo_link = 'https://github.com/moniruzzamanrony/rent-tech-api.git'
        if is_empty(repo_link):
            raise ValueError("Repository link is required")

        is_git_configured = input("Did you configure git (y/n): ").strip().lower()

        if is_git_configured == 'n':
            git_username = input("Enter git username: ").strip()
            git_access_token = input("Enter git password: ").strip()

            if is_empty(git_username) or is_empty(git_access_token):
                raise ValueError("Git credentials cannot be empty")
        else:
            git_username = GIT_USERNAME
            git_access_token = GIT_ACCESS_TOKEN

        is_server_configured = input("Did you configure server (y/n): ").strip().lower()

        if is_server_configured == 'n':
            server_host = input("Enter server host: ").strip()
            server_port = input("Enter server ssh port: ").strip()
            server_user = input("Enter server username: ").strip()
            server_password = input("Enter server password: ").strip()

            if any(is_empty(v) for v in [server_host, server_port, server_user, server_password]):
                raise ValueError("Server details cannot be empty")
        else:
            server_name = input("Enter server name (Check from .env): ").strip().upper()
            server_name = 'rent_tech'.upper()
            server_host = get_server_credential(f'SERVER_HOST_{server_name}')
            server_port = get_server_credential(f'SERVER_PORT_{server_name}')
            server_user = get_server_credential(f'SERVER_USERNAME_{server_name}')
            server_password = get_server_credential(f'SERVER_PASSWORD_{server_name}')
            # https: // github.com / moniruzzamanrony / rent - tech - api.git
            if any(is_empty(v) for v in [server_host, server_port, server_user, server_password]):
                raise ValueError("Server credentials not found in .env")

        domain = input("Enter domain (Already DNS configured for the server): ").strip()
        domain = 'mapmark.live'
        if is_empty(domain):
            raise ValueError("Domain is required")

        data = {
            "repo_link": repo_link,
            "git_username": git_username,
            "git_access_token": git_access_token,
            "server_host": server_host,
            "server_port": int(server_port) if str(server_port).isdigit() else server_port,
            "server_user": server_user,
            "server_password": server_password,
            "domain": domain
        }

        save_json(data)

        prompt = prompt_text.generate_deployment_prompt()
        print(prompt)

        response = ask_devops(prompt)
        print(response)

        if response is True:
            user_interaction()

    # Add your server setup and deployment logic here
    elif input_choice == "2":
        print("[->2] Tell me about the issues you're facing.")
        # Add your issue diagnosis and troubleshooting logic here
    else:
        print("Invalid choice. Please enter 1 or 2.")