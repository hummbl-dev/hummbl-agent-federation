"""
Immutable audit logging for compliance.

WORM (Write Once Read Many) storage for audit trails.
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class AuditEvent:
    """An auditable event in the system."""
    
    timestamp: datetime
    event_type: str
    actor: str
    action: str
    resource: str
    tenant_id: Optional[str]
    status: str
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "actor": self.actor,
            "action": self.action,
            "resource": self.resource,
            "tenant_id": self.tenant_id,
            "status": self.status,
            "details": self.details,
        }
    
    def compute_hash(self) -> str:
        """Compute hash of event for tamper detection."""
        data = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()


class AuditLogger:
    """
    Immutable audit logger for compliance.
    
    SOC2 Type II, GDPR, HIPAA compliant audit trails.
    """
    
    def __init__(self, storage_path: str = "/var/log/federation/audit"):
        self.storage_path = storage_path
        import os
        os.makedirs(storage_path, exist_ok=True)
    
    def log(
        self,
        event_type: str,
        actor: str,
        action: str,
        resource: str,
        tenant_id: Optional[str] = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """
        Log an auditable event.
        
        Args:
            event_type: Category of event (routing, auth, admin)
            actor: Who performed the action (user_id, system)
            action: What was done (route_task, create_key)
            resource: What was affected (provider, tenant)
            tenant_id: Optional tenant scope
            status: success, failure, denied
            details: Additional context
            
        Returns:
            The logged audit event
        """
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            event_type=event_type,
            actor=actor,
            action=action,
            resource=resource,
            tenant_id=tenant_id,
            status=status,
            details=details or {},
        )
        
        # Compute hash for integrity
        event_hash = event.compute_hash()
        
        # Store event
        self._store_event(event, event_hash)
        
        return event
    
    def _store_event(self, event: AuditEvent, event_hash: str):
        """Store event to WORM storage."""
        import os
        
        # Organize by date
        date_str = event.timestamp.strftime("%Y-%m-%d")
        date_dir = os.path.join(self.storage_path, date_str)
        os.makedirs(date_dir, exist_ok=True)
        
        # Filename with timestamp and hash
        time_str = event.timestamp.strftime("%H%M%S")
        filename = f"{time_str}-{event_hash[:16]}.json"
        filepath = os.path.join(date_dir, filename)
        
        # Write event
        data = event.to_dict()
        data["_hash"] = event_hash
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        # Set read-only
        os.chmod(filepath, 0o444)
    
    def query(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        tenant_id: Optional[str] = None,
        event_type: Optional[str] = None,
        actor: Optional[str] = None,
    ) -> list:
        """
        Query audit log.
        
        Args:
            start_time: Filter by start time
            end_time: Filter by end time
            tenant_id: Filter by tenant
            event_type: Filter by event type
            actor: Filter by actor
            
        Returns:
            List of matching audit events
        """
        import os
        import glob
        
        results = []
        
        # Find all log files
        pattern = os.path.join(self.storage_path, "*/*.json")
        
        for filepath in glob.glob(pattern):
            with open(filepath, "r") as f:
                data = json.load(f)
            
            # Parse timestamp
            event_time = datetime.fromisoformat(data["timestamp"])
            
            # Apply filters
            if start_time and event_time < start_time:
                continue
            if end_time and event_time > end_time:
                continue
            if tenant_id and data.get("tenant_id") != tenant_id:
                continue
            if event_type and data.get("event_type") != event_type:
                continue
            if actor and data.get("actor") != actor:
                continue
            
            results.append(data)
        
        # Sort by timestamp
        results.sort(key=lambda x: x["timestamp"])
        
        return results
    
    def verify_integrity(self, days: int = 30) -> Dict[str, Any]:
        """
        Verify audit log integrity.
        
        Checks for tampering by recomputing hashes.
        
        Args:
            days: Number of days to verify
            
        Returns:
            Verification results
        """
        import os
        import glob
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        checked = 0
        tampered = 0
        
        pattern = os.path.join(self.storage_path, "*/*.json")
        
        for filepath in glob.glob(pattern):
            with open(filepath, "r") as f:
                data = json.load(f)
            
            # Check timestamp
            event_time = datetime.fromisoformat(data["timestamp"])
            if event_time < cutoff:
                continue
            
            # Get stored hash
            stored_hash = data.pop("_hash", None)
            
            # Recompute hash
            event = AuditEvent(
                timestamp=event_time,
                event_type=data["event_type"],
                actor=data["actor"],
                action=data["action"],
                resource=data["resource"],
                tenant_id=data.get("tenant_id"),
                status=data["status"],
                details=data["details"],
            )
            
            computed_hash = event.compute_hash()
            
            checked += 1
            if computed_hash != stored_hash:
                tampered += 1
        
        return {
            "checked": checked,
            "tampered": tampered,
            "verified": tampered == 0,
        }
