"""
In-memory payload store for sharing campaign_id and bucket_name across agents.
"""

import threading
from typing import Optional


class PayloadStore:
    """Thread-safe in-memory store for payload data."""
    
    def __init__(self):
        self._store = {}
        self._lock = threading.Lock()
    
    def set_campaign_id(self, session_key: str, campaign_id: str) -> None:
        """Store campaign_id for a session."""
        with self._lock:
            if session_key not in self._store:
                self._store[session_key] = {}
            self._store[session_key]['campaign_id'] = campaign_id
    
    def get_campaign_id(self, session_key: str) -> Optional[str]:
        """Retrieve campaign_id for a session."""
        with self._lock:
            return self._store.get(session_key, {}).get('campaign_id')
    
    def set_bucket_name(self, session_key: str, bucket_name: str) -> None:
        """Store bucket_name for a session."""
        with self._lock:
            if session_key not in self._store:
                self._store[session_key] = {}
            self._store[session_key]['bucket_name'] = bucket_name
    
    def get_bucket_name(self, session_key: str) -> Optional[str]:
        """Retrieve bucket_name for a session."""
        with self._lock:
            return self._store.get(session_key, {}).get('bucket_name')
    
    def clear_session(self, session_key: str) -> None:
        """Clear payload data for a session."""
        with self._lock:
            self._store.pop(session_key, None)


# Global instance
_payload_store = PayloadStore()


def set_campaign_id(campaign_id: str, session_key: str = "default") -> None:
    """Set the campaign_id for the session."""
    _payload_store.set_campaign_id(session_key, campaign_id)


def get_campaign_id(session_key: str = "default") -> Optional[str]:
    """Get the campaign_id for the session."""
    return _payload_store.get_campaign_id(session_key)


def set_bucket_name(bucket_name: str, session_key: str = "default") -> None:
    """Set the bucket_name for the session."""
    _payload_store.set_bucket_name(session_key, bucket_name)


def get_bucket_name(session_key: str = "default") -> Optional[str]:
    """Get the bucket_name for the session."""
    return _payload_store.get_bucket_name(session_key)


def clear_session(session_key: str = "default") -> None:
    """Clear the session data."""
    _payload_store.clear_session(session_key)
