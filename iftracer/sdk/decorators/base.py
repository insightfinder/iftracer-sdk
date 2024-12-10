import json
from functools import wraps
import os
import types
from typing import Optional

from opentelemetry import trace
from opentelemetry import context as context_api
from opentelemetry.semconv.ai import SpanAttributes, TraceloopSpanKindValues

from iftracer.sdk.telemetry import Telemetry
from iftracer.sdk.tracing import get_tracer, set_workflow_name
from iftracer.sdk.tracing.tracing import (
    TracerWrapper,
    set_entity_name,
    get_chained_entity_name,
)
from iftracer.sdk.utils import camel_to_snake
from iftracer.sdk.utils.json_encoder import JSONEncoder
from iftracer.sdk.traceutils.set_trace_utils import _add_model_traces_to_spans, _add_result_traces_to_spans
from iftracer.sdk.traceutils.consts import TRACE_MODEL_RESPONSE
def entity_method(
    name: Optional[str] = None,
    version: Optional[int] = None,
    tlp_span_kind: Optional[TraceloopSpanKindValues] = TraceloopSpanKindValues.TASK,
):
    def decorate(fn):
        @wraps(fn)
        def wrap(*args, **kwargs):
            if not TracerWrapper.verify_initialized():
                return fn(*args, **kwargs)

            entity_name = name or fn.__name__
            if tlp_span_kind in [
                TraceloopSpanKindValues.WORKFLOW,
                TraceloopSpanKindValues.AGENT,
            ]:
                set_workflow_name(entity_name)
            span_name = f"{entity_name}.{tlp_span_kind.value}"

            with get_tracer() as tracer:
                span = tracer.start_span(span_name)
                ctx = trace.set_span_in_context(span)
                ctx_token = context_api.attach(ctx)

                if tlp_span_kind in [
                    TraceloopSpanKindValues.TASK,
                    TraceloopSpanKindValues.TOOL,
                ]:
                    chained_entity_name = get_chained_entity_name(entity_name)
                    set_entity_name(chained_entity_name)
                else:
                    chained_entity_name = entity_name

                span.set_attribute(
                    SpanAttributes.IFTRACER_SPAN_KIND, tlp_span_kind.value
                )
                span.set_attribute(
                    SpanAttributes.IFTRACER_ENTITY_NAME, chained_entity_name
                )
                if version:
                    span.set_attribute(SpanAttributes.IFTRACER_ENTITY_VERSION, version)

                try:
                    if _should_send_prompts():
                        span.set_attribute(
                            SpanAttributes.IFTRACER_ENTITY_INPUT,
                            json.dumps(
                                {"args": args, "kwargs": kwargs}, cls=JSONEncoder
                            ),
                        )
                        
                except TypeError as e:
                    Telemetry().log_exception(e)

                res = fn(*args, **kwargs)
                # if entity_name == STR_OUTPUT_PARSER:  # todo: Not working. STR_OUTPUT_PARSER is not using entity_method
                #     _add_str_model_traces_to_spans(span, res, args, kwargs)
                if entity_name == TRACE_MODEL_RESPONSE:
                    _add_model_traces_to_spans(span, res, args, kwargs)
                elif tlp_span_kind in [
                    TraceloopSpanKindValues.WORKFLOW
                ]:
                    _add_model_traces_to_spans(span, res, args, kwargs)
                    _add_result_traces_to_spans(span, res, args, kwargs)
                # span will be ended in the generator
                if isinstance(res, types.GeneratorType):
                    return _handle_generator(span, res)

                try:
                    if _should_send_prompts():
                        span.set_attribute(
                            SpanAttributes.IFTRACER_ENTITY_OUTPUT,
                            json.dumps(res, cls=JSONEncoder),
                        )
                except TypeError as e:
                    Telemetry().log_exception(e)

                span.end()
                context_api.detach(ctx_token)

                return res

        return wrap

    return decorate


def entity_class(
    name: Optional[str],
    version: Optional[int],
    method_name: str,
    tlp_span_kind: Optional[TraceloopSpanKindValues] = TraceloopSpanKindValues.TASK,
):
    def decorator(cls):
        task_name = name if name else camel_to_snake(cls.__name__)
        method = getattr(cls, method_name)
        setattr(
            cls,
            method_name,
            entity_method(name=task_name, version=version, tlp_span_kind=tlp_span_kind)(
                method
            ),
        )
        return cls

    return decorator


# Async Decorators


def aentity_method(
    name: Optional[str] = None,
    version: Optional[int] = None,
    tlp_span_kind: Optional[TraceloopSpanKindValues] = TraceloopSpanKindValues.TASK,
):
    def decorate(fn):
        @wraps(fn)
        async def wrap(*args, **kwargs):
            if not TracerWrapper.verify_initialized():
                return await fn(*args, **kwargs)

            entity_name = name or fn.__name__
            if tlp_span_kind in [
                TraceloopSpanKindValues.WORKFLOW,
                TraceloopSpanKindValues.AGENT,
            ]:
                set_workflow_name(entity_name)
            span_name = (f"{name}.{tlp_span_kind.value}" if name else f"{fn.__name__}.{tlp_span_kind.value}")


            with get_tracer() as tracer:
                span = tracer.start_span(span_name)
                ctx = trace.set_span_in_context(span)
                ctx_token = context_api.attach(ctx)

                if tlp_span_kind in [
                    TraceloopSpanKindValues.TASK,
                    TraceloopSpanKindValues.TOOL,
                ]:
                    chained_entity_name = get_chained_entity_name(entity_name)
                    set_entity_name(chained_entity_name)
                else:
                    chained_entity_name = entity_name

                span.set_attribute(
                    SpanAttributes.IFTRACER_SPAN_KIND, tlp_span_kind.value
                )
                span.set_attribute(
                    SpanAttributes.IFTRACER_ENTITY_NAME, chained_entity_name
                )
                if version:
                    span.set_attribute(SpanAttributes.IFTRACER_ENTITY_VERSION, version)

                try:
                    if _should_send_prompts():
                        span.set_attribute(
                            SpanAttributes.IFTRACER_ENTITY_INPUT,
                            json.dumps({"args": args, "kwargs": kwargs}),
                        )
                except TypeError as e:
                    Telemetry().log_exception(e)

                res = await fn(*args, **kwargs)
                # if entity_name == STR_OUTPUT_PARSER: # May need to change opentelemetry-instrument-langchain to process the STR_OUTPUT_PARSER contents
                #     _add_str_model_traces_to_spans(span, res, args, kwargs)
                if entity_name == TRACE_MODEL_RESPONSE:
                    _add_model_traces_to_spans(span, res, args, kwargs)
                elif tlp_span_kind in [
                    TraceloopSpanKindValues.WORKFLOW
                ]:
                    _add_model_traces_to_spans(span, res, args, kwargs)
                    _add_result_traces_to_spans(span, res, args, kwargs)
                # span will be ended in the generator
                if isinstance(res, types.AsyncGeneratorType):
                    return await _ahandle_generator(span, ctx_token, res)

                try:
                    if _should_send_prompts():
                        span.set_attribute(
                            SpanAttributes.IFTRACER_ENTITY_OUTPUT, json.dumps(res)
                        )
                except TypeError as e:
                    Telemetry().log_exception(e)

                span.end()
                context_api.detach(ctx_token)

                return res

        return wrap

    return decorate


def aentity_class(
    name: Optional[str],
    version: Optional[int],
    method_name: str,
    tlp_span_kind: Optional[TraceloopSpanKindValues] = TraceloopSpanKindValues.TASK,
):
    def decorator(cls):
        task_name = name if name else camel_to_snake(cls.__name__)
        method = getattr(cls, method_name)
        setattr(
            cls,
            method_name,
            aentity_method(
                name=task_name, version=version, tlp_span_kind=tlp_span_kind
            )(method),
        )
        return cls

    return decorator


def _handle_generator(span, res):
    # for some reason the SPAN_KEY is not being set in the context of the generator, so we re-set it
    context_api.attach(trace.set_span_in_context(span))
    yield from res

    span.end()

    # Note: we don't detach the context here as this fails in some situations
    # https://github.com/open-telemetry/opentelemetry-python/issues/2606
    # This is not a problem since the context will be detached automatically during garbage collection


async def _ahandle_generator(span, ctx_token, res):
    async for part in res:
        yield part

    span.end()
    context_api.detach(ctx_token)


def _should_send_prompts():
    return (
        os.getenv("IFTRACER_TRACE_CONTENT") or "true"
    ).lower() == "true" or context_api.get_value("override_enable_content_tracing")
