# iftracer-sdk

Iftracer’s Python SDK allows you to easily start monitoring and debugging your LLM execution. Tracing is done in a non-intrusive way, built on top of OpenTelemetry. The repo contains standard OpenTelemetry instrumentations for LLM providers and Vector DBs, as well as a Iftracer SDK that makes it easy to get started with OpenLLMetry, while still outputting standard OpenTelemetry data that can be connected to your observability stack. If you already have OpenTelemetry instrumented, you can just add any of our instrumentations directly. This package is built upon the [Traceloop SDK](https://github.com/traceloop/openllmetry/tree/main/packages/traceloop-sdk/traceloop/sdk) and shares the same environment variables so traceloop users can use this package directly without setting up them.

## Installation Guide

```
Option 1: Add GitHub link to your project directly. Example with pyproject.toml: 
Add the github link `iftracer-sdk = {git = "https://github.com/insightfinder/iftracer-sdk"}` directly to your package's `pyproject.toml` under `[tool.poetry.dependencies]`.

Option 2: Download the codes to local. Example with pyproject.toml: 
Add the local path `iftracer-sdk = { path = "/path-to-iftracer-sdk-pkg/iftracer-sdk", develop = true }` directly to your package's `pyproject.toml` under `[tool.poetry.dependencies]`.

Option 3: (In progress) `pip install iftracer-sdk`
```

## Quick Start Guide
Add the decorators like `@workflow`, `@aworkflow`, `@task`, and `@atask` over the methods to get the tracing details.

```python
from iftracer.sdk import Iftracer 
from iftracer.sdk.decorators import workflow
Iftracer.init(app_name="joke_generation_service")

@workflow(name="joke_creation")
def create_joke():
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Tell me a joke about opentelemetry"}],
    )
    return completion.choices[0].message.content
```

Response from langchain ainvoke() will normally need a handler to show more LLM model details like `prompt token`. We can use `trace_model_response()` to catch the details and avoid the handler. For example:
```python
@task(name="joke_invoke")
def create_joke():
    response = await joke_generator_langchain.ainvoke(
        {"question": prompt},
        config=config,
    )
    trace_model_response(response) # optional. Required if must show LLM model details.
    return response
```


## Unique features
1. New Tags: 
We have extracted additional data from LLM models to tags to assist tracing.
For example, we have extracted the LLM model's name, PG vector's embedding model name, and the dataset retrieved by RAG, and so on, to the workflow spans' tags. 
2. Customizable 
We can add more tags if you need them. We can adjust the tracers' behaviors based on your needs.


## FAQ:
1. Why I can't find the new tags?
1.1. This package won't extract the metadata like `prompt token` from response if the chain (e.g.: `joke_generator_langchain`) contains [StrOutputParser()](https://api.python.langchain.com/en/latest/output_parsers/langchain_core.output_parsers.string.StrOutputParser.html). Try to remove `StrOutputParser()` from the chain and stringify the result later. 
1.2. Contact our support team if the issue still persists.

2. What LLM models does this package support?
This `iftracer-sdk` package utilizes the opentelemetry packages from [ifllmetry](https://github.com/insightfinder/ifllmetry). It supports LLM models like Claude (anthropic), ChatGPT (openai), ollama, etc.
