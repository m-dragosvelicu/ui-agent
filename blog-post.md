# Building a UI/UX Research Agent: Stop Settling for Stale Components

*A practical guide to building an AI agent that does the design research while you focus on building*

---

## The Problem (A Rant You'll Relate To)

If you've been doing web development for any amount of time, you know the cycle: you need a landing page, you reach for shadcn, you get something that looks like every other SaaS landing page from 2023. Or worse—you're stuck on a bug, you've been copy-pasting between ChatGPT and your codebase for an hour, and you're one "I don't have access to your codebase" away from throwing your laptop.

I've been there. The naive workflow looks like this:
1. Complain to ChatGPT about what's broken
2. Ask it what info it needs
3. Switch to Claude Code, tell it "DON'T MAKE ANY EDITS" and extract the relevant code
4. Paste everything back into ChatGPT's agent mode
5. Repeat until sanity depletes

The problem? Too much context-switching. Too many iterations. And if you start insulting the AI models, that's your sign to take a break.

**What if we could externalize this entire process?** An agent that takes your complaint, digs through your codebase, researches solutions, and comes back with actual fresh ideas—not the same recycled Tailwind templates.

That's what we're building today.

---

## The Use Cases

### Use Case 1: "I'm Stuck on Design"
You want to improve a landing page but you're out of ideas. Or you have a vision, but every AI suggestion is the same hero-section-with-gradient nonsense. The agent should:
- Understand your current design
- Research fresh, unconventional approaches
- Suggest specific implementations that aren't just "add a CTA button"

### Use Case 2: "This Bug Makes No Sense"
You've got a bug you can't crack. The agent should:
- Extract relevant code segments automatically
- Research similar issues and solutions
- Come back with targeted fixes, not generic advice

### Use Case 3: "This Component Needs a Glow-Up"
You have an existing component that works but feels dated or clunky. Maybe it's a card, a modal, or a data table. The agent should:
- Analyze your current implementation
- Research modern patterns for that component type
- Suggest specific improvements (accessibility, animations, UX patterns)
- Provide updated code that you can drop in

---

## The Architecture

We're building a **tool-using agent** with three core capabilities:

```
┌─────────────────────────────────────────────────────┐
│                   UI/UX Research Agent              │
├─────────────────────────────────────────────────────┤
│  Tools:                                             │
│  ├── read_file: Extract code from your project      │
│  ├── search_web: Research design trends & solutions │
│  ├── analyze_ui: Break down what's wrong/missing    │
│  └── generate_suggestions: Fresh, specific ideas    │
│                                                     │
│  Loop: Think → Act → Observe → Repeat               │
└─────────────────────────────────────────────────────┘
```

The key insight: **the agent decides which tools to use and when**. You give it a problem, it figures out the research path.

---

## Step-by-Step: Building the Agent

### Prerequisites
- Python 3.10+
- An Anthropic API key (Claude)
- Basic understanding of async Python

### Step 1: Project Setup

```bash
mkdir uiux-agent && cd uiux-agent
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install anthropic httpx beautifulsoup4
```

### Step 2: Define the Tools

Create `tools.py`:

```python
import os
import httpx
from bs4 import BeautifulSoup
from pathlib import Path

def read_file(file_path: str) -> str:
    """Read a file from the project directory."""
    try:
        path = Path(file_path)
        if not path.exists():
            return f"Error: File {file_path} not found"
        return path.read_text()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def list_files(directory: str, extension: str = None) -> str:
    """List files in a directory, optionally filtered by extension."""
    try:
        path = Path(directory)
        if not path.exists():
            return f"Error: Directory {directory} not found"

        files = []
        for f in path.rglob("*"):
            if f.is_file():
                if extension is None or f.suffix == extension:
                    files.append(str(f.relative_to(path)))

        return "\n".join(files[:50])  # Limit to 50 files
    except Exception as e:
        return f"Error listing files: {str(e)}"

async def search_web(query: str) -> str:
    """Search the web for design inspiration and solutions."""
    # Using a simple approach - in production you'd use a proper search API
    async with httpx.AsyncClient() as client:
        try:
            # Search for the query (simplified - use proper search API in production)
            response = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10.0
            )
            soup = BeautifulSoup(response.text, "html.parser")
            results = []
            for result in soup.select(".result__title")[:5]:
                title = result.get_text(strip=True)
                link = result.find("a")
                if link and title:
                    results.append(f"- {title}")

            return "\n".join(results) if results else "No results found"
        except Exception as e:
            return f"Search error: {str(e)}"

# Tool definitions for Claude
TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file from the project. Use this to examine existing code, components, or styles.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "list_files",
        "description": "List files in a directory. Use this to understand project structure before reading specific files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Directory path to list"
                },
                "extension": {
                    "type": "string",
                    "description": "Optional file extension filter (e.g., '.tsx', '.css')"
                }
            },
            "required": ["directory"]
        }
    },
    {
        "name": "search_web",
        "description": "Search the web for design inspiration, UI patterns, or bug solutions. Use specific queries like 'modern hero section animations 2024' or 'react hydration mismatch fix'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                }
            },
            "required": ["query"]
        }
    }
]
```

### Step 3: The Agent Loop

Create `agent.py`:

```python
import asyncio
import anthropic
from tools import TOOLS, read_file, list_files, search_web

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a UI/UX Research Agent specialized in web development.

Your job is to help developers:
1. Find fresh, unconventional design approaches (not the same old shadcn/Tailwind templates)
2. Debug UI issues by researching solutions
3. Provide SPECIFIC, actionable suggestions with code examples

When given a task:
1. First, understand the project structure (list_files)
2. Read relevant existing code (read_file)
3. Research modern approaches and solutions (search_web)
4. Synthesize findings into actionable recommendations

Be opinionated. If something looks dated, say so. Suggest specific libraries,
techniques, or approaches that are genuinely fresh—not just "add a gradient".

Always provide code examples in your final response."""

async def execute_tool(name: str, input_data: dict) -> str:
    """Execute a tool and return the result."""
    if name == "read_file":
        return read_file(input_data["file_path"])
    elif name == "list_files":
        return list_files(input_data["directory"], input_data.get("extension"))
    elif name == "search_web":
        return await search_web(input_data["query"])
    else:
        return f"Unknown tool: {name}"

async def run_agent(user_message: str, project_path: str = ".") -> str:
    """Run the agent loop until completion."""

    messages = [
        {"role": "user", "content": f"Project directory: {project_path}\n\nTask: {user_message}"}
    ]

    print(f"\n{'='*60}")
    print(f"Starting agent with task: {user_message[:100]}...")
    print(f"{'='*60}\n")

    while True:
        # Call Claude
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )

        # Check if we're done
        if response.stop_reason == "end_turn":
            # Extract final text response
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            return final_text

        # Process tool calls
        if response.stop_reason == "tool_use":
            # Add assistant's response to messages
            messages.append({"role": "assistant", "content": response.content})

            # Execute each tool call
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  → Using tool: {block.name}")
                    print(f"    Input: {block.input}")

                    result = await execute_tool(block.name, block.input)
                    print(f"    Result: {result[:200]}..." if len(result) > 200 else f"    Result: {result}")
                    print()

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            # Add tool results to messages
            messages.append({"role": "user", "content": tool_results})
        else:
            # Unexpected stop reason
            return f"Agent stopped unexpectedly: {response.stop_reason}"

async def main():
    # Example: Design improvement task
    task = """
    I have a landing page that looks like every other SaaS site.
    It's got the standard hero with headline, subheadline, and CTA button.
    I want something that actually stands out in 2024.

    Look at my current implementation and suggest something genuinely fresh—
    not just "add animations" but specific, modern techniques I haven't tried.
    """

    result = await run_agent(task, project_path="./my-project")
    print("\n" + "="*60)
    print("AGENT RESULT:")
    print("="*60)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 4: Running the Agent

```bash
export ANTHROPIC_API_KEY="your-key-here"
python agent.py
```

---

## Real Example: Improving a Product Card

Let's run the agent against a boring product card component. Here's the original:

```tsx
// components/ProductCard.tsx - basic and forgettable
export function ProductCard({ title, price, image, description, onAddToCart }) {
  return (
    <div className="border rounded-lg p-4 shadow-sm">
      <img src={image} alt={title} className="w-full h-48 object-cover rounded" />
      <h3 className="text-lg font-semibold mt-2">{title}</h3>
      <p className="text-gray-600 text-sm mt-1">{description}</p>
      <div className="flex justify-between items-center mt-4">
        <span className="text-xl font-bold">${price}</span>
        <button onClick={onAddToCart} className="bg-blue-500 text-white px-4 py-2 rounded">
          Add to Cart
        </button>
      </div>
    </div>
  );
}
```

**Running the Agent:**

```bash
python agent.py "This product card is boring. Every e-commerce site looks like this.
I want something that feels premium and modern - maybe some micro-interactions,
better visual hierarchy, anything that isn't 'rounded corners and a shadow'." \
  -p ./example-project
```

**What the Agent Does:**

1. `list_files("./example-project")` → maps the project structure
2. `read_file("./example-project/components/ProductCard.tsx")` → examines current code
3. `search_web("modern product card design trends 2024 e-commerce")` → finds current patterns
4. `search_web("framer motion product card hover animations")` → digs into specific techniques
5. `write_file("./example-project/components/ProductCard.improved.tsx")` → outputs the improved version

**Agent Output (condensed):**

> This card screams "Bootstrap tutorial from 2019". Here's what's wrong:
> - Zero hierarchy - the price and button compete for attention
> - No interactivity - static as a newspaper ad
> - Generic shadow - the "I learned CSS yesterday" special
>
> **My recommendation:** A card with layered depth, smooth hover states, and a "quick view" micro-interaction.
>
> Key improvements:
> 1. **Stacked visual layers** using subtle transforms on hover
> 2. **Price badge** that floats over the image corner
> 3. **Animated cart button** that expands with a satisfying spring
> 4. **Quick-view overlay** on image hover

```tsx
// ProductCard.improved.tsx
'use client';
import { motion } from 'framer-motion';
import { useState } from 'react';

export function ProductCard({ title, price, image, description, onAddToCart }) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <motion.div
      className="relative group cursor-pointer"
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      whileHover={{ y: -8 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
    >
      {/* Image container with overlay */}
      <div className="relative overflow-hidden rounded-2xl">
        <motion.img
          src={image}
          alt={title}
          className="w-full h-56 object-cover"
          animate={{ scale: isHovered ? 1.05 : 1 }}
          transition={{ duration: 0.4 }}
        />
        {/* Price badge */}
        <div className="absolute top-3 right-3 bg-white/90 backdrop-blur-sm
                        px-3 py-1 rounded-full font-semibold">
          ${price}
        </div>
        {/* Quick view overlay */}
        <motion.div
          className="absolute inset-0 bg-black/40 flex items-center justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: isHovered ? 1 : 0 }}
        >
          <span className="text-white font-medium">Quick View</span>
        </motion.div>
      </div>

      {/* Content */}
      <div className="mt-4 space-y-2">
        <h3 className="font-semibold text-lg">{title}</h3>
        <p className="text-gray-500 text-sm line-clamp-2">{description}</p>
      </div>

      {/* Animated add to cart */}
      <motion.button
        onClick={onAddToCart}
        className="mt-4 w-full bg-black text-white py-3 rounded-xl font-medium"
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        Add to Cart
      </motion.button>
    </motion.div>
  );
}
```

The key difference from my manual copy-paste workflow: **the agent made the research decisions itself**. It didn't just search once—it iterated based on what it found, then wrote the improved component directly to my project.

---

## What Makes This Different

1. **Externalized thinking** - You fire off the task and come back to results
2. **Tool-use autonomy** - The agent decides what to research, not you
3. **Fresh perspectives** - By searching beyond its training data, it finds current trends
4. **Codebase awareness** - It reads your actual code, not generic examples

---

## Next Steps

This is a starting point. To make it production-ready:
- Add more tools (screenshot analysis, Figma integration, performance checks)
- Implement caching for repeated searches
- Add a simple UI (Streamlit works great)
- Fine-tune the system prompt for your specific stack

The goal isn't to replace your judgment—it's to do the research grunt work so you can focus on the creative decisions that actually matter.

Stop settling for stale components. Build agents that find the fresh stuff for you.

---

*Built with Claude, for developers tired of the same old gradients.*
