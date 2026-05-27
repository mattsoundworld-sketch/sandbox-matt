from ollama import chat


def ollama_conversation(model="llama3.2:latest", system_prompt="You are a helpful assistant."):
    """
    Start an interactive conversation with Ollama chat.
    Each user prompt is appended to the conversation context until the user types 'exit'.
    """
    messages = [{"role": "system", "content": system_prompt}]
    print("Starting Ollama chat. Type 'exit' to end.")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            print("Exiting conversation.")
            break

        messages.append({"role": "user", "content": user_input})
        response = chat(model=model, messages=messages)


        print("Ollama:", response.message.content)
        messages.append({"role": "assistant", "content": response.message.content})


if __name__ == "__main__":
    ollama_conversation()
