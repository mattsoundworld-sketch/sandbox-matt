from ollama import generate


DEFAULT_MODEL = "codellama:latest"


def generate_code(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """
    Generate code using Ollama.
    
    Args:
        model: The model to use (e.g., "codellama:latest")
        prompt: The prompt to generate code from
        
    Returns:
        The generated response text
    """
    response = generate(model=model, prompt=prompt)
    return response.get("response", "")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate code using Ollama")
    # Only allow input of the prompt via CLI; model is fixed (DEFAULT_MODEL).
    parser.add_argument("-p", "--prompt", help="Prompt to generate code from")
    args = parser.parse_args()

    if args.prompt:
        prompt = args.prompt
    else:
        try:
            prompt = input("Enter prompt: ")
        except EOFError:
            prompt = ""

    if not prompt:
        print("No prompt provided. Exiting.")
        return

    output = generate_code(prompt)
    print(output)


if __name__ == "__main__":
    main()

