"""
OpenAI adapter implementation.

Supports GPT-4, GPT-3.5, and future OpenAI models.
"""

import time
from typing import Any, Dict, AsyncIterator

import httpx

from .base import BaseAdapter, AdapterRequest, AdapterResponse


class OpenAIAdapter(BaseAdapter):
    """
    Adapter for OpenAI API.
    
    Models: gpt-4o, gpt-4o-mini, o1, o3-mini, gpt-3.5-turbo
    """
    
    DEFAULT_MODEL = "gpt-4o"
    
    def __init__(self, api_key: str, api_base: str = "https://api.openai.com/v1", **kwargs):
        super().__init__("openai", api_key, api_base, **kwargs)
        self.client = httpx.AsyncClient(
            base_url=self.api_base,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )
    
    async def authenticate(self) -> bool:
        """Check API key validity by listing models."""
        try:
            response = await self.client.get("/models")
            return response.status_code == 200
        except Exception:
            return False
    
    async def complete(self, request: AdapterRequest) -> AdapterResponse:
        """Send completion request to OpenAI."""
        start_time = time.time()
        
        payload = self._build_payload(request)
        
        try:
            response = await self.client.post(
                "/chat/completions",
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
        """Stream completion from OpenAI."""
        payload = self._build_payload(request)
        payload["stream"] = True
        
        async with self.client.stream(
            "POST",
            "/chat/completions",
            json=payload
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    
                    import json
                    chunk = json.loads(data)
                    
                    # Yield partial response
                    if chunk.get("choices"):
                        delta = chunk["choices"][0].get("delta", {})
                        if delta.get("content"):
                            yield AdapterResponse(
                                content=delta["content"],
                                model=chunk.get("model", request.model or self.DEFAULT_MODEL),
                                provider="openai",
                                input_tokens=0,  # Not available in streaming
                                output_tokens=1,  # Estimate
                                total_tokens=1,
                                cost_usd=0.0,  # Calculate at end
                                raw_response=chunk,
                            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check OpenAI API health."""
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
        except httpx.ConnectError:
            return {
                "status": "unhealthy",
                "error": "Connection failed",
                "latency_ms": None,
                "authenticated": False,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "latency_ms": None,
                "authenticated": False,
            }
    
    def _build_payload(self, request: AdapterRequest) -> Dict[str, Any]:
        """Build OpenAI API request payload."""
        messages = []
        
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        
        if request.messages:
            messages.extend(request.messages)
        else:
            messages.append({"role": "user", "content": request.prompt})
        
        payload = {
            "model": request.model or self.DEFAULT_MODEL,
            "messages": messages,
        }
        
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        
        if request.json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        return payload
    
    def _parse_response(self, data: Dict, latency_ms: int) -> AdapterResponse:
        """Parse OpenAI response to standardized format."""
        choice = data["choices"][0]
        usage = data.get("usage", {})
        
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", input_tokens + output_tokens)
        
        cost = self._calculate_cost(input_tokens, output_tokens)
        
        return AdapterResponse(
            content=choice["message"]["content"],
            model=data.get("model", self.DEFAULT_MODEL),
            provider="openai",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost,
            response_id=data.get("id"),
            finish_reason=choice.get("finish_reason"),
            latency_ms=latency_ms,
            raw_response=data,
        )
