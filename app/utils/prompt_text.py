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
1. Install dependencies on the server (if not already installed):
   - Docker (with verification)
   - Git (with verification)
   - Nginx (with verification)
   - Certbot (with verification)
2. Clone the repository (only if not already cloned)
3. Build Docker image (only if not already built)
4. Run Docker container (only if not already running)
5. Configure Nginx (only if not already configured)
6. Configure domain routing
7. Setup SSL using Let's Encrypt (only if not already exists)
8. Enable firewall ports (8080, 443) and ensure port 22 is NOT removed

========================
IDEMPOTENT RULE (VERY IMPORTANT)
========================

- BEFORE running ANY command, you MUST check:
  - If the step is already completed → SKIP execution
  - If not completed → execute the command

- Use safe patterns like:
  - command || install_command
  - condition && skip || run
  - check using:
    - command -v
    - systemctl status
    - docker ps / docker images
    - test -d / test -f

- Examples:
  - command -v docker || apt install -y docker.io
  - [ -d repo ] || git clone ...
  - docker ps | grep container || docker run ...
  - systemctl is-active nginx || systemctl start nginx

========================
COMMAND FORMAT RULES
========================

- Each command MUST use this SSH format:
  sshpass -p '{get_value('server_password')}' ssh {get_value('server_user')}@{get_value('server_host')} 'command'

- All commands must be:
  - Single-line
  - Self-contained
  - Independently executable

- Use Git credentials in clone:
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
- Ensure valid JSON
- Ensure proper escaping
- Ensure no broken quotes
- Each command must be idempotent and safe to re-run

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

- Return ONLY STRING array
- No text before or after JSON
- No partial output
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