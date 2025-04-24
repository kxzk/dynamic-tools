#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import os
import random
import re
import statistics
from datetime import datetime

import duckdb
from fastmcp import Client
from sentence_transformers import SentenceTransformer

DB_FILE = "tools.duckdb"
MODEL_ID = "BAAI/bge-small-en-v1.5"
METRIC = "cosine"


async def build_index(client) -> SentenceTransformer:
    tools = await client.list_tools()
    con = duckdb.connect(
        DB_FILE, config={"hnsw_enable_experimental_persistence": "true"}
    )
    con.execute("INSTALL vss; LOAD vss;")
    con.execute("DROP TABLE IF EXISTS tools;")
    con.execute(
        """
        CREATE TABLE tools(
            id INT, name TEXT, description TEXT, emb FLOAT[384]
        );
    """
    )
    encoder = SentenceTransformer(MODEL_ID, device="cpu")
    for idx, t in enumerate(tools):
        vec = encoder.encode(
            f"{t.name}: {t.description}", normalize_embeddings=True
        ).tolist()
        con.execute(
            "INSERT INTO tools VALUES (?,?,?,?)", [idx, t.name, t.description, vec]
        )
    con.execute(
        f"""
        CREATE INDEX idx_hnsw ON tools USING HNSW(emb)
        WITH (metric='{METRIC}', ef_construction=128, M=16);
    """
    )
    con.close()
    return encoder


_num_pat = re.compile(r"-?\d+(?:\.\d+)?")


def _numbers(txt: str) -> list[float]:
    return [float(x) for x in _num_pat.findall(txt)]


def parse_args(tool: str, query: str):
    """
    This is dumb, just for POC
    """
    low_high = _numbers(query)
    txt = query.split(":", 1)[-1].strip() if ":" in query else query.strip()

    match tool:
        case "add" | "subtract" | "multiply" | "divide":
            if len(low_high) >= 2:
                a, b = low_high[:2]
            else:
                return ({}, True)
            return ({"a": a, "b": b}, False)

        case "factorial":
            if low_high:
                return ({"n": int(low_high[0])}, False)
            return ({}, True)

        case "sqrt":
            if low_high:
                return ({"x": float(low_high[0])}, False)
            return ({}, True)

        case "random_int":
            if len(low_high) >= 2:
                lo, hi = map(int, low_high[:2])
            else:
                lo, hi = 1, 100
            return ({"low": lo, "high": hi}, False)

        case "current_datetime":
            return ({}, False)

        case "get_weather":
            # naive city extraction: word after 'in', else last token
            city = re.search(r"in ([A-Za-z ]+)", query) or re.search(
                r"weather in ([A-Za-z ]+)", query
            )
            city = city.group(1).strip() if city else txt
            return ({"city": city}, False)

        case (
            "count_characters" | "to_upper" | "to_lower" | "reverse_text" | "word_count"
        ):
            return ({"text": txt}, False)

        case "average":
            if low_high:
                return ({"nums": low_high}, False)
            return ({}, True)

        case _:
            return ({}, True)


async def choose_and_run(client, encoder, query: str):
    qvec = encoder.encode(query, normalize_embeddings=True).tolist()
    con = duckdb.connect(DB_FILE)
    top3 = con.execute(
        "SELECT name, array_cosine_distance(emb, ?::FLOAT[384]) AS d "
        "FROM tools ORDER BY d LIMIT 3;",
        [qvec],
    ).fetchall()
    con.close()

    print(f"\n[top 3 tools 🛠️]")
    for i, (n, d) in enumerate(top3, 1):
        print(f"  {i}.{n:<20} dist={d:.4f}")
    print()

    name, _ = top3[0]

    kwargs, need_prompt = parse_args(name, query)
    if need_prompt:
        # ask user for missing params
        sig_parts = []
        for k in client.get_tool_signature(name).parameters:
            if k not in kwargs:
                val = await asyncio.to_thread(input, f"  {k}= ")
                kwargs[k] = float(val) if val.replace(".", "", 1).isdigit() else val
            sig_parts.append(f"{k}={kwargs[k]}")
        print(f"→ ☎️ {name}({', '.join(sig_parts)})")

    result = await client.call_tool(name, kwargs)
    return name, result


async def main():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    async with Client("./basic.py") as client:
        encoder = await build_index(client)
        print("🤖  Dynamic-tool REPL  |  'help' to list tools, 'quit' to exit\n")

        while True:
            query = await asyncio.to_thread(input, "Query> ")
            if query.lower() in {"exit", "quit"}:
                break
            if query.lower() == "help":
                for t in await client.list_tools():
                    print(f"- {t.name}: {t.description}")
                print()
                continue
            try:
                name, out = await choose_and_run(client, encoder, query)
                print(f"Result ({name}) → {out}\n")
            except Exception as exc:
                print(f"⚠️  {exc}\n")


if __name__ == "__main__":
    asyncio.run(main())
