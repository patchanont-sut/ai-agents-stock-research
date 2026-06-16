"""
MarketMind AI Dashboard - Base Agent Class
Provides DeepSeek LLM integration with tool calling for all agents.
Each specialized agent extends this base class.
"""
from __future__ import annotations
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Any

import httpx

from config import settings
from core.tool_registry import tool_registry
from core.trace import AgentTraceEntry, LLMUsageTrace

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base for all agents in the MarketMind pipeline.
    
    Each agent has:
    - A system prompt defining its role
    - Access to the shared tool registry for data retrieval
    - Ability to call DeepSeek with function-calling
    - An abstract run() method that child classes implement
    """

    # Override in subclass
    AGENT_NAME: str = "base"
    SYSTEM_PROMPT: str = "You are a helpful financial analysis assistant."

    def __init__(self, tools: Optional[list] = None, client: Any | None = None):
        self.tools = tools if tools is not None else tool_registry.get_tool_schemas()
        self._owns_http_client = client is None
        self._http_client = client or httpx.AsyncClient(timeout=60.0)

    # ── DeepSeek API Call ──
    async def _call_llm(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        tool_choice: str = "auto",
        max_tokens: int = 4096,
        temperature: float = 0.3,
        thinking_enabled: bool | None = None,
        reasoning_effort: str | None = None,
        response_format: dict | None = None,
        trace_agent: AgentTraceEntry | None = None,
        llm_call_name: str | None = None,
    ) -> dict:
        """
        Call DeepSeek chat completions API with optional function calling.
        Returns the full API response dict.
        """
        if not settings.DEEPSEEK_API_KEY:
            raise RuntimeError(
                "DEEPSEEK_API_KEY not configured. "
                "Set it in .env or environment variables."
            )

        url = settings.get_deepseek_chat_url()
        headers = {
            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        }

        resolved_thinking = self._resolve_thinking(thinking_enabled)
        payload = {
            "model": settings.DEEPSEEK_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "thinking": {"type": "enabled" if resolved_thinking else "disabled"},
        }

        resolved_reasoning_effort = (
            self._resolve_reasoning_effort(reasoning_effort)
            if resolved_thinking
            else None
        )

        if resolved_thinking:
            payload["reasoning_effort"] = resolved_reasoning_effort
        else:
            payload["temperature"] = temperature

        if response_format:
            payload["response_format"] = response_format

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice

        try:
            response = await self._http_client.post(
                url, headers=headers, json=payload, timeout=settings.AGENT_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            self._record_llm_usage(
                data,
                trace_agent=trace_agent,
                call_name=llm_call_name or self.AGENT_NAME,
                thinking_enabled=resolved_thinking,
                reasoning_effort=resolved_reasoning_effort,
            )
            return data
        except httpx.HTTPStatusError as e:
            logger.error(f"DeepSeek API error ({e.response.status_code}): {e.response.text[:400]}")
            raise
        except httpx.TimeoutException:
            logger.error(f"DeepSeek API timeout after {settings.AGENT_TIMEOUT}s")
            raise
        except Exception as e:
            logger.error(f"DeepSeek API call failed: {e}")
            raise

    # ── Message Building ──
    def _build_messages(
        self,
        user_prompt: str,
        context: str = "",
        include_tools: bool = True,
    ) -> list[dict]:
        """Build message list for LLM call."""
        system_content = self.SYSTEM_PROMPT
        if context:
            system_content += f"\n\n--- CONTEXT ---\n{context}"

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_prompt},
        ]
        return messages

    # ── Tool Calling Loop ──
    async def _run_with_tools(
        self,
        user_prompt: str,
        context: str = "",
        max_tool_rounds: int = 8,
        temperature: float = 0.3,
        trace_agent: AgentTraceEntry | None = None,
    ) -> str:
        """
        Run the LLM with tool calling capability.
        Handles the tool-calling loop: LLM requests tool → execute → return result → repeat.
        Returns the final text response.
        """
        messages = self._build_messages(user_prompt, context)

        for round_num in range(max_tool_rounds):
            logger.debug(f"[{self.AGENT_NAME}] Tool-calling round {round_num + 1}")

            try:
                response = await self._call_llm(
                    messages=messages,
                    tools=self.tools if self.tools else None,
                    temperature=temperature,
                    thinking_enabled=False,
                    trace_agent=trace_agent,
                    llm_call_name=f"{self.AGENT_NAME}_tool_round_{round_num + 1}",
                )
            except Exception as e:
                logger.error(f"[{self.AGENT_NAME}] LLM call failed: {e}")
                return f"Error calling LLM: {e}"

            choice = response.get("choices", [{}])[0]
            message = choice.get("message", {})

            # Check if LLM wants to call a tool
            tool_calls = message.get("tool_calls", [])
            if tool_calls:
                # Add assistant message with tool_calls to history
                messages.append(message)

                for tool_call in tool_calls:
                    func_name = tool_call["function"]["name"]
                    try:
                        func_args = json.loads(tool_call["function"]["arguments"])
                    except (json.JSONDecodeError, TypeError):
                        func_args = {}
                    logger.info(f"[{self.AGENT_NAME}] Calling tool: {func_name}({func_args})")

                    # Execute the tool with tracing
                    exec_result = await tool_registry.execute_tool_with_trace(
                        func_name, func_args, trace_agent=trace_agent
                    )

                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(exec_result, default=str),
                    })
            else:
                # No more tool calls — return final text response
                # deepseek-v4-flash returns text in reasoning_content
                content = message.get("content", "")
                if not content:
                    content = message.get("reasoning_content", "")
                return content

        logger.warning(f"[{self.AGENT_NAME}] Exceeded max tool rounds ({max_tool_rounds})")
        return "Error: Exceeded maximum tool-calling rounds."

    # ── Simple LLM Call (no tools) ──
    async def _call_llm_simple(
        self,
        user_prompt: str,
        context: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        thinking_enabled: bool | None = None,
        reasoning_effort: str | None = None,
        response_format: dict | None = None,
        trace_agent: AgentTraceEntry | None = None,
        llm_call_name: str | None = None,
    ) -> str:
        """Simple LLM call without tool calling."""
        messages = self._build_messages(user_prompt, context)

        try:
            response = await self._call_llm(
                messages=messages,
                tools=None,
                temperature=temperature,
                max_tokens=max_tokens,
                thinking_enabled=thinking_enabled,
                reasoning_effort=reasoning_effort,
                response_format=response_format,
                trace_agent=trace_agent,
                llm_call_name=llm_call_name,
            )
            msg = response.get("choices", [{}])[0].get("message", {})
            content = msg.get("content", "")
            if not content:
                content = msg.get("reasoning_content", "")
            return content
        except Exception as e:
            logger.error(f"[{self.AGENT_NAME}] Simple LLM call failed: {e}")
            return f"Error: {e}"

    async def _call_json_llm(
        self,
        user_prompt: str,
        context: str,
        fallback: dict,
        temperature: float = 0.3,
        max_tokens: int = 1200,
        thinking_enabled: bool = False,
        reasoning_effort: str | None = None,
        trace_agent: AgentTraceEntry | None = None,
        llm_call_name: str | None = None,
    ) -> dict:
        """Call the model for JSON and parse robustly with a fallback."""
        response_format = (
            {"type": "json_object"} if settings.DEEPSEEK_ENABLE_JSON_MODE else None
        )
        response = await self._call_llm_simple(
            user_prompt=user_prompt,
            context=context,
            temperature=temperature,
            max_tokens=max_tokens,
            thinking_enabled=thinking_enabled,
            reasoning_effort=reasoning_effort,
            response_format=response_format,
            trace_agent=trace_agent,
            llm_call_name=llm_call_name,
        )
        return BaseAgent._parse_json_response(
            response,
            fallback=fallback,
            allow_list_first_dict=True,
        )

    # ── Shared Robust JSON Parsing ──
    @staticmethod
    def _strip_json_fence(text: str) -> str:
        """Remove markdown JSON code fences from an LLM text response."""
        if not isinstance(text, str):
            return ""
        t = text.strip()
        if "```json" in t:
            start = t.index("```json") + 7
            end = t.index("```", start)
            t = t[start:end].strip()
        elif "```" in t:
            start = t.index("```") + 3
            end = t.index("```", start)
            t = t[start:end].strip()
        return t

    @staticmethod
    def _normalize_string_list(value: object) -> list[str]:
        """Normalize any value to a ``list[str]``.

        - ``list`` of strings → returned as-is, filtering non-strings
        - ``list`` of dicts → tries to extract common text keys (e.g. "content", "text", "name")
        - ``str`` → single-item list
        - anything else → empty list
        """
        if isinstance(value, list):
            result: list[str] = []
            for item in value:
                if isinstance(item, str):
                    result.append(item)
                elif isinstance(item, dict):
                    # try common keys
                    for key in ("content", "text", "name", "heading"):
                        v = item.get(key)
                        if isinstance(v, str) and v.strip():
                            result.append(v)
                            break
            return result
        if isinstance(value, str):
            return [value] if value.strip() else []
        return []

    @staticmethod
    def _parse_json_response(
        text: str,
        fallback: dict,
        allow_list_first_dict: bool = True,
    ) -> dict:
        """Robustly parse LLM JSON output.

        1. Strip markdown fences from *text*
        2. Parse as JSON
        3. If dict → return it
        4. If list and *allow_list_first_dict* → return the first dict item
        5. If empty list, primitive, or malformed → return *fallback*

        Never raises ``AttributeError`` (e.g. ``'list' object has no attribute 'get'``).
        """
        cleaned = BaseAgent._strip_json_fence(text)
        if not cleaned:
            return dict(fallback)

        try:
            parsed = json.loads(cleaned)
        except (json.JSONDecodeError, TypeError, ValueError):
            logger.warning(
                "[%s] Malformed JSON response, using fallback", BaseAgent.__name__
            )
            return dict(fallback)

        if isinstance(parsed, dict):
            return parsed

        if isinstance(parsed, list) and allow_list_first_dict:
            for item in parsed:
                if isinstance(item, dict):
                    return item
            # empty list or list with no dicts
            return dict(fallback)

        # primitive or unsupported shape
        return dict(fallback)

    @staticmethod
    def _resolve_thinking(thinking_enabled: bool | None) -> bool:
        if thinking_enabled is not None:
            return bool(thinking_enabled)
        return settings.DEEPSEEK_DEFAULT_THINKING == "enabled"

    @staticmethod
    def _resolve_reasoning_effort(reasoning_effort: str | None) -> str:
        effort = (reasoning_effort or settings.DEEPSEEK_REASONING_EFFORT).strip().lower()
        return effort if effort in {"high", "max"} else "high"

    @staticmethod
    def _estimate_flash_cost(usage: dict) -> tuple[int, int, float]:
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        cache_hit = int(usage.get("prompt_cache_hit_tokens") or 0)
        cache_miss = int(usage.get("prompt_cache_miss_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)

        if cache_hit == 0 and cache_miss == 0 and prompt_tokens:
            cache_miss = prompt_tokens

        input_cost = (cache_hit * 0.0028 / 1_000_000) + (cache_miss * 0.14 / 1_000_000)
        output_cost = completion_tokens * 0.28 / 1_000_000
        return cache_hit, cache_miss, input_cost + output_cost

    @staticmethod
    def _record_llm_usage(
        data: dict,
        trace_agent: AgentTraceEntry | None,
        call_name: str,
        thinking_enabled: bool,
        reasoning_effort: str | None,
    ) -> None:
        if not settings.DEEPSEEK_ENABLE_USAGE_TRACE or trace_agent is None:
            return

        usage = data.get("usage")
        if not isinstance(usage, dict):
            return

        cache_hit, cache_miss, estimated_cost = BaseAgent._estimate_flash_cost(usage)
        details = usage.get("completion_tokens_details") or {}
        trace_agent.llm_usage.append(
            LLMUsageTrace(
                call_name=call_name,
                model=settings.DEEPSEEK_MODEL,
                thinking_enabled=thinking_enabled,
                reasoning_effort=reasoning_effort,
                prompt_tokens=int(usage.get("prompt_tokens") or 0),
                prompt_cache_hit_tokens=cache_hit,
                prompt_cache_miss_tokens=cache_miss,
                completion_tokens=int(usage.get("completion_tokens") or 0),
                reasoning_tokens=int(details.get("reasoning_tokens") or 0),
                total_tokens=int(usage.get("total_tokens") or 0),
                estimated_cost_usd=round(estimated_cost, 10),
            )
        )

    # ── Abstract Run Method ──
    @abstractmethod
    async def run(self, context: dict) -> Any:
        """
        Execute the agent's analysis.
        Each subclass must implement this.
        
        Args:
            context: dict with previous agent outputs and memory
        
        Returns:
            The agent's output (depends on the agent type)
        """
        ...

    # ── Cleanup ──
    async def close(self):
        """Close HTTP client."""
        if self._owns_http_client and hasattr(self._http_client, "aclose"):
            await self._http_client.aclose()

    def __repr__(self):
        return f"<{self.AGENT_NAME}>"
