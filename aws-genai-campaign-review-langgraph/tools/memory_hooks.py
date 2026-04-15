"""
Memory hooks for Nike Supply Chain Agent.
"""
import logging
import json
from bedrock_agentcore.memory import MemoryClient
from strands.hooks import AgentInitializedEvent, MessageAddedEvent, AfterToolCallEvent, HookProvider, HookRegistry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShortTermMemoryHook(HookProvider):
    """Hook to store and retrieve short-term conversation memory."""
    
    def __init__(self, memory_client: MemoryClient, memory_id: str):
        self.memory_client = memory_client
        self.memory_id = memory_id
        self.tool_results = []  # Track tool results for current session
        logger.info(f"🧠 Memory hook initialized with memory_id: {memory_id}")
    
    def on_agent_initialized(self, event: AgentInitializedEvent):
        """Load conversation history when agent starts."""
        try:
            actor_id = event.agent.state.get("actor_id")
            session_id = event.agent.state.get("session_id")
            
            if not actor_id or not session_id or not self.memory_id:
                logger.warning(f"⚠️  Memory load skipped - missing: actor_id={actor_id}, session_id={session_id}, memory_id={self.memory_id}")
                return
            
            logger.info(f"📖 Loading memory for session: {session_id}, actor: {actor_id}")
            
            # Get last 10 conversation turns
            recent_turns = self.memory_client.get_last_k_turns(
                memory_id=self.memory_id,
                actor_id=actor_id,
                session_id=session_id,
                k=10,
                branch_name="main"
            )
            
            if recent_turns:
                context_messages = []
                logger.info(f"✅ Loaded {len(recent_turns)} conversation turns from memory")
                logger.info("=" * 80)
                logger.info("📥 EXTRACTED FROM MEMORY:")
                logger.info("=" * 80)
                
                for i, turn in enumerate(recent_turns, 1):
                    for message in turn:
                        role = message['role'].title()
                        content = message['content']['text']
                        context_messages.append(f"{role}: {content}")
                        logger.info(f"Turn {i} - {role}:")
                        logger.info(f"  {content[:500]}{'...' if len(content) > 500 else ''}")
                        logger.info("-" * 80)
                
                context = "\n".join(context_messages)
                event.agent.system_prompt += f"\n\n## Previous Conversation Context:\n{context}\n"
                logger.info("=" * 80)
            else:
                logger.info(f"ℹ️  No previous conversation found for session: {session_id}")
                
        except Exception as e:
            logger.error(f"❌ Failed to load conversation history: {e}", exc_info=True)
    
    def on_tool_executed(self, event: AfterToolCallEvent):
        """Track tool execution results."""
        try:
            tool_name = event.tool_use.name if hasattr(event.tool_use, 'name') else "unknown"
            tool_args = event.tool_use.input if hasattr(event.tool_use, 'input') else {}
            tool_result = event.result
            
            # Store tool result
            tool_summary = {
                "tool": tool_name,
                "args": tool_args,
                "result": str(tool_result)[:500]  # Truncate long results
            }
            self.tool_results.append(tool_summary)
            
            logger.info("=" * 80)
            logger.info(f"🔧 TOOL EXECUTED: {tool_name}")
            logger.info(f"  Args: {json.dumps(tool_args, indent=2) if isinstance(tool_args, dict) else str(tool_args)}")
            logger.info(f"  Result: {str(tool_result)[:300]}{'...' if len(str(tool_result)) > 300 else ''}")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Failed to track tool execution: {e}", exc_info=True)
    
    def on_message_added(self, event: MessageAddedEvent):
        """Store new messages to memory."""
        try:
            actor_id = event.agent.state.get("actor_id")
            session_id = event.agent.state.get("session_id")
            
            if not actor_id or not session_id or not self.memory_id:
                logger.warning(f"⚠️  Memory store skipped - missing: actor_id={actor_id}, session_id={session_id}, memory_id={self.memory_id}")
                return
            
            messages = event.agent.messages
            if messages:
                last_message = messages[-1]
                content = last_message.get("content", "")
                
                # Handle different content structures
                if isinstance(content, list):
                    content = content[0].get("text", "") if content else ""
                
                if content:
                    # If this is an assistant message and we have tool results, append them
                    if last_message['role'] == 'assistant' and self.tool_results:
                        tool_context = "\n\n[Tool Execution Context]\n"
                        for tool in self.tool_results:
                            tool_context += f"- {tool['tool']}: {tool['result'][:200]}...\n"
                        content_with_tools = content + tool_context
                        
                        logger.info("=" * 80)
                        logger.info(f"💾 SAVING TO MEMORY (with tool context):")
                        logger.info(f"  Session: {session_id}")
                        logger.info(f"  Actor: {actor_id}")
                        logger.info(f"  Role: {last_message['role']}")
                        logger.info(f"  Tools executed: {len(self.tool_results)}")
                        logger.info(f"  Content: {content[:300]}{'...' if len(content) > 300 else ''}")
                        logger.info(f"  Tool Context: {tool_context[:300]}...")
                        logger.info("=" * 80)
                        
                        self.memory_client.create_event(
                            memory_id=self.memory_id,
                            actor_id=actor_id,
                            session_id=session_id,
                            messages=[(content_with_tools, last_message["role"])]
                        )
                        
                        # Clear tool results after saving
                        self.tool_results = []
                    else:
                        logger.info("=" * 80)
                        logger.info(f"💾 SAVING TO MEMORY:")
                        logger.info(f"  Session: {session_id}")
                        logger.info(f"  Actor: {actor_id}")
                        logger.info(f"  Role: {last_message['role']}")
                        logger.info(f"  Content: {content[:500]}{'...' if len(content) > 500 else ''}")
                        logger.info("=" * 80)
                        
                        self.memory_client.create_event(
                            memory_id=self.memory_id,
                            actor_id=actor_id,
                            session_id=session_id,
                            messages=[(content, last_message["role"])]
                        )
                    
                    logger.info(f"✅ Message stored successfully to session: {session_id}")
                else:
                    logger.warning(f"⚠️  Empty message content, skipping storage")
                
        except Exception as e:
            logger.error(f"❌ Failed to store message: {e}", exc_info=True)
    
    def register_hooks(self, registry: HookRegistry) -> None:
        """Register hook callbacks."""
        registry.add_callback(AgentInitializedEvent, self.on_agent_initialized)
        registry.add_callback(MessageAddedEvent, self.on_message_added)
        registry.add_callback(AfterToolCallEvent, self.on_tool_executed)
        logger.info("🔗 Memory hooks registered successfully")
