"""Federation SDK client."""

import httpx
from typing import Optional, Iterator, List
from datetime import datetime

from .models import RouteResponse, RouteConstraints
from .exceptions import FederationError, RoutingError, AuthenticationError


class FederationClient:
    """
    Client for the HUMMBL Agent Federation.
    
    Example:
        client = FederationClient(api_key="fk-...")
        response = client.route("Write a function to...")
        print(response.content)
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.federation.hummbl.io/v1",
        timeout: float = 60.0,
    ):
        """
        Initialize client.
        
        Args:
            api_key: Your Federation API key
            base_url: Federation API endpoint
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
        self._client = httpx.Client(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )
    
    def route(
        self,
        prompt: str,
        constraints: Optional[RouteConstraints] = None,
        system_prompt: Optional[str] = None,
    ) -> RouteResponse:
        """
        Route a task to the optimal provider.
        
        Args:
            prompt: The task to complete
            constraints: Optional routing constraints
            system_prompt: Optional system context
            
        Returns:
            RouteResponse with result and metadata
            
        Raises:
            RoutingError: If routing fails
            AuthenticationError: If API key invalid
        """
        payload = {
            "prompt": prompt,
            "system_prompt": system_prompt,
        }
        
        if constraints:
            payload["constraints"] = {
                "max_cost": constraints.max_cost,
                "max_latency_ms": constraints.max_latency_ms,
                "data_residency": constraints.data_residency,
                "gdpr_required": constraints.gdpr_required,
                "soc2_required": constraints.soc2_required,
                "hipaa_required": constraints.hipaa_required,
                "provider_preference": constraints.provider_preference,
            }
        
        response = self._client.post("/route", json=payload)
        
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code != 200:
            raise RoutingError(f"Routing failed: {response.text}")
        
        data = response.json()
        
        return RouteResponse(
            provider=data["provider"],
            model=data["model"],
            content=data["content"],
            cost=data["cost"],
            latency_ms=data["latency_ms"],
            input_tokens=data["input_tokens"],
            output_tokens=data["output_tokens"],
            confidence=data["confidence"],
            reasoning=data["reasoning"],
            created_at=datetime.utcnow(),
            raw_response=data,
        )
    
    def stream(
        self,
        prompt: str,
        constraints: Optional[RouteConstraints] = None,
    ) -> Iterator[str]:
        """
        Stream a task response.
        
        Args:
            prompt: The task to complete
            constraints: Optional routing constraints
            
        Yields:
            Content chunks as they're generated
        """
        payload = {
            "prompt": prompt,
            "stream": True,
        }
        
        if constraints:
            payload["constraints"] = constraints.__dict__
        
        with self._client.stream("POST", "/route", json=payload) as response:
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data != "[DONE]":
                        import json
                        chunk = json.loads(data)
                        yield chunk.get("content", "")
    
    def batch(
        self,
        prompts: List[str],
        constraints: Optional[RouteConstraints] = None,
        max_workers: int = 5,
    ) -> List[RouteResponse]:
        """
        Process multiple tasks in parallel.
        
        Args:
            prompts: List of tasks
            constraints: Optional constraints for all tasks
            max_workers: Maximum parallel requests
            
        Returns:
            List of responses (same order as prompts)
        """
        from concurrent.futures import ThreadPoolExecutor
        
        def route_single(prompt):
            return self.route(prompt, constraints)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(route_single, prompts))
        
        return results
    
    def health(self) -> dict:
        """Check Federation API health."""
        response = self._client.get("/health")
        return response.json()
    
    def close(self):
        """Close client connection."""
        self._client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
