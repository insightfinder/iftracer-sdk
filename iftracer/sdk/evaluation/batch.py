"""Batch evaluation utilities for IF tracer."""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from iftracer.sdk.evaluation.models import (
    EvaluationRequest,
    BatchEvaluationRequest,
    EvaluationResponse,
    EvaluationType,
    EvaluationConfig,
)
from iftracer.sdk.evaluation.evaluator import Evaluator
from iftracer.sdk.decorators import workflow


class BatchEvaluator:
    """Utility class for batch evaluation operations."""
    
    def __init__(self, config: Optional[EvaluationConfig] = None):
        self.evaluator = Evaluator(config)
    
    @workflow(name="BatchSafetyEvaluation")
    def evaluate_safety_batch(self, prompts: List[str], trace_ids: Optional[List[str]] = None,
                             timestamps: Optional[List[int]] = None, project_name: Optional[str] = None) -> List[EvaluationResponse]:
        """Evaluate multiple prompts for safety issues."""
        requests = self._create_batch_requests(
            prompts=prompts,
            responses=None,
            trace_ids=trace_ids,
            timestamps=timestamps,
            project_name=project_name
        )
        
        batch_request = BatchEvaluationRequest(requests=requests, project_name=project_name)
        return self.evaluator.evaluate_batch(EvaluationType.SAFETY, batch_request)
    
    @workflow(name="BatchHallucinationBiasEvaluation") 
    def evaluate_hallucination_bias_batch(self, prompts: List[str], responses: List[str],
                                         trace_ids: Optional[List[str]] = None,
                                         timestamps: Optional[List[int]] = None,
                                         project_name: Optional[str] = None) -> List[EvaluationResponse]:
        """Evaluate multiple prompt/response pairs for hallucination and bias."""
        if len(prompts) != len(responses):
            raise ValueError("Number of prompts and responses must match")
        
        requests = self._create_batch_requests(
            prompts=prompts,
            responses=responses,
            trace_ids=trace_ids,
            timestamps=timestamps,
            project_name=project_name
        )
        
        batch_request = BatchEvaluationRequest(requests=requests, project_name=project_name)
        return self.evaluator.evaluate_batch(EvaluationType.HALLUCINATION_BIAS, batch_request)
    
    @workflow(name="BatchExternalHallucinationEvaluation")
    def evaluate_external_hallucination_batch(self, prompts: List[str], responses: List[str],
                                             explanations: List[str], scores: List[int],
                                             trace_ids: Optional[List[str]] = None,
                                             timestamps: Optional[List[int]] = None,
                                             project_name: Optional[str] = None) -> List[EvaluationResponse]:
        """Evaluate multiple external hallucination requests."""
        if not all(len(prompts) == len(lst) for lst in [responses, explanations, scores]):
            raise ValueError("All input lists must have the same length")
        
        requests = []
        for i in range(len(prompts)):
            request = self.evaluator.create_evaluation_request(
                prompt=prompts[i],
                response=responses[i],
                explanation=explanations[i],
                score=scores[i],
                trace_id=trace_ids[i] if trace_ids else None,
                timestamp=timestamps[i] if timestamps else None,
                project_name=project_name
            )
            requests.append(request)
        
        batch_request = BatchEvaluationRequest(requests=requests, project_name=project_name)
        return self.evaluator.evaluate_batch(EvaluationType.EXTERNAL_HALLUCINATION, batch_request)
    
    async def evaluate_safety_batch_async(self, prompts: List[str], trace_ids: Optional[List[str]] = None,
                                        timestamps: Optional[List[int]] = None, 
                                        project_name: Optional[str] = None) -> List[EvaluationResponse]:
        """Asynchronously evaluate multiple prompts for safety issues."""
        requests = self._create_batch_requests(
            prompts=prompts,
            responses=None,
            trace_ids=trace_ids,
            timestamps=timestamps,
            project_name=project_name
        )
        
        batch_request = BatchEvaluationRequest(requests=requests, project_name=project_name)
        return await self.evaluator.evaluate_batch_async(EvaluationType.SAFETY, batch_request)
    
    async def evaluate_hallucination_bias_batch_async(self, prompts: List[str], responses: List[str],
                                                    trace_ids: Optional[List[str]] = None,
                                                    timestamps: Optional[List[int]] = None,
                                                    project_name: Optional[str] = None) -> List[EvaluationResponse]:
        """Asynchronously evaluate multiple prompt/response pairs for hallucination and bias."""
        if len(prompts) != len(responses):
            raise ValueError("Number of prompts and responses must match")
        
        requests = self._create_batch_requests(
            prompts=prompts,
            responses=responses,
            trace_ids=trace_ids,
            timestamps=timestamps,
            project_name=project_name
        )
        
        batch_request = BatchEvaluationRequest(requests=requests, project_name=project_name)
        return await self.evaluator.evaluate_batch_async(EvaluationType.HALLUCINATION_BIAS, batch_request)
    
    def _create_batch_requests(self, prompts: List[str], responses: Optional[List[str]] = None,
                              trace_ids: Optional[List[str]] = None, timestamps: Optional[List[int]] = None,
                              project_name: Optional[str] = None) -> List[EvaluationRequest]:
        """Helper method to create batch requests."""
        requests = []
        
        for i, prompt in enumerate(prompts):
            response = responses[i] if responses else None
            trace_id = trace_ids[i] if trace_ids else None
            timestamp = timestamps[i] if timestamps else None
            
            request = self.evaluator.create_evaluation_request(
                prompt=prompt,
                response=response,
                trace_id=trace_id,
                timestamp=timestamp,
                project_name=project_name
            )
            requests.append(request)
        
        return requests
    
    def evaluate_mixed_batch(self, evaluation_configs: List[Dict[str, Any]]) -> List[EvaluationResponse]:
        """Evaluate a mixed batch with different evaluation types."""
        results = []
        
        # Group requests by evaluation type for efficiency
        safety_requests = []
        hallubias_requests = []
        exterhallu_requests = []
        
        for config in evaluation_configs:
            eval_type = config.get('type')
            request_data = config.get('request', {})
            
            request = self.evaluator.create_evaluation_request(**request_data)
            
            if eval_type == EvaluationType.SAFETY:
                safety_requests.append(request)
            elif eval_type == EvaluationType.HALLUCINATION_BIAS:
                hallubias_requests.append(request)
            elif eval_type == EvaluationType.EXTERNAL_HALLUCINATION:
                exterhallu_requests.append(request)
        
        # Process each type in batch
        if safety_requests:
            batch_request = BatchEvaluationRequest(requests=safety_requests)
            results.extend(self.evaluator.evaluate_batch(EvaluationType.SAFETY, batch_request))
        
        if hallubias_requests:
            batch_request = BatchEvaluationRequest(requests=hallubias_requests)
            results.extend(self.evaluator.evaluate_batch(EvaluationType.HALLUCINATION_BIAS, batch_request))
        
        if exterhallu_requests:
            batch_request = BatchEvaluationRequest(requests=exterhallu_requests)
            results.extend(self.evaluator.evaluate_batch(EvaluationType.EXTERNAL_HALLUCINATION, batch_request))
        
        return results


# Convenience functions for easy access
def create_batch_evaluator(config: Optional[EvaluationConfig] = None) -> BatchEvaluator:
    """Create a new batch evaluator instance."""
    return BatchEvaluator(config)


def evaluate_prompts_safety(prompts: List[str], **kwargs) -> List[EvaluationResponse]:
    """Convenience function to evaluate multiple prompts for safety."""
    evaluator = BatchEvaluator()
    return evaluator.evaluate_safety_batch(prompts, **kwargs)


def evaluate_conversations_bias(prompts: List[str], responses: List[str], **kwargs) -> List[EvaluationResponse]:
    """Convenience function to evaluate multiple conversations for bias and hallucination."""
    evaluator = BatchEvaluator()
    return evaluator.evaluate_hallucination_bias_batch(prompts, responses, **kwargs)
