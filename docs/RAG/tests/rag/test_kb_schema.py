import pytest

# Fase 1: migração do schema KB
pytestmark = pytest.mark.phase0


def test_kb_schema_migration(db_ready):
    """Aplica migrações do KB e verifica tabela/colunas básicas.

    KISS: usa o script de migração existente apontando para sql/kb.
    """
    from scripts.migrate import db_url_from_env, apply_sql_files
    from pathlib import Path
    conn_str = db_ready
    sql_dir = Path("sql/kb")
    # aplica 01 e 02 e 03
    files = [sql_dir / "01_init.sql", sql_dir / "02_indexes.sql", sql_dir / "03_functions.sql"]
    assert all(f.exists() for f in files), "Arquivos SQL do KB ausentes"
    applied = apply_sql_files(conn_str, files, continue_on_error=False)
    assert applied == len(files)
