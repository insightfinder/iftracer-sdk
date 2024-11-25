from iftracer.sdk.decorators import workflow
import openai
'''
This file is to test openai LLM model without langchain. 
'''
@workflow(name="get_chat_completion_test")
def get_gpt4o_mini_completion(messages, model="gpt-4o-mini", temperature=0.7):
    """
    Function to get a response from the GPT-4o-mini model using the updated OpenAI API.
    
    Args:
        messages (list): List of messages (system, user, assistant).
        model (str): The model to use, default is "gpt-4o-mini".
        temperature (float): Controls the randomness of the response.
    
    Returns:
        str: The model-generated response.
    """
    try:
        # Make a request to OpenAI's new Chat Completions API. Need to set API key in local env.
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        
        # Return the content of the first choice from the response
        return response
    except openai.OpenAIError as e:
        # Catching OpenAI-specific errors
        print(f"OpenAI API error: {e}")
        return None

# Example Usage
if __name__ == "__main__":
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Can you write a haiku about recursion in programming?"}
    ]
    
    response = get_gpt4o_mini_completion(messages)

    if response:
        print("GPT-4o-mini Response:", response)
