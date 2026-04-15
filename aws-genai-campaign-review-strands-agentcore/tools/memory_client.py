"""
Memory client for Campaign_Review_Memory using AWS Bedrock AgentCore Memory.
"""
import os
from bedrock_agentcore.memory import MemoryClient

_memory_client = None
_memory_id = None

def get_memory_client() -> MemoryClient:
    """Get or create memory client singleton."""
    global _memory_client
    if _memory_client is None:
        region = os.getenv("AWS_REGION", "us-east-1")
        _memory_client = MemoryClient(region_name=region)
    return _memory_client

def initialize_memory() -> str:
    """Initialize or get existing memory resource."""
    global _memory_id
    if _memory_id:
        return _memory_id
    
    client = get_memory_client()
    
    try:
        # Try to find existing memory by ID prefix
        memories = client.list_memories()
        for memory in memories:
            memory_id = memory.get('id') or memory.get('memoryId')
            if memory_id and 'Campaign_Review_Memory' in memory_id:
                _memory_id = memory_id
                print(f"✓ Using existing memory: {_memory_id}")
                return _memory_id
        
        # Create new memory if not found
        memory = client.create_memory_and_wait(
            name="Campaign_Review_Memory",
            strategies=[],
            description="Short-term memory for Campaign Review agent",
            event_expiry_days=30
        )
        _memory_id = memory['id']
        print(f"✓ Created new memory: {_memory_id}")
        return _memory_id
    except Exception as e:
        error_msg = str(e)
        if "already exists" in error_msg:
            # Memory exists, try to find it again
            try:
                memories = client.list_memories()
                for memory in memories:
                    memory_id = memory.get('id') or memory.get('memoryId')
                    if memory_id and 'Campaign_Review_Memory' in memory_id:
                        _memory_id = memory_id
                        print(f"✓ Found existing memory: {_memory_id}")
                        return _memory_id
            except Exception:
                pass
        print(f"Warning: Failed to initialize memory: {e}")
        return None
