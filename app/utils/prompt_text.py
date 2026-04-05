def get_banner():
    banner = """
██████╗ ███████╗██╗   ██╗ ██████╗ ██████╗ ██████╗ ███████╗     █████╗ ██╗
██╔══██╗██╔════╝██║   ██║██╔═══██╗██╔══██╗██╔══██╗██╔════╝    ██╔══██╗██║
██║  ██║█████╗  ██║   ██║██║   ██║██████╔╝██████╔╝███████╗    ███████║██║
██║  ██║██╔══╝  ╚██╗ ██╔╝██║   ██║██╔═══╝ ██╔═══╝ ╚════██║    ██╔══██║██║
██████╔╝███████╗ ╚████╔╝ ╚██████╔╝██║     ██║     ███████║    ██║  ██║██║
╚═════╝ ╚══════╝  ╚═══╝   ╚═════╝ ╚═╝     ╚═╝     ╚══════╝    ╚═╝  ╚═╝╚═╝

                    🚀 D E V O P S   A I 🚀
                 Automation • Deployment • Intelligence
                 """
    return banner


def generate_deployment_prompt(repo_link,git_username,git_password, server_host, server_port, server_user, server_password, domain):
    prompt = f"""
        I want to deploy a project using Docker from a GitHub repository.

        Repository URL: {repo_link}
        Git Username: {git_username}
        Git Password: {git_password}
        Domain: {domain}

        SERVER ACCESS (only used if SERVER MODE is detected):
        • SERVER_HOST: {server_host}
        • SERVER_USER: {server_user}
        • SERVER_PORT: {server_port}
        • SERVER_PASSWORD: {server_password}

        IMPORTANT:
        • Detect that deployment should run on REMOTE SERVER
        • Prefer SERVER execution flow only

        Execution Modes:

        A) SERVER MODE:
        • All commands must be executed via SSH using provided credentials
        • Use format:
        ssh user@host “command”
        • Assume Ubuntu Linux server
        • Install Docker if not installed
        • Clone the GitHub repository if git username,password provided then use creadential for cloning
        • Build Docker image
        • Run Docker container
        • Install and configure Nginx as reverse proxy
        • Configure Nginx to forward renttech.com traffic to the Docker container
        • Open required firewall ports (80, 443)
        • Configure Let's Encrypt SSL (HTTPS) for the domain

        RESPONSE FORMAT:

        Return the result as a JSON object:
        [
            {{
                "cmd": "command to execute",
                "desc": "description of the command"
            }}

        ]

        STRICT RULES:
        • Output ONLY a valid JSON object
        • Do NOT include any text before or after the JSON
        • Do NOT include mode detection fields
        • Do NOT include code blocks
        • Do NOT include explanations
        • Do NOT include markdown
        • Commands must match SERVER execution only
        • Must include all deployment steps including SSL setup
    """
    return prompt

