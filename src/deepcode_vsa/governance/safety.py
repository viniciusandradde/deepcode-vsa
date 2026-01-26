"""Safety Checker for command execution.

Reference: .claude/skills/vsa-safety-tools/SKILL.md
"""

import re
from dataclasses import dataclass
from typing import Optional


# Dangerous patterns that should NEVER be executed
DANGEROUS_PATTERNS: list[tuple[str, str]] = [
    # Destructive file operations
    (r"rm\s+(-rf?|--recursive)\s+/", "Recursive delete from root"),
    (r"rm\s+(-rf?|--recursive)\s+~", "Recursive delete from home"),
    (r"rm\s+-rf?\s+\*", "Recursive delete wildcard"),
    
    # Disk operations
    (r"dd\s+if=.+\s+of=/dev/", "Disk overwrite"),
    (r"mkfs\.", "Filesystem format"),
    
    # System modification
    (r"chmod\s+-R\s+777", "Insecure permissions"),
    (r"chown\s+-R\s+.*\s+/", "Root ownership change"),
    
    # Network attacks
    (r":\(\)\{:\|:&\};:", "Fork bomb"),
    (r">\s*/dev/sd[a-z]", "Direct disk write"),
    
    # Credential exposure
    (r"curl.*\|\s*bash", "Pipe from internet to bash"),
    (r"wget.*\|\s*bash", "Pipe from internet to bash"),
    
    # Database destruction
    (r"DROP\s+DATABASE", "Database drop"),
    (r"TRUNCATE\s+TABLE", "Table truncate"),
    (r"DELETE\s+FROM\s+\w+\s*;?\s*$", "Delete without WHERE"),
]

# Whitelist of safe read-only commands
SAFE_COMMANDS: list[str] = [
    "ls", "cat", "head", "tail", "grep", "find", "wc",
    "ps", "top", "df", "du", "free", "uptime",
    "date", "hostname", "whoami", "id", "pwd",
    "echo", "printf", "which", "type", "file",
    "curl -s", "wget -q",  # Read-only HTTP
    "git status", "git log", "git diff", "git branch",
]


@dataclass
class SafetyResult:
    """Result of safety check."""
    
    is_safe: bool
    command: str
    reason: Optional[str] = None
    matched_pattern: Optional[str] = None
    recommendation: Optional[str] = None


class SafetyChecker:
    """Command safety checker.
    
    Validates commands before execution to prevent
    dangerous operations.
    """
    
    def __init__(
        self,
        dangerous_patterns: list[tuple[str, str]] = None,
        safe_commands: list[str] = None,
        strict_mode: bool = True
    ):
        self.dangerous_patterns = dangerous_patterns or DANGEROUS_PATTERNS
        self.safe_commands = safe_commands or SAFE_COMMANDS
        self.strict_mode = strict_mode
    
    def check(self, command: str) -> SafetyResult:
        """Check if command is safe to execute.
        
        Args:
            command: Command string to check
            
        Returns:
            SafetyResult with safety assessment
        """
        # Check against dangerous patterns
        for pattern, description in self.dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return SafetyResult(
                    is_safe=False,
                    command=command,
                    reason=f"Matches dangerous pattern: {description}",
                    matched_pattern=pattern,
                    recommendation="This command is blocked for safety."
                )
        
        # Check whitelist in strict mode
        if self.strict_mode:
            command_base = command.split()[0] if command.strip() else ""
            is_whitelisted = any(
                command.startswith(safe) 
                for safe in self.safe_commands
            )
            
            if not is_whitelisted:
                return SafetyResult(
                    is_safe=False,
                    command=command,
                    reason="Command not in whitelist (strict mode)",
                    recommendation=f"Add '{command_base}' to safe_commands or disable strict mode"
                )
        
        return SafetyResult(
            is_safe=True,
            command=command,
            reason="Command passed safety checks"
        )
    
    def is_read_only(self, command: str) -> bool:
        """Check if command is read-only."""
        read_only_prefixes = [
            "ls", "cat", "head", "tail", "grep", "find",
            "ps", "df", "du", "free", "top",
            "SELECT", "SHOW", "DESCRIBE", "EXPLAIN"
        ]
        
        command_base = command.strip().split()[0] if command.strip() else ""
        return any(
            command.upper().startswith(prefix.upper())
            for prefix in read_only_prefixes
        )
    
    def suggest_safe_alternative(self, command: str) -> Optional[str]:
        """Suggest a safer alternative for dangerous commands."""
        suggestions = {
            "rm -rf": "Use 'mv' to a trash directory instead",
            "chmod 777": "Use more restrictive permissions like 755 or 644",
            "DELETE FROM": "Add a WHERE clause to limit scope",
        }
        
        for dangerous, suggestion in suggestions.items():
            if dangerous in command:
                return suggestion
        
        return None
