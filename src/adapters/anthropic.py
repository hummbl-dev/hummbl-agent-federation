"""
Anthropic adapter implementation.

Supports Claude 3 (Haiku, Sonnet, Opus).
"""

import time
from typing import Any, Dict, AsyncIterator

import httpx

from .base import BaseAdapter, AdapterRequest, AdapterResponse


class AnthropicAdapter(BaseAdapter):
    """
    Adapter for Anthropic Claude API.
    
    Models: claude-3-5-sonnet, claude-3-opus, claude-3-haiku
    """
    
    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
    
    def __init__(self, api_key: str, api_base: str = "https://api.anthropic.com/v1", **kwargs):
        super().__init__("anthropic", api_key, api_base, **kwargs)
        self.client = httpx.AsyncClient(
            base_url=self.api_base,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )
    
    async def authenticate(self) -> bool:
        """Check API key by listing models."""
        try:
            response = await self.client.get("/models")
            return response.status_code == 200
        except Exception:
            return False
    
    async def complete(self, request: AdapterRequest) -> AdapterResponse:
        """Send completion request to Anthropic."""
        start_time = time.time()
        
        payload = self._build_payload(request)
        
        try:
            response = await self.client.post(
                "/messages",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            latency_ms = int((time.time() - start_time) * 1000)
            self._update_metrics(latency_ms)
            
            return self._parse_response(data, latency_ms)
            
        except Exception as e:
            self._update_metrics(int((time.time() - start_time) * 1000), error=True)
            raise
    
    async def stream(self, request: AdapterRequest) -> AsyncIterator[AdapterResponse]:
        """Stream completion from Anthropic."""
        payload = self._build_payload(request)
        payload["stream"] = True
        
        async with self.client.stream(
            "POST",
            "/messages",
            json=payload
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    
                    import json
                    event = json.loads(data)
                    
                    if event.get("type") == "content_block_delta":
                        delta = event.get("delta", {})
                        if delta.get("text"):
                            yield AdapterResponse(
                                content=delta["text"],
                                model=request.model or self.DEFAULT_MODEL,
                                provider="anthropic",
                                input_tokens=0,
                                output_tokens=1,
                                total_tokens=1,
                                cost_usd=0.0,
                                raw_response=event,
                            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Anthropic API health."""
        start_time = time.time()
        
        try:
            response = await self.client.get("/models")
            latency_ms = int((time.time() - start_time) * 1000)
            
            return {
                "status": "healthy" if response.status_code == 200 else "degraded",
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "authenticated": response.status_code != 401,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "latency_ms": None,
                "authenticated": False,
            }
    
    def _build_payload(self, request: AdapterRequest) -> Dict[str, Any]:
        """Build Anthropic API request payload."""
        payload = {
            "model": request.model or self.DEFAULT_MODEL,
            "max_tokens": request.max_tokens or 4096,
            "messages": [],
        }
        
        # System prompt is top-level in Anthropic API
        if request.system_prompt:
            payload["system"] = request.system_prompt
        
        # Build messages
        if request.messages:
            # Convert OpenAI format to Anthropic format
            for msg in request.messages:
                role = msg.get("role")
                content = msg.get("content")
                
                if role == "system":
                    continue  # Already handled
                elif role == "user":
                    payload["messages"].append({"role": "user", "content": content})
                elif role == "assistant":
                    payload["messages"].append({"role": "assistant", "content": content})
        else:
            payload["messages"].append({"role": "user", "content": request.prompt})
        
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        
        return payload
    
    def _parse_response(self, data: Dict, latency_ms: int) -> AdapterResponse:
        """Parse Anthropic response to standardized format."""
        usage = data.get("usage", {})
        
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        total_tokens = input_tokens + output_tokens
        
        cost = self._calculate_cost(input_tokens, output_tokens)
        
        # Extract content from content blocks
        content_blocks = data.get("content", [])
        content = "".join(block.get("text", "") for block in content_blocks if block.get("type") == "text")
        
        return AdapterResponse(
            content=content,
            model=data.get("model", self.DEFAULT_MODEL),
            provider="anthropic",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost,
            response_id=data.get("id"),
            finish_reason=data.get("stop_reason"),
            latency_ms=latency_ms,
            raw_response=data,
        )
