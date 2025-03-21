from opentelemetry.semconv.ai import SpanAttributes
from iftracer.sdk import Iftracer
from iftracer.sdk.decorators import task, workflow


def test_association_properties(exporter):
    @workflow(name="test_workflow")
    def test_workflow():
        return test_task()

    @task(name="test_task")
    def test_task():
        return

    Iftracer.set_association_properties({"user_id": 1, "user_name": "John Doe"})
    test_workflow()

    spans = exporter.get_finished_spans()
    assert [span.name for span in spans] == [
        "test_task.task",
        "test_workflow.workflow",
    ]

    some_task_span = spans[0]
    some_workflow_span = spans[1]
    assert (
        some_workflow_span.attributes[
            f"{SpanAttributes.IFTRACER_ASSOCIATION_PROPERTIES}.user_id"
        ]
        == 1
    )
    assert (
        some_workflow_span.attributes[
            f"{SpanAttributes.IFTRACER_ASSOCIATION_PROPERTIES}.user_name"
        ]
        == "John Doe"
    )
    assert (
        some_task_span.attributes[
            f"{SpanAttributes.IFTRACER_ASSOCIATION_PROPERTIES}.user_id"
        ]
        == 1
    )
    assert (
        some_task_span.attributes[
            f"{SpanAttributes.IFTRACER_ASSOCIATION_PROPERTIES}.user_name"
        ]
        == "John Doe"
    )


def test_association_properties_within_workflow(exporter):
    @workflow(name="test_workflow_within")
    def test_workflow():
        Iftracer.set_association_properties({"session_id": 15})
        return

    test_workflow()

    spans = exporter.get_finished_spans()
    assert [span.name for span in spans] == [
        "test_workflow_within.workflow",
    ]

    some_workflow_span = spans[0]
    assert (
        some_workflow_span.attributes[
            f"{SpanAttributes.IFTRACER_ASSOCIATION_PROPERTIES}.session_id"
        ]
        == 15
    )
