from app.tools.temp_credential import get_value


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

def generate_deployment_prompt():
    prompt = f"""
        You are a DevOps automation agent.
        
        Your task is to generate a COMPLETE and VALID deployment plan as a STRING array of executable commands.
        
        ========================
        PROJECT DETAILS
        ========================
        Repository URL: {get_value('repo_link')}
        Git Username: {get_value('git_username')}
        Git Access Token: {get_value('git_access_token')}
        Domain: {get_value('domain')}
        
        ========================
        SERVER DETAILS
        ========================
        Host: {get_value('server_host')}
        Port: {get_value('server_port')}
        User: {get_value('server_user')}
        Password: {get_value('server_password')}
        
        ========================
        REQUIREMENTS
        ========================
        
        Generate a step-by-step deployment command sequence that includes:
        
        0. Install sshpass (if not already installed)
        1. Connect to the remote server using sshpass
        2. Install required dependencies on the server:
           - Docker
           - Git
           - Nginx
           - Certbot (Let's Encrypt)
        3. Clone the repository using Git credentials
        4. Build the Docker image
        5. Run the Docker container
        6. Configure Nginx as a reverse proxy
        7. Configure domain routing to forward traffic to the container
        8. Setup SSL using Let's Encrypt (HTTPS)
        9. Enable firewall ports (80, 443)
        
        ========================
        COMMAND FORMAT RULES
        ========================
        
        - Each command MUST use this SSH format:
          sshpass -p '{get_value('server_password')}' ssh {get_value('server_user')}@{get_value('server_host')} 'command'
        
        - All commands must be:
          - Self-contained
          - Executable independently
          - Single-line only
        
        - Use Git credentials in clone step:
          https://{get_value('git_username')}:{get_value('git_access_token')}@github.com/...
        
        ========================
        CRITICAL RULES
        ========================
        
        - Output MUST be a valid STRING array
        - DO NOT include explanations
        - DO NOT include markdown
        - DO NOT include extra text
        - DO NOT include comments
        - DO NOT truncate output
        - Ensure all strings are properly escaped
        - Ensure no broken quotes
        - Each command must be valid and runnable
        
        ========================
        OUTPUT FORMAT
        ========================
        
        [
          "sshpass -p 'PASSWORD' ssh USER@HOST 'command'",
          "sshpass -p 'PASSWORD' ssh USER@HOST 'command'"
        ]
        
        ========================
        IMPORTANT
        ========================
        
        - Return ONLY STRING
        - No text before or after
        - No partial STRING
        - No explanations
        
        Now generate the deployment commands.
        """
    return prompt


def generate_result_analysis_prompt(res, workflowDeque):
    prompt = f"""
        You are an AI DevOps assistant responsible for analyzing command execution results and deciding the next action in a deployment workflow.
        
        ========================
        INPUT
        ========================
        Command Execution Result:
        {res}
        
        Expected Workflow:
        {list(workflowDeque)}
        
        ========================
        TASK
        ========================
        
        1. Analyze the command execution result carefully.
        
        2. Determine if the execution is successful:
           - Has value in `error` filed of {res} .
           - Has value in `output` filed and `error` filed is empty of {res} .→ return an empty array: []
        
        3. If there is ANY error:
           - Identify the root cause from the error message.
        
           Common error categories:
           - Permission issues (e.g., "Permission denied")
           - Missing commands/files (e.g., "command not found", "No such file")
           - Service/network issues (e.g., "connection refused")
           - Authentication issues (e.g., "Permission denied (publickey/password)", "authentication failed", wrong host, wrong password)
        
        4. SPECIAL RULE (Authentication / Connection Issues):
           If the error indicates authentication failure, wrong host, wrong password, or SSH connection issues:
           - DO NOT return command execution fixes
           - Instead return a USER ACTION suggestion in this format:
        
        [
         "Clear explanation of what the user should fix (e.g., verify SSH credentials, check host IP, update password, ensure SSH access, etc.)"
        ]
        
        5. For all other errors:
       - Generate the MINIMUM necessary fix commands to resolve the issue.
       - Fix commands must:
         - Use the SSH format:
           sshpass -p '{get_value('server_password')}' ssh {get_value('server_user')}@{get_value('server_host')} 'command'
         - Be self-contained in a single line
         - Be executable independently
         - Directly address the root cause
         - Avoid unnecessary or redundant steps
    
            ========================
            OUTPUT RULES
            ========================
            
            - If no error:
              Return exactly:
              []
            
            - If authentication/connection error:
              Return USER_ACTION format only.
            
            - If other errors:
              Return ONLY a valid String array of fix commands:
                [
                 "sshpass -p 'PASSWORD' ssh USER@HOST 'command'",
                  "sshpass -p 'PASSWORD' ssh USER@HOST 'command'"
                ]
                
            ========================
            IMPORTANT
            ========================
            - Return ONLY String
            - No text before or after
            - No partial String
            - No explanations
            
            
            ========================
            CRITICAL RULES
            ========================
            - DO NOT push object in result array.
            - DO NOT include explanations
            - DO NOT include markdown
            - DO NOT include extra text
            - DO NOT include partial JSON
            - DO NOT include comments
            - DO NOT truncate output
            - Each command must be complete and independently runnable
            
            ========================
            NOW ANALYZE AND RESPOND
            ========================
"""
    return prompt