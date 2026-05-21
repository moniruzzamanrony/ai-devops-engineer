from typing import List, Optional

from pydantic import BaseModel, ValidationError


class DeploymentStep(BaseModel):
    """A single deployment step the AI plans for us.

    Expected JSON shape per item:
        {
          "label": "Install Docker",
          "cmd": ["sshpass -p '...' ssh ... 'sudo apt install -y docker.io'"],
          "verify_cmd": "sshpass -p '...' ssh ... 'docker --version'"
        }
    """

    label: str
    cmd: List[str]
    verify_cmd: Optional[str] = None


def parse_steps(data) -> List[DeploymentStep]:
    """Validate a parsed JSON value against the DeploymentStep schema.

    Raises ValueError when `data` is not a list. Raises pydantic.ValidationError
    when any item fails the schema.
    """
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array of steps, got {type(data).__name__}")
    if not data:
        raise ValueError("Expected a non-empty JSON array of steps")
    return [DeploymentStep(**item) for item in data]


__all__ = ["DeploymentStep", "parse_steps", "ValidationError"]
