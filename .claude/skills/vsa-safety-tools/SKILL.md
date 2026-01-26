---
name: vsa-safety-tools
description: Computer Use safety patterns for VSA. Use when implementing bash tool with safety checks, str_replace_editor tool, or any tool that modifies system state. Includes dangerous command detection and dry-run patterns.
---

# VSA Safety & Computer Use Tools

## Safety Checker

### Dangerous Patterns

```python
import re
from dataclasses import dataclass
from typing import Optional

DANGEROUS_PATTERNS = [
    # File destruction
    (r"rm\s+(-rf?|--recursive)\s+/", "Recursive delete from root"),
    (r"rm\s+(-rf?|--recursive)\s+\*", "Recursive delete wildcard"),
    (r">\s*/dev/sd[a-z]", "Direct disk write"),
    (r"dd\s+if=.+\s+of=/dev/", "Disk overwrite"),
    (r"mkfs\.", "Filesystem format"),
    
    # System destruction
    (r":\(\)\{\s*:\|:&\s*\};:", "Fork bomb"),
    (r"chmod\s+(-R|--recursive)\s+777\s+/", "Recursive chmod 777 root"),
    (r"chown\s+(-R|--recursive)\s+.+\s+/\s*$", "Recursive chown root"),
    
    # Dangerous operations
    (r"curl.+\|\s*(ba)?sh", "Piped curl to shell"),
    (r"wget.+\|\s*(ba)?sh", "Piped wget to shell"),
    (r">\s*/etc/(passwd|shadow)", "Overwrite auth files"),
    
    # Network attacks
    (r"nmap\s+-sS", "SYN scan (requires root)"),
    (r"hping3", "Potential DoS tool"),
]

@dataclass
class SafetyCheckResult:
    is_safe: bool
    reason: Optional[str] = None
    blocked_pattern: Optional[str] = None
```

### Safety Checker Class

```python
class SafetyChecker:
    def __init__(self, whitelist: list[str] = None):
        self.whitelist = whitelist or [
            # Safe read commands
            "ls", "cat", "head", "tail", "less", "more",
            "find", "grep", "awk", "sed", "wc", "sort",
            "df", "du", "free", "top", "htop", "ps",
            
            # Safe dev tools
            "git", "npm", "pip", "python", "node",
            "docker", "docker-compose", "kubectl",
            "pytest", "ruff", "mypy",
            
            # Safe system info
            "uname", "hostname", "whoami", "id",
            "systemctl status", "journalctl",
        ]
    
    def check(self, command: str) -> SafetyCheckResult:
        # Check dangerous patterns
        for pattern, reason in DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return SafetyCheckResult(
                    is_safe=False,
                    reason=f"Blocked: {reason}",
                    blocked_pattern=pattern
                )
        
        # Check if command starts with whitelisted
        cmd_start = command.strip().split()[0] if command.strip() else ""
        if any(command.strip().startswith(w) for w in self.whitelist):
            return SafetyCheckResult(is_safe=True)
        
        # Unknown command - require explicit approval
        return SafetyCheckResult(
            is_safe=False,
            reason=f"Unknown command '{cmd_start}' - requires approval"
        )
```

---

## Bash Tool (OpenCode-style)

```python
import subprocess
import asyncio
from pydantic import BaseModel, Field
from typing import Optional

class BashInput(BaseModel):
    command: str = Field(..., description="Shell command to execute")
    cwd: Optional[str] = Field(None, description="Working directory")
    timeout: int = Field(30, description="Timeout in seconds")
    dry_run: bool = Field(True, description="Preview without executing")
    safety_check: bool = Field(True, description="Run safety checks")

class BashOutput(BaseModel):
    success: bool
    stdout: str
    stderr: str
    return_code: int
    dry_run: bool
    safety_blocked: bool = False
    safety_reason: Optional[str] = None

async def bash_tool(input: BashInput) -> BashOutput:
    """Execute shell command with safety checks."""
    checker = SafetyChecker()
    
    # Safety check
    if input.safety_check:
        result = checker.check(input.command)
        if not result.is_safe:
            return BashOutput(
                success=False,
                stdout="",
                stderr=result.reason,
                return_code=-1,
                dry_run=input.dry_run,
                safety_blocked=True,
                safety_reason=result.reason
            )
    
    # Dry run - just show what would execute
    if input.dry_run:
        return BashOutput(
            success=True,
            stdout=f"[DRY RUN] Would execute: {input.command}",
            stderr="",
            return_code=0,
            dry_run=True
        )
    
    # Execute command
    try:
        process = await asyncio.create_subprocess_shell(
            input.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=input.cwd
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=input.timeout
        )
        
        return BashOutput(
            success=process.returncode == 0,
            stdout=stdout.decode(),
            stderr=stderr.decode(),
            return_code=process.returncode,
            dry_run=False
        )
    except asyncio.TimeoutError:
        return BashOutput(
            success=False,
            stdout="",
            stderr=f"Command timed out after {input.timeout}s",
            return_code=-1,
            dry_run=False
        )
```

---

## Str Replace Editor Tool (OpenCode-style)

```python
from pathlib import Path
from enum import Enum

class EditorCommand(str, Enum):
    VIEW = "view"
    CREATE = "create"
    STR_REPLACE = "str_replace"
    INSERT = "insert"

class EditorInput(BaseModel):
    command: EditorCommand
    path: str
    file_text: Optional[str] = None
    old_str: Optional[str] = None
    new_str: Optional[str] = None
    insert_line: Optional[int] = None
    view_range: Optional[tuple[int, int]] = None
    dry_run: bool = True

class EditorOutput(BaseModel):
    success: bool
    content: Optional[str] = None
    message: str
    dry_run: bool

def str_replace_editor_tool(input: EditorInput) -> EditorOutput:
    """File editing with safety and dry-run support."""
    path = Path(input.path)
    
    if input.command == EditorCommand.VIEW:
        if not path.exists():
            return EditorOutput(
                success=False,
                message=f"File not found: {path}",
                dry_run=input.dry_run
            )
        
        content = path.read_text()
        
        # Apply range if specified
        if input.view_range:
            lines = content.split('\n')
            start, end = input.view_range
            content = '\n'.join(lines[start-1:end])
        
        return EditorOutput(
            success=True,
            content=content,
            message=f"Viewed {path}",
            dry_run=input.dry_run
        )
    
    elif input.command == EditorCommand.CREATE:
        if input.dry_run:
            return EditorOutput(
                success=True,
                message=f"[DRY RUN] Would create {path}",
                content=input.file_text,
                dry_run=True
            )
        
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(input.file_text)
        return EditorOutput(
            success=True,
            message=f"Created {path}",
            dry_run=False
        )
    
    elif input.command == EditorCommand.STR_REPLACE:
        content = path.read_text()
        
        # Check uniqueness
        count = content.count(input.old_str)
        if count == 0:
            return EditorOutput(
                success=False,
                message=f"String not found: '{input.old_str[:50]}...'",
                dry_run=input.dry_run
            )
        if count > 1:
            return EditorOutput(
                success=False,
                message=f"String found {count} times - must be unique",
                dry_run=input.dry_run
            )
        
        new_content = content.replace(input.old_str, input.new_str)
        
        if input.dry_run:
            return EditorOutput(
                success=True,
                message=f"[DRY RUN] Would replace in {path}",
                content=new_content,
                dry_run=True
            )
        
        path.write_text(new_content)
        return EditorOutput(
            success=True,
            message=f"Replaced in {path}",
            dry_run=False
        )
    
    elif input.command == EditorCommand.INSERT:
        content = path.read_text()
        lines = content.split('\n')
        
        # Insert at line
        lines.insert(input.insert_line - 1, input.file_text)
        new_content = '\n'.join(lines)
        
        if input.dry_run:
            return EditorOutput(
                success=True,
                message=f"[DRY RUN] Would insert at line {input.insert_line}",
                content=new_content,
                dry_run=True
            )
        
        path.write_text(new_content)
        return EditorOutput(
            success=True,
            message=f"Inserted at line {input.insert_line}",
            dry_run=False
        )
```

---

## Tool Schemas (Anthropic Format)

```python
BASH_TOOL_SCHEMA = {
    "name": "bash",
    "description": "Execute shell commands with safety checks",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command to execute"
            },
            "cwd": {
                "type": "string",
                "description": "Working directory"
            },
            "timeout": {
                "type": "integer",
                "default": 30,
                "description": "Timeout in seconds"
            },
            "dry_run": {
                "type": "boolean",
                "default": True,
                "description": "Preview without executing"
            }
        },
        "required": ["command"]
    }
}

EDITOR_TOOL_SCHEMA = {
    "name": "str_replace_editor",
    "description": "View, create, or edit files",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "enum": ["view", "create", "str_replace", "insert"],
                "description": "Action to perform"
            },
            "path": {
                "type": "string",
                "description": "File path"
            },
            "file_text": {
                "type": "string",
                "description": "Content for create/insert"
            },
            "old_str": {
                "type": "string",
                "description": "String to replace (str_replace)"
            },
            "new_str": {
                "type": "string",
                "description": "Replacement string (str_replace)"
            },
            "insert_line": {
                "type": "integer",
                "description": "Line number for insert"
            }
        },
        "required": ["command", "path"]
    }
}
```
