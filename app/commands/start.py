import typer
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
        # repo_link = input("Enter your git repository link: ")
        # git_username = input("Enter git username:")
        # git_password = input("Enter git password:")
        # server_host = input("Enter server host: ")
        # server_port = input("Enter server ssh port: ")
        # server_user = input("Enter server username: ")
        # server_password = input("Enter server password: ")
        # domain = input("Enter dimain(Alreday dns configured for the server): ")

        repo_link = 'https://github.com/moniruzzamanrony/rent-tech-api.git',
        git_username = 'moniruzzamanrony',
        git_access_token = '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',
        server_host = '213.199.36.174',
        server_port = 22,
        server_user = 'root',
        server_password = 'YOUR_SERVER_PASSWORD',
        domain = 'rentmark.live'
        data = {
            "repo_link": "https://github.com/moniruzzamanrony/rent-tech-api.git",
            "git_username": "moniruzzamanrony",
            "git_access_token": "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",
            "server_host": "213.199.36.174",
            "server_port": 22,
            "server_user": "root",
            "server_password": "YOUR_SERVER_PASSWORD",
            "domain": "rentmark.live"
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