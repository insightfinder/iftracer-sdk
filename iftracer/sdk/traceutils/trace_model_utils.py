from ..decorators import task
from typing import Dict, Any
from .consts import TRACE_MODEL_RESPONSE

'''
This function is only to help trace the response returned from LLM models.

Input: Response from LLM models like gpt-4o-mini or llama3.1:8b or hugging-face.
Output: None

Limitation: The function won't accept streaming response or response without the Dict structure
'''
@task(TRACE_MODEL_RESPONSE)
def trace_model_response(model: Dict[str, Any]) -> None:
    return

@task(TRACE_MODEL_RESPONSE)
def trace_model_response_str(model: str) -> None:
    return



