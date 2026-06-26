"""
MarketMind AI Dashboard - Tool Registry
Registers all tools that AI agents can call via function-calling.
Supports OpenAI-compatible function-calling format for DeepSeek.
"""
from __future__ import annotations
import inspect
from typing import Callable, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)


def tool(
    name: Optional[str] = None,
    description: str = "",
    parameters: Optional[dict] = None,
):
    """
    Decorator to register a function as a tool that AI agents can call.
    
    Usage:
        @tool(name="search_news", description="Search for news articles")
        async def search_news(query: str, limit: int = 10) -> dict:
            ...
    """
    def decorator(func: Callable) -> Callable:
        # Infer parameter schema from function signature
        sig = inspect.signature(func)
        props = {}
        required = []
        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue
            param_type = "string"
            if param.annotation is int:
                param_type = "integer"
            elif param.annotation is float:
                param_type = "number"
            elif param.annotation is bool:
                param_type = "boolean"

            default = None
            if param.default is not inspect.Parameter.empty:
                default = param.default
            else:
                required.append(param_name)

            props[param_name] = {"type": param_type}
            if default is not None:
                props[param_name]["default"] = default
            if param_name == "query":
                props[param_name]["description"] = "Search query string"
            elif param_name == "limit":
                props[param_name]["description"] = "Maximum number of results"

        param_schema = {"type": "object", "properties": props}
        if required:
            param_schema["required"] = required

        func._tool_meta = {
            "name": name or func.__name__,
            "description": description or func.__doc__ or "",
            "parameters": parameters or param_schema,
        }
        func._is_tool = True
        return func
    return decorator


class ToolRegistry:
    """
    Registry for all tools available to AI agents.
    Tools are functions decorated with @tool that the LLM can choose to invoke.
    """

    def __init__(self):
        self._tools: dict[str, Callable] = {}
        self._schemas: list[dict] = []

    def register(self, func: Callable):
        """Register a tool function."""
        if not getattr(func, "_is_tool", False):
            raise ValueError(
                f"Function '{func.__name__}' is not decorated with @tool. "
                f"Use @tool(name=..., description=...) to register it."
            )
        meta = func._tool_meta
        self._tools[meta["name"]] = func
        # Build OpenAI-compatible function calling schema
        schema = {
            "type": "function",
            "function": {
                "name": meta["name"],
                "description": meta["description"],
                "parameters": meta["parameters"],
            },
        }
        self._schemas.append(schema)
        logger.info(f"Registered tool: {meta['name']}")

    def get_tool_schemas(self) -> list[dict]:
        """Return all tool schemas in OpenAI function-calling format."""
        return self._schemas

    def get_tool(self, name: str) -> Optional[Callable]:
        """Get a tool function by name."""
        return self._tools.get(name)

    async def execute_tool(self, name: str, arguments: dict) -> dict:
        """
        Execute a tool by name with arguments.
        Returns {"result": ..., "error": None} or {"result": None, "error": "..."}
        """
        func = self._tools.get(name)
        if not func:
            return {"result": None, "error": f"Tool '{name}' not found"}

        try:
            result = await func(**arguments)
            return {"result": result, "error": None}
        except Exception as e:
            logger.error(f"Tool '{name}' failed: {e}", exc_info=True)
            return {"result": None, "error": str(e)}

    async def execute_tool_with_trace(
        self,
        name: str,
        arguments: dict,
        trace_agent: Any = None,
    ) -> dict:
        """
        Execute a tool by name with arguments, recording a ToolCallTrace.
        Wraps execute_tool() with timing, success/error, and compact result preview.
        Appends ToolCallTrace to trace_agent when provided.

        Args:
            name: Tool name to execute
            arguments: Keyword arguments for the tool function
            trace_agent: Optional AgentTraceEntry to append ToolCallTrace to

        Returns:
            Same dict as execute_tool(): {"result": ..., "error": ...}
        """
        from datetime import datetime, timezone

        started_at = datetime.now(timezone.utc)
        result = await self.execute_tool(name, arguments)
        completed_at = datetime.now(timezone.utc)

        if trace_agent is not None:
            try:
                from .trace import ToolCallTrace

                duration_ms = (
                    (completed_at - started_at).total_seconds()
                ) * 1000
                success = result.get("error") is None
                err_msg = result.get("error")
                preview = ""
                result_data = result.get("result")
                if result_data is not None:
                    preview = str(result_data)[:200]

                tc = ToolCallTrace(
                    tool_name=name,
                    arguments=arguments,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_ms=duration_ms,
                    success=success,
                    error=err_msg,
                    compact_result_preview=preview,
                )
                trace_agent.tool_calls.append(tc)
            except Exception:
                # Never let tracing break the actual tool execution
                pass

        return result

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())

    def __len__(self):
        return len(self._tools)


# Global singleton
tool_registry = ToolRegistry()
