# iftracer-sdk

Iftracer’s Python SDK allows you to easily start monitoring and debugging your LLM execution. Tracing is done in a non-intrusive way, built on top of OpenTelemetry. The repo contains standard OpenTelemetry instrumentations for LLM providers and Vector DBs, as well as a Iftracer SDK that makes it easy to get started with OpenLLMetry, while still outputting standard OpenTelemetry data that can be connected to your observability stack. If you already have OpenTelemetry instrumented, you can just add any of our instrumentations directly. 

## Installation Guide

```
Option 1: Add GitHub link to your project directly. Example with pyproject.toml: 
Add the github link `iftracer-sdk = {git = "https://github.com/insightfinder/iftracer-sdk"}` directly to your package's `pyproject.toml` under `[tool.poetry.dependencies]`.

Option 2: Download the codes to local. Example with pyproject.toml: 
Add the local path `iftracer-sdk = { path = "/path-to-iftracer-sdk-pkg/iftracer-sdk", develop = true }` directly to your package's `pyproject.toml` under `[tool.poetry.dependencies]`.

Option 3: (In progress) `pip install iftracer-sdk`
```
## Configuration Guide
Make sure to correctly configure .env file: `IFTRACER_BASE_URL=<OpenTelemetry Endpoint>`.

Alternatively, You can put the opentelemetry endpoint into python code like: `Iftracer.init(api_endpoint=<opentelemetry endpoint>)`

The tracing feature won't work without setting IFTRACER_BASE_URL correctly.

## Quick Start Guide
Add the decorators like `@workflow`, `@aworkflow`, `@task`, and `@atask` over the methods to get the tracing details. Add @workflow or @aworkflow over a function if you want to see more tags in tracing report.

#### You can copy & paste the following code example to test if the iftracer is working well. Feel free to replace openai by other LLM models like claude or ollama.

```python
from iftracer.sdk.decorators import workflow
import openai
from iftracer.sdk import Iftracer

@workflow(name="get_chat_completion_test")
def get_gpt4o_mini_completion(messages, model="gpt-4o-mini", temperature=0.7):
    """
    Note: Set your OpenAI API key before using this api

    Function to get a response from the GPT-4o-mini model using the updated OpenAI API.

    Args:
        messages (list): List of messages (system, user, assistant).
        model (str): The model to use, default is "gpt-4o-mini".
        temperature (float): Controls the randomness of the response.

    Returns:
        str: The model-generated response.
    """
    try:
        # Make a request to OpenAI's new Chat Completions API
        response = openai.chat.completions.create(
            model=model, messages=messages, temperature=temperature
        )

        # Return the content of the first choice from the response
        return response
    except openai.OpenAIError as e:
        # Catching OpenAI-specific errors
        print(f"OpenAI API error: {e}")
        return None


# Example Usage
if __name__ == "__main__":
    # Set your OpenAI API key here or export it as environment variable.
    openai.api_key = <Your OpenAI API Key>
    Iftracer.init(api_endpoint=<Your OpenTelemetry API Endpoint>)  # Make sure to include the license key provided by InsightFinder when creating an OpenTelemetry API Endpoint 
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": "Can you write a haiku about recursion in programming?",
        },
    ]

    response = get_gpt4o_mini_completion(messages)

    if response:
        print("GPT-4o-mini Response:", response)

```
```
Successful response example:
GPT-4o-mini Response: ChatCompletion(id='chatcmpl-...', choices=[Choice(finish_reason='stop', index=0, logprobs=None, message=ChatCompletionMessage(content='Functions call themselves,  \nLayers deep, a dance of code—  \nEndless paths unfold.', refusal=None, role='assistant', audio=None, function_call=None, tool_calls=None))], created=..., model='gpt-4o-mini-2024-07-18', object='chat.completion', service_tier=None, system_fingerprint='...', usage=CompletionUsage(completion_tokens=19, prompt_tokens=28, total_tokens=47, completion_tokens_details=CompletionTokensDetails(accepted_prediction_tokens=0, audio_tokens=0, reasoning_tokens=0, rejected_prediction_tokens=0), prompt_tokens_details=PromptTokensDetails(audio_tokens=0, cached_tokens=0)))
```


Response from langchain `ainvoke()/invoke()` will normally need a handler to show more LLM model details like `prompt token`. We can use `trace_model_response()` to catch the details and avoid the handler. For example:
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
