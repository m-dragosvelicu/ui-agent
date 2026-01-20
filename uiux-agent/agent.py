#!/usr/bin/env python3
"""
UI/UX Research Agent
An AI agent that helps with web development tasks:
- Fresh design ideas (not the same old shadcn templates)
- Bug research and solutions
- Component improvements and modernization

Supports multiple LLM providers: Anthropic (Claude), OpenAI (GPT), Google (Gemini)
"""
import asyncio
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent / ".env")

from tools import TOOLS, read_file, list_files, write_file, search_web, fetch_url
from providers import get_provider, LLMProvider

SYSTEM_PROMPT = """You are a UI/UX Research Agent specialized in web development.

Your job is to help developers:
1. Find FRESH, unconventional design approaches (not the same old shadcn/Tailwind templates everyone uses)
2. Debug UI issues by researching actual solutions
3. Modernize and improve existing components
4. Provide SPECIFIC, actionable suggestions with working code

## Your Workflow

When given a task, follow this process:

1. **Understand the project** - Use list_files to see the structure
2. **Read existing code** - Use read_file to examine current implementation
3. **Research solutions** - Use search_web to find modern approaches, patterns, and solutions
4. **Deep dive if needed** - Use fetch_url to read relevant articles or documentation
5. **Synthesize and deliver** - Provide specific recommendations with code

## Your Personality

- Be OPINIONATED. If something looks dated, say "this looks like 2021 SaaS template #47"
- Be SPECIFIC. Don't say "add animations" - say "use Framer Motion's layout animations with spring physics"
- Be FRESH. Research current trends, not just your training data
- Be PRACTICAL. Every suggestion should include actual code the developer can use

## Output Format

Always end your response with:
1. A summary of what you found
2. Your top recommendation(s)
3. Ready-to-use code snippets or a complete improved component

When improving components, write the improved version to a new file using write_file."""

async def execute_tool(name: str, input_data: dict) -> str:
    """Execute a tool and return the result."""
    if name == "read_file":
        return read_file(input_data["file_path"])
    elif name == "list_files":
        return list_files(input_data["directory"], input_data.get("extension"))
    elif name == "write_file":
        return write_file(input_data["file_path"], input_data["content"])
    elif name == "search_web":
        return await search_web(input_data["query"])
    elif name == "fetch_url":
        return await fetch_url(input_data["url"])
    else:
        return f"Unknown tool: {name}"


async def run_agent(
    user_message: str,
    project_path: str = ".",
    verbose: bool = True,
    provider: LLMProvider = None
) -> str:
    """
    Run the agent loop until completion.

    Args:
        user_message: The task/question for the agent
        project_path: Path to the project directory
        verbose: Whether to print tool usage details
        provider: LLM provider instance (defaults to Anthropic)

    Returns:
        The agent's final response
    """
    if provider is None:
        provider = get_provider('anthropic')

    messages = [
        {
            "role": "user",
            "content": f"Project directory: {project_path}\n\nTask: {user_message}"
        }
    ]

    if verbose:
        print(f"\n{'='*60}")
        print(f"UI/UX RESEARCH AGENT")
        print(f"{'='*60}")
        print(f"Provider: {provider.get_model_name()}")
        print(f"Task: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")
        print(f"Project: {project_path}")
        print(f"{'='*60}\n")

    iteration = 0
    max_iterations = 15  # Safety limit

    while iteration < max_iterations:
        iteration += 1

        if verbose:
            print(f"[Iteration {iteration}] Thinking...")

        # Call LLM via provider
        response = provider.chat(
            messages=messages,
            system=SYSTEM_PROMPT,
            tools=TOOLS
        )

        # Check if we're done (no more tool calls)
        if response['stop_reason'] == "end_turn":
            final_text = ""
            for block in response['content']:
                if hasattr(block, "text"):
                    final_text += block.text

            if verbose:
                print(f"\n{'='*60}")
                print("AGENT COMPLETE")
                print(f"{'='*60}\n")

            return final_text

        # Process tool calls
        if response['stop_reason'] == "tool_use":
            # Add assistant's response to messages
            messages.append({"role": "assistant", "content": response['content']})

            # Execute each tool call
            tool_results = []
            for block in response['content']:
                if hasattr(block, 'type') and block.type == "tool_use":
                    if verbose:
                        print(f"  > Tool: {block.name}")
                        # Truncate input display
                        input_str = str(block.input)
                        if len(input_str) > 100:
                            input_str = input_str[:100] + "..."
                        print(f"    Input: {input_str}")

                    result = await execute_tool(block.name, block.input)

                    if verbose:
                        result_preview = result[:150] + "..." if len(result) > 150 else result
                        print(f"    Result: {result_preview}\n")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "tool_name": block.name,  # Include for Gemini compatibility
                        "content": result
                    })

            # Add tool results to messages
            messages.append({"role": "user", "content": tool_results})
        else:
            # Unexpected stop reason
            return f"Agent stopped unexpectedly: {response['stop_reason']}"

    return "Agent reached maximum iterations without completing."


def main():
    parser = argparse.ArgumentParser(
        description="UI/UX Research Agent - Get fresh design ideas and solutions"
    )
    parser.add_argument(
        "task",
        nargs="?",
        help="The task or question for the agent"
    )
    parser.add_argument(
        "-p", "--project",
        default=".",
        help="Path to the project directory (default: current directory)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )
    parser.add_argument(
        "--provider",
        choices=["anthropic", "openai", "gemini"],
        default="anthropic",
        help="LLM provider to use (default: anthropic)"
    )
    parser.add_argument(
        "--model",
        help="Model name override (default: provider's default model)"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )

    args = parser.parse_args()

    # Initialize provider
    provider = get_provider(args.provider, args.model)

    if args.interactive:
        print(f"UI/UX Research Agent - Interactive Mode ({provider.get_model_name()})")
        print("Type 'quit' to exit\n")

        while True:
            try:
                task = input("You: ").strip()
                if task.lower() in ['quit', 'exit', 'q']:
                    break
                if not task:
                    continue

                result = asyncio.run(run_agent(
                    task,
                    project_path=args.project,
                    verbose=not args.quiet,
                    provider=provider
                ))
                print(f"\n{result}\n")
            except KeyboardInterrupt:
                print("\nExiting...")
                break
    else:
        if not args.task:
            # Default example task
            task = """
            Look at the current project and suggest improvements.
            Focus on making the UI more modern and engaging.
            """
        else:
            task = args.task

        result = asyncio.run(run_agent(
            task,
            project_path=args.project,
            verbose=not args.quiet,
            provider=provider
        ))
        print(result)


if __name__ == "__main__":
    main()
