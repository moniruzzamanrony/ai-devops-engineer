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

def generate_deployment_prompt(
    repo_link='https://github.com/moniruzzamanrony/rent-tech-api.git',
    git_username='moniruzzamanrony',
    git_password='YOUR_GIT_PASSWORD',
    server_host='213.199.36.174',
    server_port=22,
    server_user='root',
    server_password='YOUR_SERVER_PASSWORD',
    domain='rentmark.live'
):
    prompt = f"""
        You are a DevOps automation agent.

        Your task is to generate a COMPLETE and VALID deployment plan as JSON.

        ========================
        PROJECT DETAILS
        ========================
        Repository URL: {repo_link}
        Git Username: {git_username}
        Git Password: {git_password}
        Domain: {domain}

        ========================
        SERVER DETAILS
        ========================
        Host: {server_host}
        Port: {server_port}
        User: {server_user}
        Password: {server_password}

        ========================
        REQUIREMENTS
        ========================

        You must generate a step-by-step deployment command list for:

        1. Connect to the remote server via SSH
        2. Install required dependencies:
        - 
        - Docker
        - Git
        - Nginx
        - Certbot (Let's Encrypt)
        3. Clone the repository
        4. Build Docker image
        5. Run Docker container
        6. Configure Nginx as reverse proxy
        7. Configure domain routing to the container
        8. Setup SSL (Let's Encrypt HTTPS)
        9. Enable firewall ports (80, 443)

        ========================
        CRITICAL RULES
        ========================

        - Output MUST be valid JSON array
        - DO NOT truncate output
        - DO NOT include explanations
        - DO NOT include markdown or code blocks
        - DO NOT include extra text
        - ALL commands must be self-contained in a single line
        - Avoid extremely long multi-line shell scripts
        - Each command must be executable independently
        - Use sshpass for password authentication
        - Use the following SSH format:
        sshpass -p '{server_password}' ssh {server_user}@{server_host} 'command'

        - Replace placeholders properly in commands
        - Ensure JSON strings are properly escaped
        - Ensure no unclosed quotes or broken commands

        ========================
        OUTPUT FORMAT
        ========================

        [
        {{
            "cmd": "sshpass -p 'PASSWORD' ssh USER@HOST 'command'",
            "desc": "Short description of what this command does"
        }}
        ]

        ========================
        IMPORTANT
        ========================

        - Return ONLY JSON
        - No text before or after
        - No partial JSON
        - No comments
        - No markdown
        - No explanations

        Now generate the deployment commands.
        """
    return prompt