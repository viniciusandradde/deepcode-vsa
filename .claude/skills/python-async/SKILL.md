---
name: python-async
description: Python async/await patterns for I/O-bound applications. Use this skill when implementing concurrent operations, async context managers, task groups, or handling multiple API calls efficiently.
---

# Python Async Patterns

## Async Basics

```python
import asyncio

# Async function definition
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# Running async code
async def main():
    result = await fetch_data("https://api.example.com/data")
    print(result)

asyncio.run(main())
```

## Concurrent Execution

```python
# Run multiple coroutines concurrently
async def fetch_all(urls: list[str]) -> list[dict]:
    tasks = [fetch_data(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return results

# With error handling
async def fetch_all_safe(urls: list[str]) -> list[dict | Exception]:
    tasks = [fetch_data(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

## Task Groups (Python 3.11+)

```python
async def fetch_with_taskgroup(urls: list[str]) -> list[dict]:
    results = []
    
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(fetch_data(url)) for url in urls]
    
    # All tasks completed successfully
    return [task.result() for task in tasks]
```

## Async Context Manager

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def managed_client():
    client = httpx.AsyncClient()
    try:
        yield client
    finally:
        await client.aclose()

# Usage
async with managed_client() as client:
    response = await client.get(url)
```

## Semaphore (Limiting Concurrency)

```python
async def fetch_with_limit(urls: list[str], max_concurrent: int = 10) -> list[dict]:
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def fetch_one(url: str) -> dict:
        async with semaphore:
            return await fetch_data(url)
    
    return await asyncio.gather(*[fetch_one(url) for url in urls])
```

## Timeout

```python
async def fetch_with_timeout(url: str, timeout: float = 10.0) -> dict:
    try:
        result = await asyncio.wait_for(fetch_data(url), timeout=timeout)
        return result
    except asyncio.TimeoutError:
        raise TimeoutError(f"Request to {url} timed out")
```

## Async Iterator

```python
async def stream_data(url: str):
    async with httpx.AsyncClient() as client:
        async with client.stream('GET', url) as response:
            async for chunk in response.aiter_bytes():
                yield chunk

# Usage
async for chunk in stream_data("https://api.example.com/stream"):
    process(chunk)
```

## Queue Pattern

```python
async def producer(queue: asyncio.Queue, items: list):
    for item in items:
        await queue.put(item)
    await queue.put(None)  # Signal end

async def consumer(queue: asyncio.Queue):
    while True:
        item = await queue.get()
        if item is None:
            break
        await process(item)
        queue.task_done()

async def main():
    queue = asyncio.Queue()
    await asyncio.gather(
        producer(queue, items),
        consumer(queue)
    )
```

## Common Anti-Patterns

```python
# ❌ WRONG: Blocking call in async function
async def bad_fetch():
    return requests.get(url)  # Blocks event loop!

# ✅ CORRECT: Use async library
async def good_fetch():
    async with httpx.AsyncClient() as client:
        return await client.get(url)

# ❌ WRONG: Sequential when could be concurrent
async def slow():
    a = await fetch_a()
    b = await fetch_b()  # Waits for a to complete
    return a, b

# ✅ CORRECT: Concurrent execution
async def fast():
    a, b = await asyncio.gather(fetch_a(), fetch_b())
    return a, b
```
