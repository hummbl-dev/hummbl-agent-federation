"""
Load balancer for distributing requests across federation nodes.

Supports consistent hashing for sticky sessions.
"""

import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class Node:
    """A federation node in the cluster."""
    node_id: str
    host: str
    port: int
    region: str
    weight: int = 1
    healthy: bool = True
    last_heartbeat: Optional[datetime] = None
    current_load: int = 0
    
    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"


class LoadBalancer:
    """Consistent hashing load balancer for sticky sessions."""
    
    def __init__(self, virtual_nodes: int = 150):
        self.virtual_nodes = virtual_nodes
        self._nodes: Dict[str, Node] = {}
        self._ring: Dict[int, str] = {}
        self._sorted_hashes: List[int] = []
    
    def add_node(self, node: Node):
        """Add a node to the cluster."""
        self._nodes[node.node_id] = node
        
        for i in range(self.virtual_nodes * node.weight):
            key = f"{node.node_id}:{i}"
            hash_key = self._hash(key)
            self._ring[hash_key] = node.node_id
        
        self._sorted_hashes = sorted(self._ring.keys())
    
    def remove_node(self, node_id: str):
        """Remove a node from the cluster."""
        if node_id not in self._nodes:
            return
        
        del self._nodes[node_id]
        
        hashes_to_remove = [
            h for h, nid in self._ring.items() if nid == node_id
        ]
        
        for hash_key in hashes_to_remove:
            del self._ring[hash_key]
        
        self._sorted_hashes = sorted(self._ring.keys())
    
    def get_node(self, key: str) -> Optional[Node]:
        """Get the node responsible for a key using consistent hashing."""
        if not self._ring:
            return None
        
        hash_key = self._hash(key)
        
        for h in self._sorted_hashes:
            if h >= hash_key:
                node_id = self._ring[h]
                node = self._nodes.get(node_id)
                if node and node.healthy:
                    return node
        
        # Wrap around
        if self._sorted_hashes:
            node_id = self._ring[self._sorted_hashes[0]]
            node = self._nodes.get(node_id)
            if node and node.healthy:
                return node
        
        return None
    
    def get_least_loaded_node(self) -> Optional[Node]:
        """Get the node with lowest current load."""
        healthy_nodes = [n for n in self._nodes.values() if n.healthy]
        
        if not healthy_nodes:
            return None
        
        return min(healthy_nodes, key=lambda n: n.current_load / n.weight)
    
    def update_node_health(self, node_id: str, healthy: bool):
        """Update node health status."""
        if node_id in self._nodes:
            self._nodes[node_id].healthy = healthy
    
    def get_healthy_nodes(self) -> List[Node]:
        """Get all healthy nodes."""
        return [n for n in self._nodes.values() if n.healthy]
    
    def _hash(self, key: str) -> int:
        """Calculate hash for consistent hashing ring."""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
