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


def _coerce_item(item, idx: int) -> dict:
    """Coerce a model-returned item into the DeploymentStep shape.

    Different models stray from the schema in different ways. Normalise rather
    than fail so we can survive minor format drift:
      - bare string  -> {"label": f"step_{idx}", "cmd": [str]}
      - dict with cmd as string -> wrap cmd in a list
      - dict missing label -> synthesise one from the index
    """
    if isinstance(item, str):
        return {"label": f"step_{idx}", "cmd": [item]}
    if isinstance(item, dict):
        item = dict(item)
        if isinstance(item.get("cmd"), str):
            item["cmd"] = [item["cmd"]]
        if not item.get("label"):
            item["label"] = f"step_{idx}"
        return item
    raise ValueError(f"Step #{idx} is neither a string nor an object: {type(item).__name__}")


def parse_steps(data) -> List[DeploymentStep]:
    """Validate a parsed JSON value against the DeploymentStep schema.

    Raises ValueError when `data` is not a list. Raises pydantic.ValidationError
    when any item fails the schema after coercion.
    """
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array of steps, got {type(data).__name__}")
    if not data:
        raise ValueError("Expected a non-empty JSON array of steps")
    return [DeploymentStep(**_coerce_item(item, idx)) for idx, item in enumerate(data, start=1)]


__all__ = ["DeploymentStep", "parse_steps", "ValidationError"]
