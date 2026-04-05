import typer
from app.utils import prompt_text

def start():
    """Start the application"""
    print(prompt_text.get_banner())
    print("\n\n")
    print("How can I assist you today?")
    print("1. Server setup and deployment")
    print("2. Issue diagnosis and troubleshooting")
    input_choice = input("Please enter the number corresponding to your choice: ")
    if input_choice == "1":
        print("[->1] Tell me about your server setup and deployment needs.\n")
        repo_link = input("Enter your git repository link: ")
        server_host = input("Enter server host: ")
        server_port = input("Enter server ssh port: ")
        server_user = input("Enter server username: ")
        server_password = input("Enter server password: ")

        prompt = prompt_text.generate_deployment_prompt(repo_link, server_host, server_port, server_user, server_password)
        # Add your server setup and deployment logic here
    elif input_choice == "2":
        print("[->2] Tell me about the issues you're facing.")
        # Add your issue diagnosis and troubleshooting logic here
    else:         
        print("Invalid choice. Please enter 1 or 2.")
    print("[*] Starting application...")