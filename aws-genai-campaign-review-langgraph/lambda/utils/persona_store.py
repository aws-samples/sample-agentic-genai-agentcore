"""
In-memory persona store for sharing persona_id across agents.
"""

import threading
from typing import Optional

class PersonaStore:
    """Thread-safe in-memory store for persona data."""
    
    def __init__(self):
        self._store = {}
        self._lock = threading.Lock()
    
    def set_persona_id(self, session_key: str, persona_id: str) -> None:
        """Store persona_id for a session."""
        with self._lock:
            self._store[session_key] = persona_id
    
    def get_persona_id(self, session_key: str) -> Optional[str]:
        """Retrieve persona_id for a session."""
        with self._lock:
            return self._store.get(session_key)
    
    def clear_session(self, session_key: str) -> None:
        """Clear persona data for a session."""
        with self._lock:
            self._store.pop(session_key, None)

# Global instance
_persona_store = PersonaStore()

def set_current_persona_id(persona_id: str, session_key: str = "default") -> None:
    """Set the current persona_id for the session."""
    _persona_store.set_persona_id(session_key, persona_id)

def get_current_persona_id(session_key: str = "default") -> Optional[str]:
    """Get the current persona_id for the session."""
    return _persona_store.get_persona_id(session_key)

def clear_current_session(session_key: str = "default") -> None:
    """Clear the current session data."""
    _persona_store.clear_session(session_key)