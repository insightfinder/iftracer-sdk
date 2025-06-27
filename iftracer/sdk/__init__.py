import os
import sys
from pathlib import Path

from typing import Optional, Set
from colorama import Fore
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace.export import SpanExporter
from opentelemetry.sdk.metrics.export import MetricExporter
from opentelemetry.sdk.resources import SERVICE_NAME
from opentelemetry.propagators.textmap import TextMapPropagator
from opentelemetry.util.re import parse_env_headers

from iftracer.sdk.metrics.metrics import MetricsWrapper
from iftracer.sdk.telemetry import Telemetry
from iftracer.sdk.instruments import Instruments
from iftracer.sdk.config import (
    is_content_tracing_enabled,
    is_tracing_enabled,
    is_metrics_enabled,
)
from iftracer.sdk.fetcher import Fetcher
from iftracer.sdk.tracing.tracing import (
    TracerWrapper,
    set_association_properties,
    set_external_prompt_tracing_context,
)
from iftracer.sdk.evaluation import Evaluator
from iftracer.sdk.evaluation.models import EvaluationConfig
from typing import Dict


class Iftracer:
    AUTO_CREATED_KEY_PATH = str(
        Path.home() / ".cache" / "iftracer" / "auto_created_key"
    )
    AUTO_CREATED_URL = str(Path.home() / ".cache" / "iftracer" / "auto_created_url")

    __tracer_wrapper: TracerWrapper
    __fetcher: Fetcher = None
    __evaluator: Optional[Evaluator] = None

    @staticmethod
    def init(
        app_name: Optional[str] = sys.argv[0],
        iftracer_user: str = "",
        iftracer_license_key: str = "",
        iftracer_project: str = "",
        api_endpoint: str = "",
        headers: Dict[str, str] = {},
        disable_batch=False,
        exporter: SpanExporter = None,
        metrics_exporter: MetricExporter = None,
        metrics_headers: Dict[str, str] = None,
        processor: SpanProcessor = None,
        propagator: TextMapPropagator = None,
        should_enrich_metrics: bool = True,
        resource_attributes: dict = {},
        instruments: Optional[Set[Instruments]] = None,
        # Evaluation-specific parameters
        evaluation_project_name: str = "",
        evaluation_api_endpoint: str = "",
        evaluation_api_key: str = "",
        evaluation_username: str = "",
    ) -> None:
        Telemetry()

        api_endpoint = os.getenv("IFTRACER_BASE_URL") or api_endpoint
        if api_endpoint is None:
            return
        api_key = None # Disable the usage of api_key

        if not is_tracing_enabled():
            print(Fore.YELLOW + "Tracing is disabled" + Fore.RESET)
            return

        enable_content_tracing = is_content_tracing_enabled()

        if exporter or processor:
            print(Fore.GREEN + "Iftracer exporting traces to a custom exporter")

        headers = os.getenv("IFTRACER_HEADERS") or headers

        if isinstance(headers, str):
            headers = parse_env_headers(headers)
        
        if not exporter and not processor and headers:
            print(
                Fore.GREEN
                + f"Iftracer exporting traces to {api_endpoint}, authenticating with custom headers"
            )

        if api_key and not exporter and not processor and not headers:
            print(
                Fore.GREEN
                + f"Iftracer exporting traces to {api_endpoint} authenticating with bearer token"
            )
            headers = {
                "Authorization": f"Bearer {api_key}",
            }

        print(Fore.RESET)

        # Tracer init
        resource_attributes.update({SERVICE_NAME: app_name})
        if iftracer_user:
            # Arguments passed in Iftracer.init() will have higher priority than other environment variables values.
            headers['iftracer_user'] = iftracer_user or os.getenv("IFTRACER_USER") or "" 
        if iftracer_license_key:
            headers['iftracer_license_key'] = iftracer_license_key or os.getenv("IFTRACER_LICENSE_KEY")  or ""
        if iftracer_project:
            headers['iftracer_project'] = iftracer_project or os.getenv("IFTRACER_PROJECT_NAME")  or ""
        TracerWrapper.set_static_params(
            resource_attributes, enable_content_tracing, api_endpoint, headers
        )
        Iftracer.__tracer_wrapper = TracerWrapper(
            disable_batch=disable_batch,
            processor=processor,
            propagator=propagator,
            exporter=exporter,
            should_enrich_metrics=should_enrich_metrics,
            instruments=instruments,
        )

        # Initialize evaluation configuration if parameters are provided
        if evaluation_api_endpoint or evaluation_api_key or evaluation_username or evaluation_project_name:
            eval_config = EvaluationConfig(
                project_name=evaluation_project_name or iftracer_project,
                api_endpoint=evaluation_api_endpoint or api_endpoint,
                api_key=evaluation_api_key or iftracer_license_key,
                username=evaluation_username or iftracer_user,
            )
            Iftracer.__evaluator = Evaluator(eval_config)

        if not metrics_exporter and exporter:
            return

        metrics_endpoint = os.getenv("IFTRACER_METRICS_ENDPOINT") or api_endpoint
        metrics_headers = (
            os.getenv("IFTRACER_METRICS_HEADERS") or metrics_headers or headers
        )

        if not is_metrics_enabled() or not metrics_exporter and exporter:
            print(Fore.YELLOW + "Metrics are disabled" + Fore.RESET)
            return

        MetricsWrapper.set_static_params(
            resource_attributes, metrics_endpoint, metrics_headers
        )

        Iftracer.__metrics_wrapper = MetricsWrapper(exporter=metrics_exporter)

    def set_association_properties(properties: dict) -> None:
        set_association_properties(properties)

    def set_prompt(template: str, variables: dict, version: int):
        set_external_prompt_tracing_context(template, variables, version)

    def report_score(
        association_property_name: str,
        association_property_id: str,
        score: float,
    ):
        if not Iftracer.__fetcher:
            print(
                Fore.RED
                + "Error: Cannot report score. Missing Iftracer API key,"
                + " go to https://app.traceloop.com/settings/api-keys to create one"
            )
            print("Set the IFTRACER_API_KEY environment variable to the key")
            print(Fore.RESET)
            return

        Iftracer.__fetcher.post(
            "score",
            {
                "entity_name": f"iftracer.association.properties.{association_property_name}",
                "entity_id": association_property_id,
                "score": score,
            },
        )

    @staticmethod
    def _get_trace_eval_timestamps():
        '''
        trace_time is utc_timestamp
        eval_time is local_timestamp
        '''
        from datetime import datetime, timezone
        local_time = datetime.now()
        utc_timestamp = int(local_time.timestamp() * 1000)
        # Get the offset from UTC in seconds
        offset_seconds = local_time.astimezone().utcoffset()
        if offset_seconds:
            offset = int(offset_seconds.total_seconds() * 1000)
        else:
            offset = 0
        local_timestamp = utc_timestamp + offset
        return utc_timestamp, local_timestamp

    @staticmethod
    def get_evaluator(config: Optional[EvaluationConfig] = None) -> Evaluator:
        """Get or create evaluator instance."""
        if not Iftracer.__evaluator:
            Iftracer.__evaluator = Evaluator(config)
        return Iftracer.__evaluator

    @staticmethod
    def evaluate_safety(prompt: str, trace_id: Optional[str] = None, 
                       timestamp: Optional[int] = None):
        """Evaluate prompt for safety issues."""
        import uuid
        
        evaluator = Iftracer.get_evaluator()
        
        # Use defaults if not provided
        if trace_id is None:
            trace_id = str(uuid.uuid4())
        if timestamp is None:
            _, timestamp = Iftracer._get_trace_eval_timestamps()
        
        request = evaluator.create_evaluation_request(
            prompt=prompt,
            trace_id=trace_id,
            timestamp=timestamp,
            project_name=None  # Will use evaluator's configured project name
        )
        return evaluator.evaluate_safety(request)

    @staticmethod
    def evaluate_hallucination_bias(prompt: str, response: str, trace_id: Optional[str] = None,
                                   timestamp: Optional[int] = None):
        """Evaluate prompt and response for hallucination and bias."""
        import uuid
        
        evaluator = Iftracer.get_evaluator()
        
        # Use defaults if not provided
        if trace_id is None:
            trace_id = str(uuid.uuid4())
        if timestamp is None:
            _, timestamp = Iftracer._get_trace_eval_timestamps()
        
        request = evaluator.create_evaluation_request(
            prompt=prompt,
            response=response,
            trace_id=trace_id,
            timestamp=timestamp,
            project_name=None  # Will use evaluator's configured project name
        )
        return evaluator.evaluate_hallucination_bias(request)

    @staticmethod
    def evaluate_external_hallucination(prompt: str, response: str, explanation: str, score: int,
                                       trace_id: Optional[str] = None, timestamp: Optional[int] = None):
        """Evaluate external hallucination with explanation and score."""
        import uuid
        
        evaluator = Iftracer.get_evaluator()
        
        # Use defaults if not provided
        if trace_id is None:
            trace_id = str(uuid.uuid4())
        if timestamp is None:
            _, timestamp = Iftracer._get_trace_eval_timestamps()
        
        request = evaluator.create_evaluation_request(
            prompt=prompt,
            response=response,
            explanation=explanation,
            score=score,
            trace_id=trace_id,
            timestamp=timestamp,
            project_name=None  # Will use evaluator's configured project name
        )
        return evaluator.evaluate_external_hallucination(request)

    # Backward compatibility alias
    @staticmethod
    def evaluate_custom_hallucination(prompt: str, response: str, explanation: str, score: int,
                                     trace_id: Optional[str] = None, timestamp: Optional[int] = None):
        """Deprecated: Use evaluate_external_hallucination instead."""
        import warnings
        warnings.warn(
            "evaluate_custom_hallucination is deprecated. Use evaluate_external_hallucination instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return Iftracer.evaluate_external_hallucination(prompt, response, explanation, score, trace_id, timestamp)

    # Batch evaluation methods
    @staticmethod
    def batch_evaluate_safety(prompts: list, trace_ids: Optional[list] = None, 
                             timestamps: Optional[list] = None, project_name: Optional[str] = None):
        """Evaluate multiple prompts for safety issues."""
        from iftracer.sdk.evaluation import BatchEvaluator
        
        evaluator = Iftracer.get_evaluator()
        batch_evaluator = BatchEvaluator(evaluator.config)
        return batch_evaluator.evaluate_safety_batch(
            prompts=prompts,
            trace_ids=trace_ids,
            timestamps=timestamps,
            project_name=project_name
        )

    @staticmethod  
    def batch_evaluate_hallucination_bias(prompts: list, responses: list,
                                         trace_ids: Optional[list] = None,
                                         timestamps: Optional[list] = None,
                                         project_name: Optional[str] = None):
        """Evaluate multiple prompt/response pairs for hallucination and bias."""
        from iftracer.sdk.evaluation import BatchEvaluator
        
        evaluator = Iftracer.get_evaluator()
        batch_evaluator = BatchEvaluator(evaluator.config)
        return batch_evaluator.evaluate_hallucination_bias_batch(
            prompts=prompts,
            responses=responses,
            trace_ids=trace_ids,
            timestamps=timestamps,
            project_name=project_name
        )

    @staticmethod
    def batch_evaluate_external_hallucination(prompts: list, responses: list,
                                           explanations: list, scores: list,
                                           trace_ids: Optional[list] = None,
                                           timestamps: Optional[list] = None,
                                           project_name: Optional[str] = None):
        """Evaluate multiple external hallucination requests."""
        from iftracer.sdk.evaluation import BatchEvaluator
        
        evaluator = Iftracer.get_evaluator()
        batch_evaluator = BatchEvaluator(evaluator.config)
        return batch_evaluator.evaluate_external_hallucination_batch(
            prompts=prompts,
            responses=responses,
            explanations=explanations,
            scores=scores,
            trace_ids=trace_ids,
            timestamps=timestamps,
            project_name=project_name
        )

    @staticmethod
    def batch_evaluate_mixed(evaluation_configs: list, project_name: Optional[str] = None):
        """Evaluate a mixed batch with different evaluation types."""
        from iftracer.sdk.evaluation import BatchEvaluator
        
        evaluator = Iftracer.get_evaluator()
        batch_evaluator = BatchEvaluator(evaluator.config)
        return batch_evaluator.evaluate_mixed_batch(evaluation_configs)
