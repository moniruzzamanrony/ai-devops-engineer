import typer
from app.core.config import GIT_USERNAME, GIT_ACCESS_TOKEN, get_server_credential
from app.tools.temp_credential import save_json
from app.utils import prompt_text
from app.services import ai_agent

def start():
    """Start the application"""
    print(prompt_text.get_banner())
    print("\n\n")
    user_interaction()
    print("[*] Starting application...")

def user_interaction():
    print("How can I assist you today?")
    print("1. Server setup")
    print("2. App deployment")
    print("3. Issue diagnosis and troubleshooting")
    input_choice = input("Please enter the number corresponding to your choice: ")

    def is_empty(value):
        return value is None or str(value).strip() == ""

    if input_choice == "1":
        print("\n---Server setup---")
        print("1. Package 1 (Docker, Nginx, Chatbot)")
        option = input("Enter your choice: ")

        if option == '1':
            ai_agent.do_it(prompt_text.generate_server_setup_prompt('1'))

        else:
            raise ValueError("Invalid option selected")

    if input_choice == "2":
        print("\n---Server setup and deployment---")

        app_type = input("Choice your app type (1. Dockerize app. 2. Node frontend): ").strip()
        repo_link = input("Enter your git repository link: ").strip()
        enter_domain = input("Enter your domain: ").strip()
        if app_type == "1":
            response = ai_agent.do_it(prompt_text.generate_dockerize_app_deploy_prompt(repo_link, enter_domain))
        elif app_type == "2":
            response = ai_agent.do_it(prompt_text.generate_static_app_deploy_prompt(enter_domain))
        else:
            raise ValueError("Invalid option selected")

    # Add your server setup and deployment logic here
    elif input_choice == "3":
        print("[->2] Tell me about the issues you're facing.")
        # Add your issue diagnosis and troubleshooting logic here
    else:
        print("Invalid choice. Please enter 1 or 2.")