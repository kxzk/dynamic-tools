#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import math
import random
import statistics
from datetime import datetime

from fastmcp import FastMCP

mcp = FastMCP("BasicServer")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    return a - b


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b


@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide a by b (float)"""
    if b == 0:
        raise ValueError("division by zero")
    return a / b


@mcp.tool()
def factorial(n: int) -> int:
    """n! (non-negative integer)"""
    return math.factorial(n)


@mcp.tool()
def sqrt(x: float) -> float:
    """Square root of x (non-negative)"""
    if x < 0:
        raise ValueError("square root of negative")
    return math.sqrt(x)


@mcp.tool()
def random_int(low: int, high: int) -> int:
    """Random integer N such that low ≤ N ≤ high"""
    return random.randint(low, high)


@mcp.tool()
def current_datetime() -> str:
    """Current date–time in ISO-8601 format (UTC)"""
    return datetime.utcnow().isoformat()


@mcp.tool()
def count_characters(text: str) -> int:
    """Number of characters in text"""
    return len(text)


@mcp.tool()
def to_upper(text: str) -> str:
    """Convert text to UPPERCASE"""
    return text.upper()


@mcp.tool()
def to_lower(text: str) -> str:
    """Convert text to lowercase"""
    return text.lower()


@mcp.tool()
def reverse_text(text: str) -> str:
    """Return text reversed"""
    return text[::-1]


@mcp.tool()
def word_count(text: str) -> int:
    """Count words separated by whitespace"""
    return len(text.split())


@mcp.tool()
def average(nums: list[float]) -> float:
    """Arithmetic mean of a list of numbers"""
    if not nums:
        raise ValueError("empty list")
    return statistics.mean(nums)


@mcp.tool()
def get_weather(city: str) -> str:
    """(Stub) Always returns sunny for the demo"""
    return f"sunny in {city}"


if __name__ == "__main__":
    mcp.run()
