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
        2. Install required dependencies on the server (if not already installed):
           - Docker and add verify commend
           - Git and add verify commend
           - Nginx and add verify commend
           - Certbot (Let's Encrypt) and add verify commend
        3. Clone the repository using Git credentials
        4. Build the Docker image
        5. Run the Docker container
        6. Configure Nginx as a reverse proxy
        7. Configure domain routing to forward traffic to the container
        8. Setup SSL using Let's Encrypt (HTTPS)
        9. Enable firewall ports (80, 443). Must be remember thatDON'T remove 22 port 
        
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
        You are an AI DevOps assistant.
        
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
        Analyze the result and decide next action.
        
        Step 1:
        If "error" is empty/null AND "output" is meaningful → SUCCESS
        → Return:
        []
        
        Step 2:
        If "error" exists → FAILURE
        
        Classify the error:
        - Authentication / SSH / Connection issues
        - Other issues
        
        Step 3:
        ❗ IMPORTANT RULES:
        
        A) If it is Authentication / SSH / Connection related:
        Return ONLY ONE string inside array explaining the issue.
        
        Example:
        [
          "SSH authentication failed. Verify username, password, host, and SSH access."
        ]
        
        B) If it is ANY OTHER error:
        Return ONLY FIX COMMANDS.
        
        ========================
        STRICT REQUIREMENTS FOR FIX COMMANDS
        ========================
        - Output MUST be ONLY an array of commands
        - NO explanations
        - NO text
        - NO markdown
        - NO comments
        - NO descriptions
        
        Each item MUST be a complete executable command.
        
        Preferred commands (examples):
        [
          "apt-get update",
          "pip install package_name"
        ]
        
        If remote execution is needed:
        [
          "sshpass -p 'PASSWORD' ssh USER@HOST 'apt-get update'",
          "sshpass -p 'PASSWORD' ssh USER@HOST 'pip install package_name'"
        ]
        
        ========================
        OUTPUT FORMAT (STRICT JSON ONLY)
        ========================
        
        Case 1 (Success):
        []
        
        Case 2 (Auth issue):
        [
          "single explanation string"
        ]
        
        Case 3 (Other errors):
        [
          "command1",
          "command2"
        ]
        
        ========================
        CRITICAL RULES
        ========================
        - Return ONLY JSON array
        - No explanations at all in command mode
        - No sentences
        - No reasoning
        - No markdown/code blocks
        - No extra characters
        - No trailing commas
        - Use double quotes only
        - Output must be valid JSON
        
        ========================
        FINAL OUTPUT
        ========================
        Return ONLY the JSON array.
        """
    return prompt

def generate_error_fix_prompt(error_block):
    prompt = f"""
You are a DevOps automation agent.

Your task is to analyze failed command executions and return ONLY a valid JSON array of strings.

========================
INPUT
========================
{error_block}

Each item contains:
- run_cmd
- error

========================
RULES
========================

1. If ALL errors are empty or null:
Return:
[]

2. If ANY error is related to:
- authentication failure
- wrong host
- wrong password
- SSH connection issue
- permission denied (SSH)

Return ONLY:
["Fix SSH credentials or connection (check host, username, password, SSH access)"]

3. For ALL OTHER errors:
- Return ONLY fix commands
- Use this exact format:

sshpass -p '{get_value('server_password')}' ssh {get_value('server_user')}@{get_value('server_host')} 'command'

- Each command must:
  - Be single-line
  - Be independent
  - Directly fix the issue

========================
STRICT OUTPUT FORMAT
========================

- Output MUST be valid JSON
- Output MUST be a JSON array only
- Output MUST contain ONLY strings
- NO markdown (no ```json)
- NO explanations
- NO extra text
- NO comments
- NO objects
- NO trailing commas

Valid examples:

[]
["sshpass -p 'pass' ssh root@host 'apt install -y docker.io'"]
["Fix SSH credentials or connection (check host, username, password, SSH access)"]

========================
IMPORTANT
========================

- Response must start with [ and end with ]
- Do not include anything before or after JSON
- Ensure JSON is parseable by json.loads()

Now analyze and return the result.
"""
    return prompt