---
name: vsa-external-integrations
description: External integrations for VSA. Use when implementing Linear issue creation, Telegram notifications, or other external API integrations.
---

# VSA External Integrations

## Linear Integration

### Client

```python
import httpx
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class LinearPriority(int, Enum):
    NO_PRIORITY = 0
    URGENT = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4

class LinearIssue(BaseModel):
    id: str
    identifier: str
    title: str
    url: str
    state: str

class LinearConfig(BaseModel):
    api_key: str
    team_id: str
    default_project_id: Optional[str] = None

class LinearClient:
    BASE_URL = "https://api.linear.app/graphql"
    
    def __init__(self, config: LinearConfig):
        self.config = config
        self.headers = {
            "Authorization": config.api_key,
            "Content-Type": "application/json"
        }
    
    async def create_issue(
        self,
        title: str,
        description: str,
        priority: LinearPriority = LinearPriority.NORMAL,
        labels: list[str] = None,
        dry_run: bool = True
    ) -> LinearIssue:
        """Create a Linear issue."""
        
        if dry_run:
            return LinearIssue(
                id="dry-run",
                identifier="DRY-001",
                title=title,
                url="https://linear.app/dry-run",
                state="preview"
            )
        
        mutation = """
        mutation CreateIssue($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    url
                    state { name }
                }
            }
        }
        """
        
        variables = {
            "input": {
                "teamId": self.config.team_id,
                "title": title,
                "description": description,
                "priority": priority.value
            }
        }
        
        if self.config.default_project_id:
            variables["input"]["projectId"] = self.config.default_project_id
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.BASE_URL,
                headers=self.headers,
                json={"query": mutation, "variables": variables}
            )
            response.raise_for_status()
            data = response.json()
        
        issue_data = data["data"]["issueCreate"]["issue"]
        return LinearIssue(
            id=issue_data["id"],
            identifier=issue_data["identifier"],
            title=issue_data["title"],
            url=issue_data["url"],
            state=issue_data["state"]["name"]
        )
    
    async def get_issues(
        self,
        status: str = None,
        limit: int = 50
    ) -> list[LinearIssue]:
        """Get issues from Linear."""
        query = """
        query GetIssues($teamId: String!, $first: Int) {
            team(id: $teamId) {
                issues(first: $first) {
                    nodes {
                        id
                        identifier
                        title
                        url
                        state { name }
                    }
                }
            }
        }
        """
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.BASE_URL,
                headers=self.headers,
                json={
                    "query": query,
                    "variables": {
                        "teamId": self.config.team_id,
                        "first": limit
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
        
        return [
            LinearIssue(
                id=node["id"],
                identifier=node["identifier"],
                title=node["title"],
                url=node["url"],
                state=node["state"]["name"]
            )
            for node in data["data"]["team"]["issues"]["nodes"]
        ]
```

---

## Telegram Integration

### Client

```python
class TelegramConfig(BaseModel):
    bot_token: str
    chat_id: str
    thread_id: Optional[str] = None  # For topics/threads

class TelegramClient:
    BASE_URL = "https://api.telegram.org/bot{token}"
    
    def __init__(self, config: TelegramConfig):
        self.config = config
        self.base_url = self.BASE_URL.format(token=config.bot_token)
    
    async def send_message(
        self,
        text: str,
        parse_mode: str = "MarkdownV2",
        dry_run: bool = True
    ) -> dict:
        """Send message to Telegram chat."""
        
        if dry_run:
            return {
                "ok": True,
                "result": {"message_id": 0, "dry_run": True, "text": text}
            }
        
        payload = {
            "chat_id": self.config.chat_id,
            "text": self._escape_markdown(text),
            "parse_mode": parse_mode
        }
        
        if self.config.thread_id:
            payload["message_thread_id"] = self.config.thread_id
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/sendMessage",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def send_alert(
        self,
        title: str,
        severity: str,
        description: str,
        dry_run: bool = True
    ) -> dict:
        """Send formatted alert."""
        
        emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢"
        }.get(severity.lower(), "⚪")
        
        message = f"""
{emoji} *{title}*

*Severity:* {severity.upper()}
*Time:* {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

{description}
        """.strip()
        
        return await self.send_message(message, dry_run=dry_run)
    
    def _escape_markdown(self, text: str) -> str:
        """Escape MarkdownV2 special characters."""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text
```

---

## Integration in VSA Agent

```python
class ExternalIntegrations:
    def __init__(
        self,
        linear_config: LinearConfig = None,
        telegram_config: TelegramConfig = None
    ):
        self.linear = LinearClient(linear_config) if linear_config else None
        self.telegram = TelegramClient(telegram_config) if telegram_config else None
    
    async def create_linear_from_analysis(
        self,
        analysis_result: dict,
        dry_run: bool = True
    ) -> Optional[LinearIssue]:
        """Create Linear issue from VSA analysis."""
        if not self.linear:
            return None
        
        # Map VSA priority to Linear priority
        priority_map = {
            "CRITICAL": LinearPriority.URGENT,
            "HIGH": LinearPriority.HIGH,
            "MEDIUM": LinearPriority.NORMAL,
            "LOW": LinearPriority.LOW
        }
        
        priority = priority_map.get(
            analysis_result.get("priority", "MEDIUM"),
            LinearPriority.NORMAL
        )
        
        # Build description
        description = f"""
## VSA Analysis

**Category:** {analysis_result.get('category', 'N/A')}
**Methodology:** {analysis_result.get('methodology', 'N/A')}
**GUT Score:** {analysis_result.get('gut_score', 'N/A')}

### Summary
{analysis_result.get('summary', 'No summary available')}

### Recommended Actions
{chr(10).join(f'- {a}' for a in analysis_result.get('actions', []))}

---
*Generated by VSA DeepCode*
        """
        
        return await self.linear.create_issue(
            title=f"[VSA] {analysis_result.get('title', 'Analysis Result')}",
            description=description,
            priority=priority,
            dry_run=dry_run
        )
    
    async def notify_critical_alert(
        self,
        alert: dict,
        dry_run: bool = True
    ) -> Optional[dict]:
        """Send Telegram notification for critical alerts."""
        if not self.telegram:
            return None
        
        return await self.telegram.send_alert(
            title=alert.get("title", "Critical Alert"),
            severity=alert.get("severity", "critical"),
            description=alert.get("description", ""),
            dry_run=dry_run
        )
```

---

## Configuration from Environment

```python
import os
from typing import Optional

def load_integrations_config() -> ExternalIntegrations:
    """Load integration configs from environment."""
    
    linear_config = None
    if os.getenv("LINEAR_API_KEY"):
        linear_config = LinearConfig(
            api_key=os.getenv("LINEAR_API_KEY"),
            team_id=os.getenv("LINEAR_TEAM_ID"),
            default_project_id=os.getenv("LINEAR_PROJECT_ID")
        )
    
    telegram_config = None
    if os.getenv("TELEGRAM_BOT_TOKEN"):
        telegram_config = TelegramConfig(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            chat_id=os.getenv("TELEGRAM_CHAT_ID"),
            thread_id=os.getenv("TELEGRAM_THREAD_ID")
        )
    
    return ExternalIntegrations(
        linear_config=linear_config,
        telegram_config=telegram_config
    )

# Usage
integrations = load_integrations_config()
```

---

## Environment Variables

```bash
# Linear
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LINEAR_TEAM_ID=TEAM-xxx
LINEAR_PROJECT_ID=PROJECT-xxx  # Optional

# Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=-1001234567890
TELEGRAM_THREAD_ID=123  # Optional, for topics
```
