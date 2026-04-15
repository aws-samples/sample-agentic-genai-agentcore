"""
LangGraph Hooks for Memory and Observability

This module provides hook implementations for LangGraph workflows,
similar to Strands hooks but adapted for LangGraph's architecture.
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage

logger = logging.getLogger(__name__)


class WorkflowHook:
    """Base class for LangGraph workflow hooks"""
    
    def on_workflow_start(self, state: Dict[str, Any]) -> None:
        """Called when workflow starts"""
        pass
    
    def on_workflow_end(self, state: Dict[str, Any]) -> None:
        """Called when workflow ends"""
        pass
    
    def on_node_start(self, node_name: str, state: Dict[str, Any]) -> None:
        """Called before a node executes"""
        pass
    
    def on_node_end(self, node_name: str, state: Dict[str, Any]) -> None:
        """Called after a node executes"""
        pass
    
    def on_error(self, error: Exception, state: Dict[str, Any]) -> None:
        """Called when an error occurs"""
        pass


class LoggingHook(WorkflowHook):
    """Hook for detailed workflow logging"""
    
    def __init__(self, session_id: str, actor_id: str = "system"):
        self.session_id = session_id
        self.actor_id = actor_id
        self.start_time = None
    
    def on_workflow_start(self, state: Dict[str, Any]) -> None:
        self.start_time = datetime.now()
        logger.info(f"[{self.session_id}] Workflow started by {self.actor_id}")
        logger.info(f"[{self.session_id}] Campaign ID: {state.get('campaign_id')}")
    
    def on_workflow_end(self, state: Dict[str, Any]) -> None:
        duration = (datetime.now() - self.start_time).total_seconds()
        logger.info(f"[{self.session_id}] Workflow completed in {duration:.2f}s")
        logger.info(f"[{self.session_id}] Final state keys: {list(state.keys())}")
    
    def on_node_start(self, node_name: str, state: Dict[str, Any]) -> None:
        logger.info(f"[{self.session_id}] Node '{node_name}' starting")
    
    def on_node_end(self, node_name: str, state: Dict[str, Any]) -> None:
        logger.info(f"[{self.session_id}] Node '{node_name}' completed")
        if state.get("error"):
            logger.error(f"[{self.session_id}] Node '{node_name}' error: {state['error']}")
    
    def on_error(self, error: Exception, state: Dict[str, Any]) -> None:
        logger.error(f"[{self.session_id}] Workflow error: {str(error)}", exc_info=True)


class MemoryHook(WorkflowHook):
    """
    Hook for AgentCore Memory integration with LangGraph
    
    This hook stores workflow context and results in AWS Bedrock AgentCore Memory
    for cross-session learning and context retrieval.
    """
    
    def __init__(self, memory_client, memory_id: str, session_id: str):
        """
        Initialize memory hook
        
        Args:
            memory_client: AWS Bedrock AgentCore Memory client
            memory_id: Unique identifier for the memory store
            session_id: Current session identifier
        """
        self.memory_client = memory_client
        self.memory_id = memory_id
        self.session_id = session_id
        self.workflow_context = []
    
    def on_workflow_start(self, state: Dict[str, Any]) -> None:
        """Store initial workflow context in memory"""
        try:
            # Retrieve relevant past context
            campaign_content = state.get("campaign_content", "")
            if campaign_content:
                # Query memory for similar past campaigns
                past_context = self.memory_client.retrieve(
                    memory_id=self.memory_id,
                    query=campaign_content[:500],  # First 500 chars for context
                    max_results=3
                )
                
                if past_context:
                    logger.info(f"[{self.session_id}] Retrieved {len(past_context)} past contexts from memory")
                    # Add past context to state messages
                    context_msg = f"Relevant past campaign insights:\n{past_context}"
                    state.setdefault("messages", []).insert(0, 
                        AIMessage(content=context_msg)
                    )
        except Exception as e:
            logger.warning(f"[{self.session_id}] Failed to retrieve memory context: {e}")
    
    def on_node_end(self, node_name: str, state: Dict[str, Any]) -> None:
        """Store node results in short-term memory"""
        try:
            # Track workflow progress
            self.workflow_context.append({
                "node": node_name,
                "timestamp": datetime.now().isoformat(),
                "campaign_id": state.get("campaign_id"),
                "has_error": bool(state.get("error"))
            })
        except Exception as e:
            logger.warning(f"[{self.session_id}] Failed to track node context: {e}")
    
    def on_workflow_end(self, state: Dict[str, Any]) -> None:
        """Store final workflow results in long-term memory"""
        try:
            # Only store successful completions
            if not state.get("error") and state.get("final_report"):
                memory_content = {
                    "session_id": self.session_id,
                    "campaign_id": state.get("campaign_id"),
                    "franchise": state.get("franchise"),
                    "timestamp": datetime.now().isoformat(),
                    "workflow_path": [ctx["node"] for ctx in self.workflow_context],
                    "summary": state.get("final_report", "")[:1000],  # First 1000 chars
                    "persona_insights": state.get("persona_review", "")[:500],
                    "compliance_notes": state.get("validation_report", "")[:500]
                }
                
                # Store in memory for future retrieval
                self.memory_client.store(
                    memory_id=self.memory_id,
                    content=str(memory_content),
                    metadata={
                        "session_id": self.session_id,
                        "campaign_id": state.get("campaign_id"),
                        "franchise": state.get("franchise"),
                        "type": "campaign_review"
                    }
                )
                
                logger.info(f"[{self.session_id}] Stored workflow results in memory")
        except Exception as e:
            logger.warning(f"[{self.session_id}] Failed to store memory: {e}")
    
    def on_error(self, error: Exception, state: Dict[str, Any]) -> None:
        """Store error context in memory for learning"""
        try:
            error_content = {
                "session_id": self.session_id,
                "campaign_id": state.get("campaign_id"),
                "timestamp": datetime.now().isoformat(),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "workflow_path": [ctx["node"] for ctx in self.workflow_context]
            }
            
            self.memory_client.store(
                memory_id=self.memory_id,
                content=str(error_content),
                metadata={
                    "session_id": self.session_id,
                    "type": "error",
                    "error_type": type(error).__name__
                }
            )
            
            logger.info(f"[{self.session_id}] Stored error context in memory")
        except Exception as e:
            logger.warning(f"[{self.session_id}] Failed to store error in memory: {e}")


class MetricsHook(WorkflowHook):
    """Hook for collecting workflow metrics"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.metrics = {
            "start_time": None,
            "end_time": None,
            "node_durations": {},
            "node_start_times": {}
        }
    
    def on_workflow_start(self, state: Dict[str, Any]) -> None:
        self.metrics["start_time"] = datetime.now()
    
    def on_workflow_end(self, state: Dict[str, Any]) -> None:
        self.metrics["end_time"] = datetime.now()
        duration = (self.metrics["end_time"] - self.metrics["start_time"]).total_seconds()
        
        logger.info(f"[{self.session_id}] Workflow Metrics:")
        logger.info(f"  Total Duration: {duration:.2f}s")
        for node, node_duration in self.metrics["node_durations"].items():
            logger.info(f"  {node}: {node_duration:.2f}s")
    
    def on_node_start(self, node_name: str, state: Dict[str, Any]) -> None:
        self.metrics["node_start_times"][node_name] = datetime.now()
    
    def on_node_end(self, node_name: str, state: Dict[str, Any]) -> None:
        if node_name in self.metrics["node_start_times"]:
            start_time = self.metrics["node_start_times"][node_name]
            duration = (datetime.now() - start_time).total_seconds()
            self.metrics["node_durations"][node_name] = duration


class HookManager:
    """Manages multiple hooks for a workflow"""
    
    def __init__(self):
        self.hooks = []
    
    def add_hook(self, hook: WorkflowHook) -> None:
        """Add a hook to the manager"""
        self.hooks.append(hook)
    
    def on_workflow_start(self, state: Dict[str, Any]) -> None:
        for hook in self.hooks:
            try:
                hook.on_workflow_start(state)
            except Exception as e:
                logger.error(f"Hook {hook.__class__.__name__} failed on_workflow_start: {e}")
    
    def on_workflow_end(self, state: Dict[str, Any]) -> None:
        for hook in self.hooks:
            try:
                hook.on_workflow_end(state)
            except Exception as e:
                logger.error(f"Hook {hook.__class__.__name__} failed on_workflow_end: {e}")
    
    def on_node_start(self, node_name: str, state: Dict[str, Any]) -> None:
        for hook in self.hooks:
            try:
                hook.on_node_start(node_name, state)
            except Exception as e:
                logger.error(f"Hook {hook.__class__.__name__} failed on_node_start: {e}")
    
    def on_node_end(self, node_name: str, state: Dict[str, Any]) -> None:
        for hook in self.hooks:
            try:
                hook.on_node_end(node_name, state)
            except Exception as e:
                logger.error(f"Hook {hook.__class__.__name__} failed on_node_end: {e}")
    
    def on_error(self, error: Exception, state: Dict[str, Any]) -> None:
        for hook in self.hooks:
            try:
                hook.on_error(error, state)
            except Exception as e:
                logger.error(f"Hook {hook.__class__.__name__} failed on_error: {e}")


def create_hooked_node(node_func, node_name: str, hook_manager: HookManager):
    """
    Wrap a node function with hook calls
    
    Args:
        node_func: The original node function
        node_name: Name of the node
        hook_manager: HookManager instance
    
    Returns:
        Wrapped node function with hooks
    """
    def wrapped_node(state: Dict[str, Any]) -> Dict[str, Any]:
        hook_manager.on_node_start(node_name, state)
        try:
            result = node_func(state)
            hook_manager.on_node_end(node_name, result)
            return result
        except Exception as e:
            hook_manager.on_error(e, state)
            raise
    
    return wrapped_node
