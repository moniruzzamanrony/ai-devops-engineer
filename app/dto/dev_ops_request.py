from pydantic import BaseModel

class DevOpsRequest(BaseModel):
    prompt: str
    serverHost: str
    serverUsername: str
    serverPass: str
    domain: str
    domainHost: str
    domainHostUsername: str
    domainHostPass: str