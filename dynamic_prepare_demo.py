#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import random
from typing import List

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.test import TestModel
from pydantic_ai.tools import Tool, ToolDefinition


def weather(city: str) -> str:
    """Return the weather for city"""
    return "sunny in {city}"


def dice_roll(sides: int = 6) -> int:
    return random.randint(1, sides)


def greet(name: str) -> str:
    return f"hello, {name}"


keywords: dict[str, List[str]] = {
    "weather": ["weather", "forecast", "temperature", "rain"],
    "dice_roll": ["dice", "roll", "random number"],
    "greet": ["hello", "hi", "greet", "name"],
}


def choose_tools(mesage: str, top_k: int = 2) -> list[str]:
    message_lower = mesage.lower()
    scored = []
    for n, k in keywords.items():
        score = sum(word in message_lower for word in k)
        if score:
            scored.append((score, n))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [name for _, name in scored[:top_k]]


async def prepare_from_keywords(
    ctx: RunContext, tool_def: ToolDefinition
) -> ToolDefinition | None:
    # print(f"{ctx=}")
    visible = choose_tools(ctx.prompt)
    print(f"tools_visible={visible}")
    return tool_def if tool_def.name in visible else None


tools = [
    Tool(weather, prepare=prepare_from_keywords),
    Tool(dice_roll, prepare=prepare_from_keywords),
    Tool(greet, prepare=prepare_from_keywords),
]

agent = Agent(TestModel(), tools=tools)

if __name__ == "__main__":
    print("— Query 1 —")
    out1 = agent.run_sync("What will the weather be like in Tokyo tomorrow?")
    print(out1.output)  # expect weather tool call

    print("\n— Query 2 —")
    out2 = agent.run_sync("Can you say hello to Ada?")
    print(out2.output)
