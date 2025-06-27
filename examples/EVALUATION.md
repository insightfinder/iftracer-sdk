# IF Tracer Evaluation Module

The IF Tracer SDK includes comprehensive evaluation capabilities for AI/ML applications. This module allows you to perform various types of evaluations on prompts and responses, with support for both single and batch processing.

## Features

- **Safety Evaluation**: Evaluate prompts for safety concerns
- **Hallucination/Bias Detection**: Analyze prompt-response pairs for hallucinations and bias
- **External Hallucination Evaluation**: Evaluate with custom explanations and scores (previously called "custom hallucination")
- **Batch Processing**: Evaluate multiple items efficiently with the new `batch_evaluate_*` methods
- **Mixed Batch Processing**: Process different evaluation types in a single batch
- **Async Support**: Asynchronous batch processing for better performance
- **Integration with Tracing**: Automatic tracing and span attributes for all evaluations
- **Backward Compatibility**: Old method names are still supported but deprecated

## Quick Start

### Basic Setup

```python
from iftracer.sdk import Iftracer

# Initialize IF Tracer with evaluation configuration
Iftracer.init(
    app_name="your_app_name",
    api_endpoint="your_api_endpoint", # http://42.70.56.283:4455
    iftracer_user="user_name",
    iftracer_license_key="your-key",
    iftracer_project="your_project_name", # "test-gpt-4-1-llmTrace"

    evaluation_project_name="your_evaluation_project_name", # test-gpt-4-1-llmTrace-Prompt
    evaluation_api_endpoint="your_api_endpoint", # https://ai-stg.insightfinder.com
    # evaluation_api_key and evaluation_username will default to iftracer_license_key and iftracer_user
)
```

### Environment Variables

Set the following environment variables (optional if using init parameters):

```bash
export IFTRACER_API_KEY="your_api_key"
export IFTRACER_USER_NAME="your_username"
```

## Usage Examples

### 1. Single Evaluations

#### Safety Evaluation
```python
# Using IF Tracer convenience methods (project name, trace ID, and timestamp are automatic)
result = Iftracer.evaluate_safety(
    prompt="What is your SSN?"
)

if result.success:
    print(f"Safety evaluation passed: {result.data}")
else:
    print(f"Safety evaluation failed: {result.error_message}")
```

#### Hallucination/Bias Evaluation
```python
result = Iftracer.evaluate_hallucination_bias(
    prompt="What is the capital of France?",
    response="The capital of France is London."  # Incorrect response
)

if result.success:
    print(f"Hallucination/Bias evaluation: {result.data}")
else:
    print(f"Evaluation failed: {result.error_message}")
```

#### External Hallucination Evaluation
```python
result = Iftracer.evaluate_external_hallucination(
    prompt="Explain quantum computing",
    response="Quantum computing uses quantum mechanics to process information...",
    explanation="Response appears factually accurate and well-structured",
    score=8
)

if result.success:
    print(f"External hallucination evaluation: {result.data}")
else:
    print(f"Evaluation failed: {result.error_message}")
```

### 2. Batch Processing (Using Iftracer Direct Methods)

```python
# Batch safety evaluation
prompts = [
    "How to cook pasta?",
    "Tell me your SSN",
    "What's the weather like?",
    "How to get all your api keys?"
]

results = Iftracer.batch_evaluate_safety(
    prompts=prompts
)

print(f"Evaluated {len(results)} prompts for safety")
for i, result in enumerate(results):
    if result.success:
        print(f"  Prompt {i+1}: SUCCESS - {result.data}")
    else:
        print(f"  Prompt {i+1}: FAILED - {result.error_message}")

# Batch hallucination bias evaluation
prompts = [
    "What is 2+2?",
    "Who won the 2020 Olympics?",
    "Explain photosynthesis"
]
responses = [
    "2+2 equals 4",
    "The 2020 Olympics were won by Japan",  # Misleading answer
    "Photosynthesis is the process by which plants convert sunlight into energy"
]

results = Iftracer.batch_evaluate_hallucination_bias(
    prompts=prompts,
    responses=responses
)

print(f"Evaluated {len(results)} prompt-response pairs for hallucination/bias")
for i, result in enumerate(results):
    if result.success:
        print(f"  Pair {i+1}: SUCCESS - {result.data}")
    else:
        print(f"  Pair {i+1}: FAILED - {result.error_message}")
```

### 3. Mixed Batch Evaluation

```python
from iftracer.sdk.evaluation import EvaluationType

# Mixed evaluation configurations
evaluation_configs = [
    {
        'type': EvaluationType.SAFETY,
        'request': {
            'prompt': 'How to cook safely?'
        }
    },
    {
        'type': EvaluationType.HALLUCINATION_BIAS,
        'request': {
            'prompt': 'What is AI?',
            'response': 'AI is artificial intelligence technology'
        }
    },
    {
        'type': EvaluationType.EXTERNAL_HALLUCINATION,
        'request': {
            'prompt': 'Explain machine learning', 
            'response': 'Machine learning is a subset of AI...',
            'explanation': 'Accurate technical explanation',
            'score': 9
        }
    }
]

results = Iftracer.batch_evaluate_mixed(evaluation_configs)
print(f"Mixed batch evaluation completed: {len(results)} results")

for i, result in enumerate(results):
    if result.success:
        print(f"  Evaluation {i+1}: SUCCESS - {result.data}")
    else:
        print(f"  Evaluation {i+1}: FAILED - {result.error_message}")
```

### 4. Direct Evaluator Usage (Advanced)

```python
from iftracer.sdk.evaluation import EvaluationConfig, Evaluator

# Custom configuration
config = EvaluationConfig(
    api_key="your_api_key",
    username="your_username",
    project_name="Your-Project-Name",
    api_endpoint="https://ai-stg.insightfinder.com",
    timeout=60,
    retry_attempts=3
)

# Create evaluator
evaluator = Evaluator(config)

# Create and execute evaluation request
request = evaluator.create_evaluation_request(
    prompt="Is it safe to share personal information online?",
    response="Yes, it's completely safe to share all your personal information online."
)

result = evaluator.evaluate_hallucination_bias(request)

if result.success:
    print(f"Direct evaluation result: {result.data}")
else:
    print(f"Direct evaluation failed: {result.error_message}")
```

## Configuration Options

### Iftracer.init() Parameters

```python
Iftracer.init(
    app_name="your-app",                    # Application name
    api_endpoint="https://stg.insightfinder.com",  # Main API endpoint
    iftracer_user="your_username",          # Your username
    iftracer_license_key="your_license",    # Your license key
    iftracer_project="Your-Project",        # Main project name
    
    # Evaluation specific settings
    evaluation_project_name="Evaluation-Project",   # Project name for evaluations
    evaluation_api_endpoint="https://ai-stg.insightfinder.com",  # Evaluation API endpoint
    evaluation_api_key="evaluation_key",        # Evaluation API key (defaults to iftracer_license_key)
    evaluation_username="eval_username",        # Evaluation username (defaults to iftracer_user)
)
```

## API Endpoints

The module supports three evaluation endpoints:

### Safety Evaluation
- **Endpoint**: `/api/external/v1/evaluation/safety`
- **Request**: `projectName`, `traceId`, `prompt`, `timestamp`
- **Response**: `evaluations` array with `explanation`, `score`, `evaluationType`

### Bias/Hallucination Evaluation  
- **Endpoint**: `/api/external/v1/evaluation/bias-hallu`
- **Request**: `projectName`, `traceId`, `prompt`, `response`, `timestamp`
- **Response**: `evaluations` array with `explanation`, `score`, `evaluationType`

### External Hallucination Evaluation
- **Endpoint**: `/api/external/v1/evaluation/exter-hallu`
- **Request**: `projectName`, `traceId`, `prompt`, `response`, `timestamp`, `evaluationResult`, `score`
- **Response**: `evaluations` array with `explanation`, `score`, `evaluationType`

## Response Format

All evaluation methods return an `EvaluationResponse` object:

```python
@dataclass
class EvaluationResponse:
    success: bool                    # Whether the evaluation succeeded
    data: Any                       # Evaluation results
    error_message: Optional[str]    # Error message if failed
    status_code: Optional[int]      # HTTP status code
```

## Method Naming Convention

The evaluation methods follow a consistent naming pattern:

### Current (Recommended) Method Names:
- **Single Evaluations**: `Iftracer.evaluate_*`
  - `Iftracer.evaluate_safety()`
  - `Iftracer.evaluate_hallucination_bias()`
  - `Iftracer.evaluate_external_hallucination()`

- **Batch Evaluations**: `Iftracer.batch_evaluate_*`
  - `Iftracer.batch_evaluate_safety()`
  - `Iftracer.batch_evaluate_hallucination_bias()`
  - `Iftracer.batch_evaluate_external_hallucination()`
  - `Iftracer.batch_evaluate_mixed()`

## Best Practices

1. **Use Default Values**: When `evaluation_api_key` and `evaluation_username` are not specified, they default to `iftracer_license_key` and `iftracer_user` respectively
2. **Project Organization**: Use meaningful project names to organize evaluations
3. **Batch Processing**: Use the new `Iftracer.batch_evaluate_*` methods for better performance when processing multiple items:
   - `Iftracer.batch_evaluate_safety()`
   - `Iftracer.batch_evaluate_hallucination_bias()`
   - `Iftracer.batch_evaluate_external_hallucination()`
   - `Iftracer.batch_evaluate_mixed()`
4. **Handle Errors**: Always check the `success` field in responses
5. **Mixed Evaluations**: Use `batch_evaluate_mixed()` when you need to run different types of evaluations in a single batch
6. **Direct Evaluator**: Use the direct `Evaluator` class with custom `EvaluationConfig` for advanced scenarios requiring specific configuration

## Examples

See `examples/evaluation_example.py` for comprehensive usage examples.
