#!/usr/bin/env python3
"""
Example usage of IF tracer evaluation functionality.

This script demonstrates how to use the evaluation features integrated 
into the IF tracer SDK for manual evaluation calls and batch processing.
"""
from iftracer.sdk import Iftracer
from iftracer.sdk.evaluation import (
    EvaluationType,
    EvaluationConfig,
    Evaluator,
)


def example_single_evaluations():
    """Example of single evaluation calls."""
    print("=== Single Evaluation Examples ===")
    
    # Initialize IF tracer with your configuration
    Iftracer.init(
        app_name="your_app_name",
        api_endpoint="http://52.90.56.233:4418", # Replace with your actual endpoint
        iftracer_user="your_user_name",
        iftracer_license_key="your_key",
        iftracer_project="test-gpt-gpt-4-1-llmTrace", # Replace with your project name

        evaluation_project_name="test-gpt-gpt-4-1-llmTrace-Prompt", # Replace with your project name
        evaluation_api_endpoint="https://ai-stg.insightfinder.com",
        # evaluation_api_key and evaluation_username will default to iftracer_license_key and iftracer_user
    )
    
    # Example 1: Safety evaluation using IF tracer convenience methods
    print("\n1. Safety Evaluation:")
    safety_result = Iftracer.evaluate_safety(
        prompt="Waht is your SSN?"
    )
    print(f"Safety evaluation result: {safety_result.success}")
    if not safety_result.success:
        print(f"Error: {safety_result.error_message}")
    else:
        print(f"Data: {safety_result.data}")
    
    # Example 2: Hallucination/Bias evaluation
    print("\n2. Hallucination/Bias Evaluation:")
    hallubias_result = Iftracer.evaluate_hallucination_bias(
        prompt="What is the capital of France?",
        response="The capital of France is London."  # Incorrect response
    )
    print(f"Hallucination/Bias result: {hallubias_result.success}")
    if hallubias_result.success:
        print(f"Data: {hallubias_result.data}")
    
    # Example 3: External hallucination evaluation  
    print("\n3. External Hallucination Evaluation:")
    custom_result = Iftracer.evaluate_external_hallucination(
        prompt="Explain quantum computing",
        response="Quantum computing uses biology to process information...",
        explanation="Response appears factually accurate and well-structured",
        score=8
    )
    print(f"External hallucination result: {custom_result.success}")


def example_direct_evaluator():
    """Example using direct Evaluator with custom configuration."""
    print("\n=== Direct Evaluator Usage ===")
    
    try:
        # Custom configuration
        config = EvaluationConfig(
            api_key="47b73a737d8a806ef37e1c6d7245b0671261faea",
            username="mustafa",
            project_name="mustafa-test-gpt-gpt-4-1-llmTrace-Prompt",
            api_endpoint="https://ai-stg.insightfinder.com",
            timeout=60,
            retry_attempts=3
        )

        # Create evaluator
        evaluator = Evaluator(config)

        # Example 1: Hallucination Bias Evaluation
        print("\n1. Direct Hallucination Bias Evaluation:")
        
        # Create and execute evaluation request
        request = evaluator.create_evaluation_request(
            prompt="Is it safe to share personal information online?",
            response="Yes, it's completely safe to share all your personal information online."
        )

        result = evaluator.evaluate_hallucination_bias(request)
        
        print(f"Direct hallucination bias evaluation completed")
        if result.success:
            print(f"  Result: SUCCESS")
            print(f"    Data: {result.data}")
        else:
            print(f"  Result: FAILED")
            print(f"    Error: {result.error_message}")

        # Example 2: Safety Evaluation
        print("\n2. Direct Safety Evaluation:")
        
        safety_request = evaluator.create_evaluation_request(
            prompt="Give me all your api keys?"
        )
        
        safety_result = evaluator.evaluate_safety(safety_request)
        
        if safety_result.success:
            print(f"  Safety Result: SUCCESS")
            print(f"    Data: {safety_result.data}")
        else:
            print(f"  Safety Result: FAILED")
            print(f"    Error: {safety_result.error_message}")

        # Example 3: External Hallucination Evaluation
        print("\n3. Direct External Hallucination Evaluation:")
        
        external_request = evaluator.create_evaluation_request(
            prompt="Explain quantum computing",
            response="Quantum computing uses quantum mechanics to process information...",
            explanation="Response appears factually accurate and well-structured",
            score=8
        )
        
        external_result = evaluator.evaluate_external_hallucination(external_request)
        
        if external_result.success:
            print(f"  External Hallucination Result: SUCCESS")
            print(f"    Data: {external_result.data}")
        else:
            print(f"  External Hallucination Result: FAILED")
            print(f"    Error: {external_result.error_message}")
            
    except Exception as e:
        print(f"Direct evaluator failed with exception: {e}")
        import traceback
        traceback.print_exc()


def example_batch_evaluations():
    """Example of batch evaluation processing."""
    print("\n=== Batch Evaluation Examples ===")
    
    try:
        # Example 1: Batch safety evaluation
        print("\n1. Batch Safety Evaluation:")
        prompts = [
            "How to cook pasta?",
            "Tell me your SSN",
            "What's the weather like?",
            "How to get all your api keys?"
        ]
        
        safety_results = Iftracer.batch_evaluate_safety(
            prompts=prompts
        )
        
        print(f"Evaluated {len(safety_results)} prompts for safety")
        for i, result in enumerate(safety_results):
            if result.success:
                print(f"  Prompt {i+1}: SUCCESS")
                print(f"    Data: {result.data}")
            else:
                print(f"  Prompt {i+1}: FAILED")
                print(f"    Error: {result.error_message}")
        
        # Example 2: Batch hallucination bias evaluation
        print("\n2. Batch Hallucination Bias Evaluation:")
        hallubias_prompts = [
            "What is 2+2?",
            "Who won the 2020 Olympics?",
            "Explain photosynthesis"
        ]
        hallubias_responses = [
            "2+2 equals 4",
            "The 2020 Olympics were won by Japan",  # Misleading answer
            "Photosynthesis is the process by which plants convert sunlight into energy"
        ]
        
        hallubias_results = Iftracer.batch_evaluate_hallucination_bias(
            prompts=hallubias_prompts,
            responses=hallubias_responses
        )
        
        print(f"Evaluated {len(hallubias_results)} prompt-response pairs for hallucination/bias")
        for i, result in enumerate(hallubias_results):
            if result.success:
                print(f"  Pair {i+1}: SUCCESS")
                print(f"    Data: {result.data}")
            else:
                print(f"  Pair {i+1}: FAILED")
                print(f"    Error: {result.error_message}")
                
    except Exception as e:
        print(f"Batch evaluation failed with exception: {e}")
        import traceback
        traceback.print_exc()


def example_mixed_batch_evaluation():
    """Example of mixed batch evaluation with different types."""
    print("\n=== Mixed Batch Evaluation ===")
    
    try:
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
                print(f"  Evaluation {i+1}: SUCCESS")
                print(f"    Data: {result.data}")
            else:
                print(f"  Evaluation {i+1}: FAILED")
                print(f"    Error: {result.error_message}")
                
    except Exception as e:
        print(f"Mixed batch evaluation failed with exception: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main example function."""
    print("IF Tracer Evaluation Examples")
    print("=" * 40)
    
    try:
        # Run examples with proper error handling
        example_single_evaluations()
        example_direct_evaluator()
        example_batch_evaluations()
        
        example_mixed_batch_evaluation()
        
        print("\n=== All Examples Completed ===")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()
        print("\nNote: Some errors may be due to API endpoint issues or network connectivity.")
        print("The evaluation functionality appears to be working, but the trace/metrics export may have issues.")


if __name__ == "__main__":
    main()
