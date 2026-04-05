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
    if input_choice == "1":
        print("\n---Server setup and deployment---")
        repo_link = input("Enter your git repository link: ")
        is_git_configured = input("Did you configure git:(y/n)")
        if is_git_configured is 'n':
            git_username = input("Enter git username:")
            git_access_token = input("Enter git password:")
        else:
            git_username = str(GIT_USERNAME)
            git_access_token = str(GIT_ACCESS_TOKEN)

        is_server_configured = input("Did you configure server:(y/n)")
        if is_server_configured is 'n':
            server_host = input("Enter server host: ")
            server_port = input("Enter server ssh port: ")
            server_user = input("Enter server username: ")
            server_password = input("Enter server password: ")
        else:
            server_name = input("Enter server name: (Check from .env)")
            server_host = get_server_credential(server_name.capitalize(),"SERVER_NAME")
            server_port = get_server_credential(server_name.capitalize(),"SERVER_PORT")
            server_user = get_server_credential(server_name.capitalize(),"SERVER_USERNAME")
            server_password = get_server_credential(server_name.capitalize(),"SERVER_PASSWORD")

        domain = input("Enter domain (Already dns configured for the server): ")

        data = {
            "repo_link": repo_link,
            "git_username": git_username,
            "git_access_token": git_access_token,
            "server_host": server_host,
            "server_port": int(server_port) if isinstance(server_port, str) and server_port.isdigit() else server_port,
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