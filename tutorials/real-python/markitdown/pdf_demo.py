from markitdown import MarkItDown


def main() -> None:
    md = MarkItDown()
    result = md.convert("sample.pdf")

    print("TITLE:", result.title)
    print("\nMARKDOWN OUTPUT:\n")
    print(result.text_content)


if __name__ == "__main__":
    main()
