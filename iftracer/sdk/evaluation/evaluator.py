"""Evaluator class for IF tracer integration."""

import os
import json
import time
import uuid
import asyncio
import concurrent.futures
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

import requests
from opentelemetry import trace

from iftracer.sdk.evaluation.models import (
    EvaluationRequest,
    BatchEvaluationRequest,
    EvaluationResponse,
    EvaluationType,
    EvaluationConfig,
)
from iftracer.sdk.decorators import workflow


class Evaluator:
    """Main evaluator class for performing evaluations and integrating with IF tracer."""
    
    def __init__(self, config: Optional[EvaluationConfig] = None):
        """Initialize evaluator with configuration."""
        self.config = config or EvaluationConfig()
        
        # Set up default credentials from environment
        if not self.config.api_key:
            self.config.api_key = os.getenv("IFTRACER_API_KEY", "")
        if not self.config.username:
            self.config.username = os.getenv("IFTRACER_USER_NAME", "")
            
        if not self.config.api_key or not self.config.username:
            raise ValueError(
                "API key or username is missing. Set IFTRACER_API_KEY and IFTRACER_USER_NAME "
                "environment variables or provide them in EvaluationConfig."
            )
            
        self.headers = {
            'X-Api-Key': self.config.api_key,
            'X-User-Name': self.config.username,
            'Content-Type': 'application/json'
        }
    
    def _get_trace_eval_timestamps(self) -> tuple[int, int]:
        """Get UTC timestamp for tracing and local timestamp for evaluation."""
        local_time = datetime.now()
        utc_timestamp = int(local_time.timestamp() * 1000)
        
        # Get the offset from UTC in seconds and convert to milliseconds
        utc_offset = local_time.astimezone().utcoffset()
        if utc_offset:
            offset_seconds = utc_offset.total_seconds()
            offset = int(offset_seconds * 1000)
            local_timestamp = utc_timestamp + offset
        else:
            local_timestamp = utc_timestamp
        
        return utc_timestamp, local_timestamp
    
    def _post_request(self, endpoint: str, data: Dict[str, Any]) -> EvaluationResponse:
        """Send POST request to evaluation endpoint with retry logic."""
        for attempt in range(self.config.retry_attempts):
            try:
                response = requests.post(
                    endpoint, 
                    headers=self.headers, 
                    json=data,
                    timeout=self.config.timeout
                )
                return self._process_response(response)
            
            except requests.exceptions.RequestException as e:
                if attempt == self.config.retry_attempts - 1:
                    return EvaluationResponse.error_response(
                        f"Request to {endpoint} failed after {self.config.retry_attempts} attempts: {e}"
                    )
                time.sleep(2 ** attempt)  # Exponential backoff
        
        # This should never be reached, but added for type safety
        return EvaluationResponse.error_response("Unknown error occurred during request")
    
    def _process_response(self, response: requests.Response) -> EvaluationResponse:
        """Process HTTP response and return EvaluationResponse."""
        try:
            if response.status_code == 200:
                response_data = response.json()
                # Extract evaluations if present, otherwise return full response
                data = response_data.get('evaluations', response_data)
                return EvaluationResponse.success_response(data)
            
            elif 400 <= response.status_code < 500:
                return EvaluationResponse.error_response(
                    f"Client error {response.status_code}: {response.text}",
                    response.status_code
                )
            elif 500 <= response.status_code < 600:
                return EvaluationResponse.error_response(
                    f"Server error {response.status_code}: {response.text}",
                    response.status_code
                )
            else:
                return EvaluationResponse.error_response(
                    f"Unexpected status code {response.status_code}: {response.text}",
                    response.status_code
                )
        finally:
            response.close()
    
    @workflow(name="SafetyEvaluation")
    def evaluate_safety(self, request: EvaluationRequest) -> EvaluationResponse:
        """Evaluate prompt for safety issues."""
        span = trace.get_current_span()
        span.set_attribute("evaluation.type", EvaluationType.SAFETY.value)
        span.set_attribute("evaluation.trace_id", request.trace_id)
        span.set_attribute("evaluation.timestamp", request.timestamp)
        
        data = {
            'projectName': request.project_name or self.config.project_name,
            'prompt': request.prompt,
            'traceId': request.trace_id,
            'timestamp': request.timestamp,
        }
        
        result = self._post_request(self.config.safety_endpoint, data)
        
        # Set span attributes based on result
        span.set_attribute("evaluation.success", result.success)
        if not result.success:
            span.set_attribute("evaluation.error", result.error_message or "Unknown error")
        
        return result
    
    @workflow(name="HallucinationBiasEvaluation")
    def evaluate_hallucination_bias(self, request: EvaluationRequest) -> EvaluationResponse:
        """Evaluate prompt and response for hallucination and bias."""
        if not request.response:
            return EvaluationResponse.error_response("Response is required for hallucination/bias evaluation")
        
        span = trace.get_current_span()
        span.set_attribute("evaluation.type", EvaluationType.HALLUCINATION_BIAS.value)
        span.set_attribute("evaluation.trace_id", request.trace_id)
        span.set_attribute("evaluation.timestamp", request.timestamp)
        
        data = {
            'projectName': request.project_name or self.config.project_name,
            'prompt': request.prompt,
            'response': request.response,
            'traceId': request.trace_id,
            'timestamp': request.timestamp,
        }
        
        result = self._post_request(self.config.hallubias_endpoint, data)
        
        span.set_attribute("evaluation.success", result.success)
        if not result.success:
            span.set_attribute("evaluation.error", result.error_message or "Unknown error")
            
        return result
    
    @workflow(name="ExternalHallucinationEvaluation")
    def evaluate_external_hallucination(self, request: EvaluationRequest) -> EvaluationResponse:
        """Evaluate external hallucination with explanation and score."""
        if not request.response:
            return EvaluationResponse.error_response("Response is required for external hallucination evaluation")
        if request.explanation is None or request.score is None:
            return EvaluationResponse.error_response("Explanation and score are required for external hallucination evaluation")
        
        span = trace.get_current_span()
        span.set_attribute("evaluation.type", EvaluationType.EXTERNAL_HALLUCINATION.value)
        span.set_attribute("evaluation.trace_id", request.trace_id)
        span.set_attribute("evaluation.timestamp", request.timestamp)
        span.set_attribute("evaluation.score", request.score)
        
        data = {
            'projectName': request.project_name or self.config.project_name,
            'prompt': request.prompt,
            'response': request.response,
            'traceId': request.trace_id,
            'timestamp': request.timestamp,
            'evaluationResult': request.explanation,
            'score': request.score,
        }
        
        result = self._post_request(self.config.exterhallu_endpoint, data)
        
        span.set_attribute("evaluation.success", result.success)
        if not result.success:
            span.set_attribute("evaluation.error", result.error_message or "Unknown error")
            
        return result
    
    def evaluate(self, evaluation_type: EvaluationType, request: EvaluationRequest) -> EvaluationResponse:
        """Evaluate based on type."""
        if evaluation_type == EvaluationType.SAFETY:
            return self.evaluate_safety(request)
        elif evaluation_type == EvaluationType.HALLUCINATION_BIAS:
            return self.evaluate_hallucination_bias(request)
        elif evaluation_type == EvaluationType.EXTERNAL_HALLUCINATION:
            return self.evaluate_external_hallucination(request)
        else:
            return EvaluationResponse.error_response(f"Unsupported evaluation type: {evaluation_type}")
    
    @workflow(name="BatchEvaluation")
    def evaluate_batch(self, evaluation_type: EvaluationType, batch_request: BatchEvaluationRequest) -> List[EvaluationResponse]:
        """Evaluate multiple requests in batch with parallel processing."""
        span = trace.get_current_span()
        span.set_attribute("evaluation.type", f"batch_{evaluation_type.value}")
        span.set_attribute("evaluation.batch_size", len(batch_request.requests))
        
        results = []
        successful_evaluations = 0
        
        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all evaluation tasks
            future_to_request = {
                executor.submit(self.evaluate, evaluation_type, req): req 
                for req in batch_request.requests
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_request):
                try:
                    result = future.result()
                    results.append(result)
                    if result.success:
                        successful_evaluations += 1
                except Exception as e:
                    results.append(EvaluationResponse.error_response(f"Evaluation failed: {str(e)}"))
        
        span.set_attribute("evaluation.successful_count", successful_evaluations)
        span.set_attribute("evaluation.failed_count", len(batch_request.requests) - successful_evaluations)
        
        return results
    
    async def evaluate_batch_async(self, evaluation_type: EvaluationType, batch_request: BatchEvaluationRequest) -> List[EvaluationResponse]:
        """Asynchronously evaluate multiple requests in batch."""
        span = trace.get_current_span()
        span.set_attribute("evaluation.type", f"async_batch_{evaluation_type.value}")
        span.set_attribute("evaluation.batch_size", len(batch_request.requests))
        
        async def evaluate_single(req: EvaluationRequest) -> EvaluationResponse:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.evaluate, evaluation_type, req)
        
        # Create tasks for all evaluations
        tasks = [evaluate_single(req) for req in batch_request.requests]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        processed_results = []
        successful_evaluations = 0
        
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(EvaluationResponse.error_response(f"Evaluation failed: {str(result)}"))
            elif isinstance(result, EvaluationResponse):
                processed_results.append(result)
                if result.success:
                    successful_evaluations += 1
            else:
                processed_results.append(EvaluationResponse.error_response("Unknown result type"))
        
        span.set_attribute("evaluation.successful_count", successful_evaluations)
        span.set_attribute("evaluation.failed_count", len(batch_request.requests) - successful_evaluations)
        
        return processed_results
    
    def create_evaluation_request(
        self,
        prompt: str,
        response: Optional[str] = None,
        trace_id: Optional[str] = None,
        timestamp: Optional[int] = None,
        explanation: Optional[str] = None,
        score: Optional[int] = None,
        project_name: Optional[str] = None,
        use_local_timestamp: bool = True
    ) -> EvaluationRequest:
        """Helper method to create evaluation request with proper timestamps."""
        if timestamp is None:
            if use_local_timestamp:
                _, timestamp = self._get_trace_eval_timestamps()
            else:
                timestamp = int(datetime.now().timestamp() * 1000)
        
        return EvaluationRequest(
            prompt=prompt,
            response=response,
            trace_id=trace_id or str(uuid.uuid4()),
            timestamp=timestamp,
            explanation=explanation,
            score=score,
            project_name=project_name or self.config.project_name
        )
