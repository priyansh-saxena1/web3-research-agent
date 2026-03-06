# Langchain 0.3.27 Import Fixes - Complete Reference

**Last Updated:** After multiple iterations of import corrections  
**Status:** ✅ All critical imports validated for langchain 0.3.27

## Problem Summary

The web3-research-agent uses LangChain. Version 0.3.27 underwent major restructuring where:
1. Memory classes were moved to `langchain_classic` namespace
2. Tool base classes are in `langchain_core.tools`
3. LLM integrations remained in their respective packages

## Final Correct Imports (VERIFIED)

### 1. **Memory Imports** ✅
```python
# CORRECT (langchain_classic.memory):
from langchain_classic.memory import ConversationBufferWindowMemory

# WRONG (these don't exist in 0.3.27):
# ❌ from langchain.memory import ConversationBufferWindowMemory
# ❌ from langchain_community.memory import ConversationBufferWindowMemory
```

**Files Fixed:**
- `src/agent/memory_manager.py` (line 1)
- `src/agent/research_agent.py` (line 3)

### 2. **Tool Base Class** ✅
```python
# CORRECT (langchain_core.tools):
from langchain_core.tools import BaseTool

# WRONG:
# ❌ from langchain_community.tools import BaseTool
# ❌ from langchain.tools import BaseTool
```

**Files Using This:**
- `src/tools/base_tool.py` (line 3)
- `src/tools/chart_data_tool.py` (line 1)
- `src/tools/chart_creator_tool.py` (line 1)

### 3. **LLM Integrations** ✅ (Also Correct)
```python
# Google Generative AI (Gemini):
from langchain_google_genai import ChatGoogleGenerativeAI

# Ollama (Local):
from langchain_community.llms import Ollama
```

### 4. **Pydantic Models** ✅
```python
# All are correct Pydantic v2:
from pydantic import BaseModel, Field, PrivateAttr, field_validator
```

## All Langchain Imports in Codebase

| File | Import | Status |
|------|--------|--------|
| `src/agent/memory_manager.py` | `from langchain_classic.memory import ConversationBufferWindowMemory` | ✅ |
| `src/agent/research_agent.py` (L1) | `from langchain_google_genai import ChatGoogleGenerativeAI` | ✅ |
| `src/agent/research_agent.py` (L2) | `from langchain_community.llms import Ollama` | ✅ |
| `src/agent/research_agent.py` (L3) | `from langchain_classic.memory import ConversationBufferWindowMemory` | ✅ |
| `src/tools/base_tool.py` | `from langchain_core.tools import BaseTool` | ✅ |
| `src/tools/chart_data_tool.py` | `from langchain_core.tools import BaseTool` | ✅ |
| `src/tools/chart_creator_tool.py` | `from langchain_core.tools import BaseTool` | ✅ |
| `debug_gemini.py` | `from langchain_google_genai import ChatGoogleGenerativeAI` | ✅ |

## Requirements.txt Dependencies

**All packages confirmed in requirements.txt:**
```
langchain                    # Main package (includes langchain_classic)
langchain-google-genai      # Google Generative AI (Gemini)
langchain-community         # Community integrations (Ollama, etc.)
google-generativeai         # Google AI API
pydantic                    # Data validation
... (other dependencies)
```

## Why Langchain_classic?

In langchain 0.3.27:
- **Memory classes** moved to `langchain_classic` (backwards compatibility layer)
- These are marked `@deprecated(since="0.3.1", removal="1.0.0")`
- `langchain_classic` serves as a compatibility bridge
- Full migration would require replacing with `RunnableWithMessageHistory` (future work)

## Prevention Checklist

✅ No imports from non-existent modules  
✅ All `BaseTool` imports from `langchain_core.tools`  
✅ All memory imports from `langchain_classic.memory`  
✅ All LLM integrations from correct packages  
✅ No circular imports detected  
✅ Pydantic v2 syntax used consistently  

## Next Error Discovery Method

If new import errors occur:
1. Check error message for module path
2. Verify in [langchain GitHub](https://github.com/langchain-ai/langchain) - `libs/langchain/` folder
3. Look for `__init__.py` exports to find actual location
4. Never assume module is available under base `langchain` package - check `langchain_classic` or `langchain_core`

---
**Last Fix Commit:** `ac70217` - Fixed memory imports to use `langchain_classic`
