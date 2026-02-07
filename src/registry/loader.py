"""
Registry loader for YAML/JSON provider configurations.

Supports loading from files, environment variables, and dynamic discovery.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import asdict

from .models import (
    Provider, 
    ProviderCapabilities, 
    ProviderCost, 
    ProviderHealth,
    ProviderTier,
    DEFAULT_PROVIDERS,
)


class RegistryLoader:
    """
    Loads and validates provider configurations from various sources.
    
    Supports:
    - YAML files (recommended for human editing)
    - JSON files (recommended for API/programmatic)
    - Environment variables (for secrets and overrides)
    - Python dictionaries (for dynamic generation)
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the loader.
        
        Args:
            config_path: Base path for configuration files.
                        Defaults to ./config relative to current working directory.
        """
        self.config_path = config_path or Path("config")
        self._providers: Dict[str, Provider] = {}
    
    def load_defaults(self) -> Dict[str, Provider]:
        """Load the built-in default providers."""
        return DEFAULT_PROVIDERS.copy()
    
    def load_yaml(self, path: Union[str, Path]) -> Dict[str, Provider]:
        """
        Load providers from a YAML file.
        
        Args:
            path: Path to YAML file
            
        Returns:
            Dictionary of provider_id -> Provider
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Provider config not found: {path}")
        
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        return self._parse_providers(data)
    
    def load_json(self, path: Union[str, Path]) -> Dict[str, Provider]:
        """
        Load providers from a JSON file.
        
        Args:
            path: Path to JSON file
            
        Returns:
            Dictionary of provider_id -> Provider
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Provider config not found: {path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        return self._parse_providers(data)
    
    def load_directory(self, dir_path: Optional[Path] = None) -> Dict[str, Provider]:
        """
        Load all provider configs from a directory.
        
        Files are processed in order:
        1. providers.yaml (or .json)
        2. Individual provider files: {provider_id}.yaml
        
        Later files override earlier ones.
        """
        dir_path = dir_path or self.config_path
        providers = {}
        
        # Try main providers file
        for ext in ['.yaml', '.yml', '.json']:
            main_file = dir_path / f"providers{ext}"
            if main_file.exists():
                if ext == '.json':
                    providers.update(self.load_json(main_file))
                else:
                    providers.update(self.load_yaml(main_file))
                break
        
        # Load individual provider files
        if dir_path.exists():
            for file_path in sorted(dir_path.glob("*.yaml")):
                if file_path.stem != "providers":
                    providers.update(self.load_yaml(file_path))
            
            for file_path in sorted(dir_path.glob("*.json")):
                if file_path.stem != "providers":
                    providers.update(self.load_json(file_path))
        
        return providers
    
    def load_env_overrides(self) -> Dict[str, dict]:
        """
        Load provider overrides from environment variables.
        
        Format: FEDERATION_PROVIDER_{ID}_{KEY}=value
        
        Examples:
            FEDERATION_PROVIDER_OPENAI_ENABLED=false
            FEDERATION_PROVIDER_DEEPSEEK_QUALITY_SCORE=0.92
        """
        overrides = {}
        prefix = "FEDERATION_PROVIDER_"
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Parse: FEDERATION_PROVIDER_OPENAI_ENABLED -> openai, enabled
                parts = key[len(prefix):].lower().split('_')
                if len(parts) >= 2:
                    provider_id = parts[0]
                    config_key = '_'.join(parts[1:])
                    
                    if provider_id not in overrides:
                        overrides[provider_id] = {}
                    
                    # Try to parse as number/bool
                    overrides[provider_id][config_key] = self._parse_value(value)
        
        return overrides
    
    def _parse_providers(self, data: dict) -> Dict[str, Provider]:
        """Parse provider data from dictionary format."""
        providers = {}
        
        # Support both list and dict formats
        if isinstance(data, list):
            provider_list = data
        elif isinstance(data, dict) and 'providers' in data:
            provider_list = data['providers']
        elif isinstance(data, dict):
            # Direct dict of provider_id -> config
            provider_list = [
                {'id': k, **v} for k, v in data.items()
            ]
        else:
            raise ValueError(f"Invalid provider data format: {type(data)}")
        
        for config in provider_list:
            provider = self._create_provider(config)
            providers[provider.id] = provider
        
        return providers
    
    def _create_provider(self, config: dict) -> Provider:
        """Create a Provider instance from configuration dictionary."""
        # Parse tier
        tier_str = config.get('tier', 'frontier')
        tier = ProviderTier(tier_str)
        
        # Parse capabilities
        caps_config = config.get('capabilities', {})
        capabilities = ProviderCapabilities(
            max_context=caps_config.get('max_context', 4096),
            supports_functions=caps_config.get('supports_functions', False),
            supports_vision=caps_config.get('supports_vision', False),
            supports_json_mode=caps_config.get('supports_json_mode', False),
            supports_streaming=caps_config.get('supports_streaming', True),
            supports_batch=caps_config.get('supports_batch', False),
            specialties=set(caps_config.get('specialties', [])),
            typical_latency_ms=caps_config.get('typical_latency_ms'),
            throughput_tpm=caps_config.get('throughput_tpm'),
            soc2_compliant=caps_config.get('soc2_compliant', False),
            gdpr_compliant=caps_config.get('gdpr_compliant', False),
            hipaa_compliant=caps_config.get('hipaa_compliant', False),
            data_residency=set(caps_config.get('data_residency', [])),
        )
        
        # Parse cost
        cost_config = config.get('cost', {})
        cost = ProviderCost(
            input_per_1m=cost_config.get('input_per_1m', 0.0),
            output_per_1m=cost_config.get('output_per_1m', 0.0),
            context_cache_hit=cost_config.get('context_cache_hit'),
            batch_discount=cost_config.get('batch_discount'),
            currency=cost_config.get('currency', 'USD'),
        )
        
        # Create provider
        provider = Provider(
            id=config['id'],
            name=config.get('name', config['id'].title()),
            tier=tier,
            emoji=config.get('emoji', '🤖'),
            api_base=config['api_base'],
            api_key_env=config.get('api_key_env', f"{config['id'].upper()}_API_KEY"),
            capabilities=capabilities,
            cost=cost,
            enabled=config.get('enabled', True),
            quality_score=config.get('quality_score'),
            reliability_score=config.get('reliability_score'),
            models=config.get('models', []),
            docs_url=config.get('docs_url'),
            config=config.get('config', {}),
        )
        
        return provider
    
    def _parse_value(self, value: str) -> Union[str, int, float, bool]:
        """Parse environment variable value to appropriate type."""
        # Try bool
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False
        
        # Try int
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def save_yaml(self, providers: Dict[str, Provider], path: Union[str, Path]):
        """Save providers to a YAML file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'providers': [p.to_dict() for p in providers.values()]
        }
        
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    def save_json(self, providers: Dict[str, Provider], path: Union[str, Path]):
        """Save providers to a JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'providers': [p.to_dict() for p in providers.values()]
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
