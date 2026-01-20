"""
Multi-provider LLM support for the UI/UX Research Agent.
Supports: Anthropic (Claude), OpenAI (GPT), Google (Gemini)
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def chat(self, messages: List[Dict], system: str, tools: List[Dict]) -> Dict[str, Any]:
        """
        Send a chat request to the LLM.

        Returns:
            Dict with keys:
                - 'content': List of content blocks (text and tool_use)
                - 'stop_reason': 'end_turn' or 'tool_use'
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model name being used."""
        pass


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        from anthropic import Anthropic
        self.client = Anthropic()
        self.model = model

    def chat(self, messages: List[Dict], system: str, tools: List[Dict]) -> Dict[str, Any]:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            tools=tools,
            messages=messages
        )
        return {
            'content': response.content,
            'stop_reason': response.stop_reason
        }

    def get_model_name(self) -> str:
        return f"Anthropic/{self.model}"


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    def __init__(self, model: str = "gpt-4o"):
        from openai import OpenAI
        self.client = OpenAI()
        self.model = model

    def _convert_tools_to_openai(self, tools: List[Dict]) -> List[Dict]:
        """Convert Anthropic tool format to OpenAI function format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            }
            for tool in tools
        ]

    def _convert_messages_to_openai(self, messages: List[Dict], system: str) -> List[Dict]:
        """Convert Anthropic message format to OpenAI format."""
        openai_messages = [{"role": "system", "content": system}]

        for msg in messages:
            if msg["role"] == "user":
                if isinstance(msg["content"], str):
                    openai_messages.append({"role": "user", "content": msg["content"]})
                elif isinstance(msg["content"], list):
                    # Tool results
                    for item in msg["content"]:
                        if item.get("type") == "tool_result":
                            openai_messages.append({
                                "role": "tool",
                                "tool_call_id": item["tool_use_id"],
                                "content": item["content"]
                            })
            elif msg["role"] == "assistant":
                if isinstance(msg["content"], list):
                    # Process assistant content with potential tool calls
                    text_content = ""
                    tool_calls = []

                    for block in msg["content"]:
                        if hasattr(block, 'text'):
                            text_content += block.text
                        elif hasattr(block, 'type') and block.type == "tool_use":
                            tool_calls.append({
                                "id": block.id,
                                "type": "function",
                                "function": {
                                    "name": block.name,
                                    "arguments": str(block.input) if not isinstance(block.input, str) else block.input
                                }
                            })

                    assistant_msg = {"role": "assistant", "content": text_content or None}
                    if tool_calls:
                        assistant_msg["tool_calls"] = tool_calls
                    openai_messages.append(assistant_msg)

        return openai_messages

    def chat(self, messages: List[Dict], system: str, tools: List[Dict]) -> Dict[str, Any]:
        import json

        openai_messages = self._convert_messages_to_openai(messages, system)
        openai_tools = self._convert_tools_to_openai(tools)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            tools=openai_tools,
            max_tokens=4096
        )

        message = response.choices[0].message
        content = []

        # Add text content if present
        if message.content:
            content.append(TextBlock(text=message.content))

        # Add tool calls if present
        if message.tool_calls:
            for tc in message.tool_calls:
                content.append(ToolUseBlock(
                    id=tc.id,
                    name=tc.function.name,
                    input=json.loads(tc.function.arguments)
                ))

        stop_reason = "tool_use" if message.tool_calls else "end_turn"

        return {
            'content': content,
            'stop_reason': stop_reason
        }

    def get_model_name(self) -> str:
        return f"OpenAI/{self.model}"


class GeminiProvider(LLMProvider):
    """Google Gemini provider."""

    def __init__(self, model: str = "gemini-2.0-flash"):
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
        self.model_name = model
        self.genai = genai

    def _convert_tools_to_gemini(self, tools: List[Dict]) -> List:
        """Convert Anthropic tool format to Gemini format."""
        function_declarations = []
        for tool in tools:
            function_declarations.append({
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"]
            })
        return function_declarations

    def chat(self, messages: List[Dict], system: str, tools: List[Dict]) -> Dict[str, Any]:
        from google.generativeai.types import content_types
        import json

        # Create model with system instruction
        model = self.genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system,
            tools=self._convert_tools_to_gemini(tools)
        )

        # Convert messages to Gemini format
        gemini_history = []
        for msg in messages:
            if msg["role"] == "user":
                if isinstance(msg["content"], str):
                    gemini_history.append({
                        "role": "user",
                        "parts": [msg["content"]]
                    })
                elif isinstance(msg["content"], list):
                    # Tool results
                    parts = []
                    for item in msg["content"]:
                        if item.get("type") == "tool_result":
                            parts.append(self.genai.protos.Part(
                                function_response=self.genai.protos.FunctionResponse(
                                    name=item.get("tool_name", "unknown"),
                                    response={"result": item["content"]}
                                )
                            ))
                    if parts:
                        gemini_history.append({"role": "user", "parts": parts})
            elif msg["role"] == "assistant":
                if isinstance(msg["content"], list):
                    parts = []
                    for block in msg["content"]:
                        if hasattr(block, 'text'):
                            parts.append(block.text)
                        elif hasattr(block, 'type') and block.type == "tool_use":
                            parts.append(self.genai.protos.Part(
                                function_call=self.genai.protos.FunctionCall(
                                    name=block.name,
                                    args=block.input
                                )
                            ))
                    if parts:
                        gemini_history.append({"role": "model", "parts": parts})

        # Start chat and get response
        chat = model.start_chat(history=gemini_history[:-1] if gemini_history else [])

        last_msg = gemini_history[-1]["parts"] if gemini_history else ["Hello"]
        response = chat.send_message(last_msg)

        # Parse response
        content = []
        has_function_calls = False

        for part in response.parts:
            if hasattr(part, 'text') and part.text:
                content.append(TextBlock(text=part.text))
            elif hasattr(part, 'function_call') and part.function_call:
                has_function_calls = True
                fc = part.function_call
                content.append(ToolUseBlock(
                    id=f"gemini_{fc.name}_{id(fc)}",
                    name=fc.name,
                    input=dict(fc.args)
                ))

        stop_reason = "tool_use" if has_function_calls else "end_turn"

        return {
            'content': content,
            'stop_reason': stop_reason
        }

    def get_model_name(self) -> str:
        return f"Google/{self.model_name}"


# Simple data classes to standardize content blocks across providers
class TextBlock:
    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class ToolUseBlock:
    def __init__(self, id: str, name: str, input: Dict):
        self.type = "tool_use"
        self.id = id
        self.name = name
        self.input = input


def get_provider(provider_name: str, model: Optional[str] = None) -> LLMProvider:
    """
    Factory function to get the appropriate provider.

    Args:
        provider_name: 'anthropic', 'openai', or 'gemini'
        model: Optional model override

    Returns:
        LLMProvider instance
    """
    providers = {
        'anthropic': (AnthropicProvider, "claude-sonnet-4-20250514"),
        'openai': (OpenAIProvider, "gpt-4o"),
        'gemini': (GeminiProvider, "gemini-2.0-flash"),
    }

    if provider_name not in providers:
        raise ValueError(f"Unknown provider: {provider_name}. Choose from: {list(providers.keys())}")

    provider_class, default_model = providers[provider_name]
    return provider_class(model=model or default_model)
