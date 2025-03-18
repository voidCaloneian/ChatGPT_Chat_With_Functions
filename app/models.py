from pydantic import BaseModel
from typing import Dict, Any


class FunctionCall(BaseModel):
    name: str
    arguments: Dict[str, Any]
