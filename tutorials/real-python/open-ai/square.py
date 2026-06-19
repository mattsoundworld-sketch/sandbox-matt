def square(n: int | float) -> int | float:
    """Return the square of a number."""
    return n * n


if __name__ == "__main__":
    try:
        x = float(input("Enter a number: ").strip())
        print(square(x))
    except ValueError:
        print("Please enter a valid number.")
