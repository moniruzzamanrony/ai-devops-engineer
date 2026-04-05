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
        print("[*] Starting server setup and deployment...")
        # Add your server setup and deployment logic here
    elif input_choice == "2":
        print("[*] Starting issue diagnosis and troubleshooting...")
        # Add your issue diagnosis and troubleshooting logic here
    else:         
        print("Invalid choice. Please enter 1 or 2.")
    print("[*] Starting application...")