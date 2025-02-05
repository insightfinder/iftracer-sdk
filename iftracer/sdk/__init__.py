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
from typing import Dict


class Iftracer:
    AUTO_CREATED_KEY_PATH = str(
        Path.home() / ".cache" / "iftracer" / "auto_created_key"
    )
    AUTO_CREATED_URL = str(Path.home() / ".cache" / "iftracer" / "auto_created_url")

    __tracer_wrapper: TracerWrapper
    __fetcher: Fetcher = None

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
