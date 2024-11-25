# iftracer-sdk

Iftracer’s Python SDK allows you to easily start monitoring and debugging your LLM execution. Tracing is done in a non-intrusive way, built on top of OpenTelemetry. You can choose to export the traces to Iftracer, or to your existing observability stack.

```python
Iftracer.init(app_name="joke_generation_service")

@workflow(name="joke_creation")
def create_joke():
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Tell me a joke about opentelemetry"}],
    )

    return completion.choices[0].message.content
```


## Use this package for an upgraded tracing experience

```
iftracer-sdk = {git = "https://<token>@github.com/insightfinder/iftracer-sdk"}
```

This package will use the opentelemetry packages from [ifllmetry](https://github.com/insightfinder/ifllmetry)


## easy to use:
1. Set up traceloop env or use the existing traceloop env.
  * make sure the iftracer-sdk is ours: iftracer-sdk = {git = "https://<token>@github.com/insightfinder/iftracer-sdk"}
2. `from iftracer.sdk.decorators import atask, task, aworkflow, workflow`: all of the decorators from traceloop can be used. Use workflow/aworkflow if you want to get more tags. 
3. `from iftracer.sdk.traceutils.trace_model_utils import trace_model_response`: Use `trace_model_response(response)` to trace the details of the LLM model that generates the response. This will also generate more tags. 
