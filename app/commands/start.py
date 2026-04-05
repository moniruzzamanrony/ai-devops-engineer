import typer
from app.utils import prompt_text
from app.services.ai_service import ask_devops

def start():
    """Start the application"""
    print(prompt_text.get_banner())
    print("\n\n")
    print("How can I assist you today?")
    print("1. Server setup and deployment")
    print("2. Issue diagnosis and troubleshooting")
    input_choice = input("Please enter the number corresponding to your choice: ")
    if input_choice == "1":
        print("\n---Server setup and deployment---")
        repo_link = input("Enter your git repository link: ")
        git_username = input("Enter git username:")
        git_password = input("Enter git password:")
        server_host = input("Enter server host: ")
        server_port = input("Enter server ssh port: ")
        server_user = input("Enter server username: ")
        server_password = input("Enter server password: ")
        domain = input("Enter dimain(Alreday dns configured for the server): ")

        prompt = prompt_text.generate_deployment_prompt(repo_link, git_username, git_password, server_host, server_port, server_user, server_password, domain)
        print(prompt)
        response = ask_devops(prompt)
        print("\n--- DevOps Response ---")
        print(response)
        # Add your server setup and deployment logic here
    elif input_choice == "2":
        print("[->2] Tell me about the issues you're facing.")
        # Add your issue diagnosis and troubleshooting logic here
    else:         
        print("Invalid choice. Please enter 1 or 2.")
    print("[*] Starting application...")