"""
Ollama adapter implementation.

Local inference for privacy and zero cost.
"""

import time
from typing import Any, Dict, AsyncIterator

import httpx

from .base import BaseAdapter, AdapterRequest, AdapterResponse


class OllamaAdapter(BaseAdapter):
    """
    Adapter for Ollama local API.
    
    Models: llama3.2, mistral, qwen2.5, phi4, etc.
    
    Known for: Privacy (local), zero cost, no internet required.
    """
    
    DEFAULT_MODEL = "llama3.2"
    
    def __init__(self, api_key: str = "", api_base: str = "http://localhost:11434", **kwargs):
        # API key is optional for local Ollama
        super().__init__("ollama", api_key or "local", api_base, **kwargs)
        self.client = httpx.AsyncClient(
            base_url=self.api_base,
            timeout=300.0,  # Local models can be slow
        )
    
    async def authenticate(self) -> bool:
        """Check if Ollama is running locally."""
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    async def complete(self, request: AdapterRequest) -> AdapterResponse:
        """Send completion request to local Ollama."""
        start_time = time.time()
        
        payload = self._build_payload(request)
        
        try:
            response = await self.client.post(
                "/api/generate",
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
        """Stream completion from Ollama."""
        payload = self._build_payload(request)
        payload["stream"] = True
        
        async with self.client.stream(
            "POST",
            "/api/generate",
            json=payload
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if not line:
                    continue
                
                import json
                chunk = json.loads(line)
                
                if chunk.get("response"):
                    yield AdapterResponse(
                        content=chunk["response"],
                        model=chunk.get("model", request.model or self.DEFAULT_MODEL),
                        provider="ollama",
                        input_tokens=0,
                        output_tokens=1,
                        total_tokens=1,
                        cost_usd=0.0,
                        raw_response=chunk,
                    )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Ollama local service health."""
        start_time = time.time()
        
        try:
            response = await self.client.get("/api/tags")
            latency_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name") for m in data.get("models", [])]
                
                return {
                    "status": "healthy",
                    "latency_ms": latency_ms,
                    "models_available": len(models),
                    "models": models[:5],  # List first 5
                    "authenticated": True,  # Local doesn't need auth
                }
            else:
                return {
                    "status": "degraded",
                    "status_code": response.status_code,
                    "latency_ms": latency_ms,
                    "authenticated": True,
                }
                
        except httpx.ConnectError:
            return {
                "status": "unhealthy",
                "error": "Ollama not running on localhost:11434",
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
        """Build Ollama API request payload."""
        # Ollama uses a simpler format
        prompt = request.prompt
        
        # If we have messages, convert to prompt
        if request.messages:
            prompt_parts = []
            for msg in request.messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "system":
                    prompt_parts.append(f"System: {content}")
                elif role == "user":
                    prompt_parts.append(f"User: {content}")
                elif role == "assistant":
                    prompt_parts.append(f"Assistant: {content}")
            prompt = "\n\n".join(prompt_parts)
        
        if request.system_prompt and not request.messages:
            prompt = f"System: {request.system_prompt}\n\nUser: {prompt}"
        
        payload = {
            "model": request.model or self.DEFAULT_MODEL,
            "prompt": prompt,
            "stream": False,
        }
        
        if request.temperature is not None:
            payload["options"] = {"temperature": request.temperature}
        
        return payload
    
    def _parse_response(self, data: Dict, latency_ms: int) -> AdapterResponse:
        """Parse Ollama response to standardized format."""
        # Ollama format is different from OpenAI
        content = data.get("response", "")
        
        # Try to extract token counts from eval_count
        eval_count = data.get("eval_count", 0)
        prompt_eval_count = data.get("prompt_eval_count", 0)
        
        return AdapterResponse(
            content=content,
            model=data.get("model", self.DEFAULT_MODEL),
            provider="ollama",
            input_tokens=prompt_eval_count,
            output_tokens=eval_count,
            total_tokens=prompt_eval_count + eval_count,
            cost_usd=0.0,  # Local = free
            response_id=None,
            finish_reason="stop" if data.get("done") else None,
            latency_ms=latency_ms,
            raw_response=data,
        )
    
    async def list_models(self) -> list:
        """List available local models."""
        response = await self.client.get("/api/tags")
        response.raise_for_status()
        data = response.json()
        return data.get("models", [])
    
    async def pull_model(self, model: str):
        """Pull a model to local Ollama."""
        response = await self.client.post(
            "/api/pull",
            json={"name": model},
        )
        response.raise_for_status()
        return response.json()
