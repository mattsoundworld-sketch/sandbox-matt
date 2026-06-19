from pathlib import Path

from markitdown import MarkItDown


def main() -> None:
    sample_path = Path(__file__).with_name("sample.pptx")
    output_path = Path(__file__).with_name("sample_output.md")
    md = MarkItDown()
    result = md.convert(str(sample_path))

    output_path.write_text(result.text_content, encoding="utf-8")

    print("TITLE:", result.title)
    print(f"\nMARKDOWN SAVED TO: {output_path}\n")
    print(result.text_content)


if __name__ == "__main__":
    main()
