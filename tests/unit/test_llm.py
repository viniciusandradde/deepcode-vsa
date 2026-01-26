"""Tests for LLM Client and Model Router."""

import pytest

from deepcode_vsa.config.settings import LLMSettings, ModelTier
from deepcode_vsa.llm.openrouter import ModelRouter, ModelConfig, OpenRouterClient


class TestModelRouter:
    """Tests for ModelRouter."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return LLMSettings(
            api_key="test-key",
            fast_model="test/fast",
            smart_model="test/smart",
            creative_model="test/creative",
            premium_model="test/premium",
            default_tier=ModelTier.SMART,
        )
    
    @pytest.fixture
    def router(self, settings):
        """Create test router."""
        return ModelRouter(settings)
    
    def test_get_model_default(self, router):
        """Test getting default model."""
        config = router.get_model()
        
        assert config.model_id == "test/smart"  # Default tier
    
    def test_get_model_by_tier(self, router):
        """Test getting model by tier."""
        fast = router.get_model(ModelTier.FAST)
        assert fast.model_id == "test/fast"
        
        premium = router.get_model(ModelTier.PREMIUM)
        assert premium.model_id == "test/premium"
    
    def test_route_by_task_classify(self, router):
        """Test routing classification tasks."""
        config = router.route_by_task("classify")
        
        assert config.model_id == "test/fast"
        assert config.temperature == 0.3  # Lower for deterministic
    
    def test_route_by_task_plan(self, router):
        """Test routing planning tasks."""
        config = router.route_by_task("plan")
        
        assert config.model_id == "test/smart"
    
    def test_route_by_task_report(self, router):
        """Test routing report tasks."""
        config = router.route_by_task("report")
        
        assert config.model_id == "test/creative"
        assert config.temperature == 0.9  # Higher for creativity
    
    def test_route_by_task_unknown(self, router):
        """Test routing unknown tasks (uses default)."""
        config = router.route_by_task("unknown_task")
        
        assert config.model_id == "test/smart"  # Default


class TestModelConfig:
    """Tests for ModelConfig."""
    
    def test_default_values(self):
        """Test default config values."""
        config = ModelConfig(model_id="test/model")
        
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
    
    def test_custom_values(self):
        """Test custom config values."""
        config = ModelConfig(
            model_id="test/model",
            max_tokens=8192,
            temperature=0.5
        )
        
        assert config.max_tokens == 8192
        assert config.temperature == 0.5


class TestOpenRouterClient:
    """Tests for OpenRouterClient."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        settings = LLMSettings(api_key="test-key")
        return OpenRouterClient(settings)
    
    def test_headers(self, client):
        """Test request headers."""
        headers = client.headers
        
        assert "Authorization" in headers
        assert "Bearer test-key" in headers["Authorization"]
        assert "X-Title" in headers
        assert headers["X-Title"] == "DeepCode VSA"
    
    def test_get_content(self, client):
        """Test content extraction from response."""
        response = {
            "choices": [
                {
                    "message": {
                        "content": "This is the response"
                    }
                }
            ]
        }
        
        content = client.get_content(response)
        
        assert content == "This is the response"
    
    def test_base_url(self, client):
        """Test base URL."""
        assert client.BASE_URL == "https://openrouter.ai/api/v1"
