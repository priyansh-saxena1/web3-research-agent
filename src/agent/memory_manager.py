from langchain_community.memory import ConversationBufferWindowMemory
from typing import Dict, Any, List, Optional

class MemoryManager:
    """Enhanced conversation memory management"""
    
    def __init__(self, window_size: int = 10):
        self.memory = ConversationBufferWindowMemory(
            k=window_size,
            return_messages=True,
            memory_key="chat_history"
        )
        self.context_cache: Dict[str, Any] = {}
    
    def add_interaction(self, query: str, response: str, metadata: Optional[Dict[str, Any]] = None):
        """Add user interaction to memory with metadata"""
        self.memory.save_context(
            {"input": query},
            {"output": response}
        )
        
        if metadata:
            self.context_cache[query[:50]] = metadata
    
    def get_relevant_context(self, query: str) -> Dict[str, Any]:
        """Retrieve relevant context for current query"""
        return {
            "history": self.memory.load_memory_variables({}),
            "cached_context": self._find_similar_context(query)
        }
    
    def _find_similar_context(self, query: str) -> List[Dict[str, Any]]:
        """Find contextually similar previous interactions"""
        query_lower = query.lower()
        relevant = []
        
        for cached_key, context in self.context_cache.items():
            if any(word in cached_key.lower() for word in query_lower.split()[:3]):
                relevant.append(context)
        
        return relevant[:3]
    
    def clear_memory(self):
        """Clear conversation memory and cache"""
        self.memory.clear()
        self.context_cache.clear()
