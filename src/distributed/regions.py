"""
Regional routing for compliance and latency.

Routes requests to appropriate regions based on data residency requirements.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from enum import Enum


class Region(Enum):
    """Supported deployment regions."""
    US_EAST = "us-east"
    US_WEST = "us-west"
    EU_WEST = "eu-west"
    EU_CENTRAL = "eu-central"
    APAC_SINGAPORE = "apac-singapore"
    APAC_TOKYO = "apac-tokyo"
    LOCAL = "local"


@dataclass
class RegionalConfig:
    """Configuration for a region."""
    region: Region
    providers: Set[str]  # Providers available in this region
    default_provider: str
    gdpr_compliant: bool = False
    soc2_compliant: bool = False
    hipaa_compliant: bool = False


class RegionalRouter:
    """
    Routes requests to appropriate regions based on compliance requirements.
    
    Ensures data residency for GDPR, SOC2, HIPAA compliance.
    """
    
    # Compliance to region mapping
    COMPLIANCE_REGIONS = {
        "gdpr": {Region.EU_WEST, Region.EU_CENTRAL},
        "soc2": {Region.US_EAST, Region.US_WEST, Region.EU_WEST},
        "hipaa": {Region.US_EAST, Region.US_WEST},
    }
    
    def __init__(self):
        """Initialize regional router."""
        self._regions: Dict[Region, RegionalConfig] = {}
        self._default_region = Region.US_EAST
    
    def register_region(self, config: RegionalConfig):
        """
        Register a region configuration.
        
        Args:
            config: Regional configuration
        """
        self._regions[config.region] = config
    
    def route_by_residency(
        self,
        data_residency: Optional[str],
        compliance_requirements: List[str],
    ) -> Optional[Region]:
        """
        Determine appropriate region based on residency and compliance.
        
        Args:
            data_residency: Required residency (us, eu, apac, local)
            compliance_requirements: List of compliance needs (gdpr, soc2, hipaa)
            
        Returns:
            Appropriate region or None
        """
        # Build set of acceptable regions
        acceptable_regions = set(self._regions.keys())
        
        # Filter by compliance requirements
        for req in compliance_requirements:
            req_lower = req.lower()
            if req_lower in self.COMPLIANCE_REGIONS:
                acceptable_regions &= self.COMPLIANCE_REGIONS[req_lower]
        
        # Filter by explicit data residency
        if data_residency:
            residency = data_residency.lower()
            
            if residency == "us":
                acceptable_regions &= {Region.US_EAST, Region.US_WEST}
            elif residency == "eu":
                acceptable_regions &= {Region.EU_WEST, Region.EU_CENTRAL}
            elif residency == "apac":
                acceptable_regions &= {Region.APAC_SINGAPORE, Region.APAC_TOKYO}
            elif residency == "local":
                acceptable_regions &= {Region.LOCAL}
        
        # Return first acceptable region or default
        if acceptable_regions:
            # Prefer regions in order of registration
            for region in self._regions.keys():
                if region in acceptable_regions:
                    return region
        
        return self._default_region
    
    def get_provider_for_region(
        self,
        region: Region,
        preferred_provider: Optional[str] = None,
    ) -> Optional[str]:
        """
        Get appropriate provider for a region.
        
        Args:
            region: Target region
            preferred_provider: User's preferred provider
            
        Returns:
            Provider ID available in the region
        """
        config = self._regions.get(region)
        if not config:
            return None
        
        # Use preferred if available in region
        if preferred_provider and preferred_provider in config.providers:
            return preferred_provider
        
        # Return region default
        return config.default_provider
    
    def get_regions_for_provider(self, provider_id: str) -> List[Region]:
        """
        Get all regions where a provider is available.
        
        Args:
            provider_id: Provider to check
            
        Returns:
            List of regions
        """
        regions = []
        for region, config in self._regions.items():
            if provider_id in config.providers:
                regions.append(region)
        return regions
    
    def is_provider_available(self, provider_id: str, region: Region) -> bool:
        """Check if a provider is available in a region."""
        config = self._regions.get(region)
        if not config:
            return False
        return provider_id in config.providers
    
    def setup_default_regions(self):
        """Setup default regional configuration."""
        # US East - Full provider support
        self.register_region(RegionalConfig(
            region=Region.US_EAST,
            providers={"openai", "anthropic", "openrouter", "groq", "deepseek"},
            default_provider="openai",
            soc2_compliant=True,
        ))
        
        # EU West - GDPR compliant
        self.register_region(RegionalConfig(
            region=Region.EU_WEST,
            providers={"mistral", "openrouter", "ollama"},
            default_provider="mistral",
            gdpr_compliant=True,
            soc2_compliant=True,
        ))
        
        # Local - Privacy focused
        self.register_region(RegionalConfig(
            region=Region.LOCAL,
            providers={"ollama"},
            default_provider="ollama",
            gdpr_compliant=True,
            soc2_compliant=True,
            hipaa_compliant=True,
        ))
