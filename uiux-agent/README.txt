FIXITMANY - UI/UX RESEARCH AGENT
=================================

An AI agent that helps with web development tasks:
- Fresh design ideas (not the same old shadcn templates)
- Bug research and solutions
- Component improvements and modernization

Supports: Anthropic (Claude), OpenAI (GPT), Google (Gemini)


TL;DR
-----

   # Install
   cd uiux-agent
   pip install -e .

   # Set your API key (Gemini is default)
   export GOOGLE_API_KEY="your-key"

   # Use from anywhere
   fixitmany "Make this component not suck" -p ~/projects/my-webapp


INSTALLATION
------------

Option 1: Install globally (recommended)

   cd uiux-agent
   pip install -e .

   # Now you can run from anywhere:
   fixitmany "Your task" -p /path/to/project

Option 2: Run directly with Python

   cd uiux-agent
   pip install -r requirements.txt
   python agent.py "Your task" -p /path/to/project


CONFIGURATION
-------------

Set your API key(s) as environment variables:

   export GOOGLE_API_KEY="your-key"       # For Gemini (default)
   export ANTHROPIC_API_KEY="your-key"    # For Claude
   export OPENAI_API_KEY="your-key"       # For GPT

Or create a .env file in the uiux-agent directory:

   cp .env.example .env
   # Edit .env and add your API key(s)


USAGE
-----

Basic usage:
   fixitmany "Improve my landing page design" -p ./my-project

With different providers:
   fixitmany --provider anthropic "Fix this CSS bug" -p ./my-project
   fixitmany --provider openai "Modernize this component" -p ./my-project
   fixitmany --provider gemini "Research animation libraries" -p ./my-project

Interactive mode (chat-style):
   fixitmany --interactive -p ./my-project

Quiet mode (less output):
   fixitmany -q "Your task" -p ./my-project

Custom model:
   fixitmany --provider openai --model gpt-4-turbo "Your task" -p ./my-project


EXAMPLE TASKS
-------------

Design inspiration:
   fixitmany "My hero section looks like every other SaaS site. Give me something fresh and modern with actual code." -p ./my-project

Bug fixing:
   fixitmany "I have a hydration mismatch error in my Next.js app. Find and fix it." -p ./my-project

Component upgrade:
   fixitmany "This product card is boring. Add micro-interactions and better visual hierarchy." -p ./my-project

Research:
   fixitmany "What are the best animation libraries for React in 2024? Show me examples." -p ./my-project


WHAT THE AGENT DOES
-------------------

When you give it a task, the agent autonomously:

1. Lists your project files to understand the structure
2. Reads relevant code files
3. Searches the web for modern solutions and patterns
4. Fetches documentation or articles if needed
5. Synthesizes findings into actionable recommendations
6. Writes improved code directly to your project (as new files)


ENVIRONMENT VARIABLES
---------------------

GOOGLE_API_KEY      - Required for Gemini (default provider)
ANTHROPIC_API_KEY   - Required for Claude
OPENAI_API_KEY      - Required for GPT


FILES
-----

agent.py        - Main agent loop and CLI
providers.py    - Multi-provider LLM abstraction
tools.py        - File, search, and fetch tools
.env.example    - Template for API keys
requirements.txt - Python dependencies
pyproject.toml  - Package config for pip install


QUICK REFERENCE
---------------

   fixitmany "task" -p <path>              Basic usage (Gemini default)
   fixitmany --provider anthropic "task"   Use Claude instead
   fixitmany --provider openai "task"      Use GPT instead
   fixitmany -q "task" -p <path>           Quiet mode (less output)
   fixitmany --interactive -p <path>       Chat mode
   fixitmany --model gemini-2.5-pro "task" Custom model
   fixitmany --help                        Show all options


SAFETY
------

The agent NEVER overwrites existing files. If you ask it to write to a file
that already exists, it creates a new file with .new suffix instead:

   ProductCard.tsx (exists) -> ProductCard.new.tsx (created)
