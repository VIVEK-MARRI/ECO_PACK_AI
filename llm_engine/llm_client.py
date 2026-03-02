"""
LLM Client with provider abstraction
Supports OpenAI, Anthropic, Cohere, and local models
"""

from typing import Dict, Optional, List
from enum import Enum
from abc import ABC, abstractmethod
import json
import os
import structlog

logger = structlog.get_logger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    LOCAL = "local"
    FALLBACK = "fallback"


class BaseLLMClient(ABC):
    """Base class for LLM clients."""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        schema: Optional[Dict] = None
    ) -> Dict:
        """Generate structured JSON output."""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI API client."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """Initialize OpenAI client."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        if self.api_key:
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized", model=model)
            except ImportError:
                logger.warning("openai package not installed")
                self.client = None
        else:
            logger.warning("OpenAI API key not found")
            self.client = None
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate text using OpenAI."""
        if not self.client:
            raise ValueError("OpenAI client not initialized")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a sustainability expert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error("OpenAI generation failed", error=str(e))
            raise
    
    def generate_json(
        self,
        prompt: str,
        schema: Optional[Dict] = None
    ) -> Dict:
        """Generate structured JSON using OpenAI."""
        if not self.client:
            raise ValueError("OpenAI client not initialized")
        
        # Add JSON formatting instructions
        json_prompt = f"{prompt}\n\nRespond with valid JSON only."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                    {"role": "user", "content": json_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
        
        except Exception as e:
            logger.error("OpenAI JSON generation failed", error=str(e))
            raise


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet"):
        """Initialize Anthropic client."""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        
        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("Anthropic client initialized", model=model)
            except ImportError:
                logger.warning("anthropic package not installed")
                self.client = None
        else:
            logger.warning("Anthropic API key not found")
            self.client = None
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate text using Claude."""
        if not self.client:
            raise ValueError("Anthropic client not initialized")
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
        
        except Exception as e:
            logger.error("Anthropic generation failed", error=str(e))
            raise
    
    def generate_json(
        self,
        prompt: str,
        schema: Optional[Dict] = None
    ) -> Dict:
        """Generate structured JSON using Claude."""
        json_prompt = f"{prompt}\n\nRespond with valid JSON only."
        
        response_text = self.generate(json_prompt, temperature=0.3)
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Extract JSON from markdown code blocks if present
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            raise


class FallbackClient(BaseLLMClient):
    """Fallback rule-based client when LLM is unavailable."""
    
    def __init__(self):
        """Initialize fallback client."""
        logger.info("Fallback client initialized")
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate rule-based explanation."""
        return self._generate_rule_based_explanation(prompt)
    
    def generate_json(
        self,
        prompt: str,
        schema: Optional[Dict] = None
    ) -> Dict:
        """Generate structured fallback response."""
        return {
            "reasoning": "Rule-based recommendation (LLM unavailable)",
            "impact": "Environmental impact estimated from models",
            "tradeoffs": "Cost vs sustainability balance considered",
            "compliance": "Standard sustainability guidelines followed",
            "score_explanation": "Score based on multiple environmental factors"
        }
    
    def _generate_rule_based_explanation(self, prompt: str) -> str:
        """Generate simple rule-based explanation."""
        return (
            "This packaging was recommended based on AI model predictions "
            "considering cost, CO2 emissions, and damage probability. "
            "The recommendation balances environmental sustainability with "
            "practical requirements for your product."
        )


class LLMClient:
    """
    Unified LLM client with provider fallback.
    Attempts providers in order until one succeeds.
    """
    
    def __init__(
        self,
        provider_order: List[LLMProvider] = None,
        openai_key: Optional[str] = None,
        anthropic_key: Optional[str] = None
    ):
        """
        Initialize LLM client with provider fallback.
        
        Args:
            provider_order: Ordered list of providers to try
            openai_key: OpenAI API key
            anthropic_key: Anthropic API key
        """
        if provider_order is None:
            provider_order = [
                LLMProvider.OPENAI,
                LLMProvider.ANTHROPIC,
                LLMProvider.FALLBACK
            ]
        
        self.provider_order = provider_order
        self.clients: Dict[LLMProvider, BaseLLMClient] = {}
        
        # Initialize clients
        for provider in provider_order:
            if provider == LLMProvider.OPENAI:
                self.clients[provider] = OpenAIClient(api_key=openai_key)
            elif provider == LLMProvider.ANTHROPIC:
                self.clients[provider] = AnthropicClient(api_key=anthropic_key)
            elif provider == LLMProvider.FALLBACK:
                self.clients[provider] = FallbackClient()
        
        logger.info("LLM client initialized",
                   providers=[p.value for p in provider_order])
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text with provider fallback.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        
        Returns:
            Generated text
        """
        for provider in self.provider_order:
            client = self.clients.get(provider)
            if not client:
                continue
            
            try:
                logger.info("Attempting generation", provider=provider.value)
                result = client.generate(prompt, max_tokens, temperature)
                logger.info("Generation successful", provider=provider.value)
                return result
            
            except Exception as e:
                logger.warning("Generation failed, trying next provider",
                             provider=provider.value,
                             error=str(e))
                continue
        
        raise RuntimeError("All LLM providers failed")
    
    def generate_json(
        self,
        prompt: str,
        schema: Optional[Dict] = None
    ) -> Dict:
        """
        Generate structured JSON with provider fallback.
        
        Args:
            prompt: Input prompt
            schema: Optional JSON schema
        
        Returns:
            Generated JSON dictionary
        """
        for provider in self.provider_order:
            client = self.clients.get(provider)
            if not client:
                continue
            
            try:
                logger.info("Attempting JSON generation", provider=provider.value)
                result = client.generate_json(prompt, schema)
                logger.info("JSON generation successful", provider=provider.value)
                return result
            
            except Exception as e:
                logger.warning("JSON generation failed, trying next provider",
                             provider=provider.value,
                             error=str(e))
                continue
        
        raise RuntimeError("All LLM providers failed")
    
    def is_available(self, provider: LLMProvider) -> bool:
        """Check if a provider is available."""
        client = self.clients.get(provider)
        if not client:
            return False
        
        # For clients with API connection, check if initialized
        if hasattr(client, 'client'):
            return client.client is not None
        
        return True
