---
name: api-patterns
description: API design patterns for Python async applications. Use this skill when designing REST API clients, implementing API tools, handling authentication, error handling, pagination, or rate limiting.
---

# API Patterns

## Async HTTP Client

```python
import httpx
from contextlib import asynccontextmanager

class AsyncAPIClient:
    def __init__(self, base_url: str, headers: dict):
        self.base_url = base_url
        self.headers = headers
        self._client: httpx.AsyncClient | None = None
    
    @asynccontextmanager
    async def session(self):
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=30.0
        )
        try:
            yield self._client
        finally:
            await self._client.aclose()
            self._client = None
    
    async def get(self, endpoint: str, params: dict = None) -> dict:
        async with self.session() as client:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
    
    async def post(self, endpoint: str, data: dict) -> dict:
        async with self.session() as client:
            response = await client.post(endpoint, json=data)
            response.raise_for_status()
            return response.json()
```

## Tool Result Pattern

```python
from pydantic import BaseModel
from typing import Optional, Any

class ToolResult(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[dict] = None

# Usage
return ToolResult(success=True, data=response_data)
return ToolResult(success=False, error="Connection timeout")
```

## APITool Contract

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Operation:
    name: str
    description: str
    method: str  # GET, POST, PUT, DELETE
    requires_confirmation: bool = False

class APITool(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @property
    @abstractmethod
    def description(self) -> str: ...
    
    @property
    @abstractmethod
    def operations(self) -> list[Operation]: ...
    
    @abstractmethod
    async def read(self, operation: str, params: dict) -> ToolResult: ...
    
    @abstractmethod
    async def write(self, operation: str, data: dict, dry_run: bool = True) -> ToolResult: ...
```

## Error Handling

```python
class APIError(Exception):
    def __init__(self, status_code: int, message: str, details: dict = None):
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

async def handle_response(response: httpx.Response) -> dict:
    if response.status_code >= 400:
        try:
            error_data = response.json()
        except:
            error_data = {"message": response.text}
        
        raise APIError(
            status_code=response.status_code,
            message=error_data.get("message", "Unknown error"),
            details=error_data
        )
    
    return response.json()
```

## Pagination

```python
async def paginate(
    self,
    endpoint: str,
    page_size: int = 50,
    max_pages: int = 10
) -> list[dict]:
    all_items = []
    
    for page in range(max_pages):
        params = {
            "offset": page * page_size,
            "limit": page_size
        }
        
        result = await self.get(endpoint, params)
        items = result.get("data", [])
        all_items.extend(items)
        
        if len(items) < page_size:
            break
    
    return all_items
```

## Rate Limiting

```python
import asyncio
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, calls_per_second: int = 10):
        self.calls_per_second = calls_per_second
        self.calls: list[datetime] = []
    
    async def acquire(self):
        now = datetime.now()
        cutoff = now - timedelta(seconds=1)
        self.calls = [c for c in self.calls if c > cutoff]
        
        if len(self.calls) >= self.calls_per_second:
            wait_time = (self.calls[0] - cutoff).total_seconds()
            await asyncio.sleep(wait_time)
        
        self.calls.append(datetime.now())
```

## Retry Pattern

```python
import asyncio
from typing import Callable, TypeVar

T = TypeVar('T')

async def retry(
    func: Callable[..., T],
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    **kwargs
) -> T:
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except APIError as e:
            if e.status_code >= 500 and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
            else:
                raise
```
