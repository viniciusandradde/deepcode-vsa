#!/usr/bin/env python3
"""Script para corrigir api/routes/chat.py - mover get_checkpointer() para dentro das funções."""

import re
from pathlib import Path

chat_file = Path(__file__).parent.parent / "api" / "routes" / "chat.py"

if not chat_file.exists():
    print(f"❌ Arquivo não encontrado: {chat_file}")
    exit(1)

content = chat_file.read_text(encoding="utf-8")

# 1. Atualizar import
if "from core.checkpointing import get_checkpointer" in content:
    content = content.replace(
        "from core.checkpointing import get_checkpointer",
        "from core.checkpointing import get_checkpointer, get_async_checkpointer"
    )
    print("✅ Import atualizado")

# 2. Remover checkpointer do nível do módulo
if "checkpointer = get_checkpointer()" in content and "# Checkpointer will be initialized" not in content:
    # Encontrar e remover a linha
    lines = content.split("\n")
    new_lines = []
    skip_next = False
    for i, line in enumerate(lines):
        if "checkpointer = get_checkpointer()" in line and "# Initialize checkpointer" in lines[max(0, i-2):i]:
            # Substituir por comentário
            new_lines.append("# Checkpointer will be initialized in lifespan (api/main.py)")
            new_lines.append("# Use get_checkpointer() at runtime to get the initialized checkpointer")
            print("✅ Removido checkpointer do nível do módulo")
            skip_next = True
        elif skip_next and line.strip() == "":
            continue
        else:
            new_lines.append(line)
            skip_next = False
    content = "\n".join(new_lines)

# 3. Adicionar get_checkpointer() dentro de chat()
if 'async def chat(request: ChatRequest):' in content:
    # Procurar onde adicionar
    pattern = r'(# Linear tools.*?logger\.info\("✅ Linear tools enabled"\)\s*\n\s*\n)(\s*# Select agent)'
    replacement = r'\1        # Get checkpointer at runtime (after initialization in lifespan)\n        checkpointer = get_checkpointer()\n        logger.debug(f"📦 Checkpointer type: {type(checkpointer).__name__}")\n        \n\2'
    
    if "Get checkpointer at runtime" not in content:
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        print("✅ Adicionado get_checkpointer() em chat()")

# 4. Adicionar get_async_checkpointer() dentro de stream_chat()
if 'async def stream_chat(request: ChatRequest):' in content:
    pattern = r'(# Linear tools.*?logger\.info\("✅ Linear tools enabled \(stream\)"\)\s*\n\s*\n)(\s*# Select agent)'
    replacement = r'\1        # Get async checkpointer at runtime (after initialization in lifespan)\n        checkpointer = get_async_checkpointer()\n        logger.debug(f"📦 Async checkpointer type: {type(checkpointer).__name__}")\n        \n\2'
    
    if "Get async checkpointer at runtime" not in content:
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        print("✅ Adicionado get_async_checkpointer() em stream_chat()")

# Salvar
chat_file.write_text(content, encoding="utf-8")
print(f"✅ Arquivo atualizado: {chat_file}")
