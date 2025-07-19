from langchain_core.tools import tool

@tool
def add(x: int, y: int) -> int:
    """
    Add two numbers
    """
    return x + y
