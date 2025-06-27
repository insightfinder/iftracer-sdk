"""Data models for evaluation requests and responses."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


class EvaluationType(Enum):
    """Types of evaluations supported by the platform."""
    SAFETY = "safety"
    HALLUCINATION_BIAS = "hallubias" 
    EXTERNAL_HALLUCINATION = "exterhallu"


@dataclass
class EvaluationRequest:
    """Single evaluation request."""
    prompt: str
    trace_id: str
    timestamp: int
    response: Optional[str] = None
    explanation: Optional[str] = None
    score: Optional[int] = None
    project_name: Optional[str] = None
    
    def __post_init__(self):
        if not self.trace_id:
            self.trace_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = int(datetime.now().timestamp() * 1000)


@dataclass
class BatchEvaluationRequest:
    """Batch evaluation request for multiple prompts/responses."""
    requests: List[EvaluationRequest]
    project_name: Optional[str] = None
    
    def __post_init__(self):
        # Ensure all requests have the same project_name if specified
        if self.project_name:
            for req in self.requests:
                if not req.project_name:
                    req.project_name = self.project_name


@dataclass 
class EvaluationResponse:
    """Response from evaluation API."""
    success: bool
    data: Any
    error_message: Optional[str] = None
    status_code: Optional[int] = None
    
    @classmethod
    def success_response(cls, data: Any) -> 'EvaluationResponse':
        return cls(success=True, data=data)
    
    @classmethod
    def error_response(cls, error_message: str, status_code: Optional[int] = None) -> 'EvaluationResponse':
        return cls(success=False, data=None, error_message=error_message, status_code=status_code)


@dataclass
class EvaluationConfig:
    """Configuration for evaluation endpoints and settings."""
    project_name: str = ""
    api_endpoint: str = "https://ai-stg.insightfinder.com"
    api_key: Optional[str] = None
    username: Optional[str] = None
    timeout: int = 30
    retry_attempts: int = 3
    
    @property
    def safety_endpoint(self) -> str:
        return f"{self.api_endpoint}/api/external/v1/evaluation/safety"
    
    @property 
    def hallubias_endpoint(self) -> str:
        return f"{self.api_endpoint}/api/external/v1/evaluation/bias-hallu"
    
    @property
    def exterhallu_endpoint(self) -> str:
        return f"{self.api_endpoint}/api/external/v1/evaluation/exter-hallu"
