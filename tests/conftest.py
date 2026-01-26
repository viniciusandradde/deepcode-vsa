"""Tests package configuration."""

import pytest


@pytest.fixture
def sample_user_request():
    """Sample user request for testing."""
    return "servidor web01 está fora do ar há 2 horas"


@pytest.fixture
def sample_glpi_ticket():
    """Sample GLPI ticket data."""
    return {
        "id": 123,
        "name": "Servidor web01 offline",
        "content": "Servidor não responde desde 10:00",
        "status": 1,
        "priority": 4,
        "urgency": 4,
    }
