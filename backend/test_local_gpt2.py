from transformers import pipeline

print("Loading local GPT-2...")
generator = pipeline('text-generation', model='gpt2')
print("Model loaded.")

prompt = "Explain the history of the Internet in two lines:"
output = generator(prompt, max_new_tokens=50, num_return_sequences=1)

print(f"\nPrompt: {prompt}")
print(f"Output: {output[0]['generated_text']}")
