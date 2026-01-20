"""
Tools for the UI/UX Research Agent
"""
import os
import httpx
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Optional

def read_file(file_path: str) -> str:
    """Read a file from the project directory."""
    try:
        path = Path(file_path)
        if not path.exists():
            return f"Error: File {file_path} not found"
        content = path.read_text()
        # Limit content length to avoid token overflow
        if len(content) > 10000:
            return content[:10000] + "\n\n... [truncated]"
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


def list_files(directory: str, extension: Optional[str] = None) -> str:
    """List files in a directory, optionally filtered by extension."""
    try:
        path = Path(directory)
        if not path.exists():
            return f"Error: Directory {directory} not found"

        files = []
        for f in path.rglob("*"):
            if f.is_file():
                # Skip common non-code directories
                if any(skip in str(f) for skip in ['node_modules', '.git', '__pycache__', '.next']):
                    continue
                if extension is None or f.suffix == extension:
                    files.append(str(f.relative_to(path)))

        return "\n".join(sorted(files)[:50])  # Limit to 50 files, sorted
    except Exception as e:
        return f"Error listing files: {str(e)}"


def write_file(file_path: str, content: str) -> str:
    """Write content to a file. Never overwrites existing files - creates new ones with .new suffix."""
    try:
        path = Path(file_path)

        # Never overwrite existing files
        if path.exists():
            # Add .new before the extension (e.g., Component.tsx -> Component.new.tsx)
            stem = path.stem
            suffix = path.suffix
            new_path = path.parent / f"{stem}.new{suffix}"

            # If .new also exists, add a number
            counter = 2
            while new_path.exists():
                new_path = path.parent / f"{stem}.new{counter}{suffix}"
                counter += 1

            path = new_path

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


async def search_web(query: str) -> str:
    """Search the web for design inspiration and solutions."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
                timeout=10.0
            )
            soup = BeautifulSoup(response.text, "html.parser")
            results = []

            for result in soup.select(".result")[:5]:
                title_elem = result.select_one(".result__title")
                snippet_elem = result.select_one(".result__snippet")

                if title_elem:
                    title = title_elem.get_text(strip=True)
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    results.append(f"**{title}**\n{snippet}\n")

            return "\n".join(results) if results else "No results found"
        except Exception as e:
            return f"Search error: {str(e)}"


async def fetch_url(url: str) -> str:
    """Fetch and extract text content from a URL."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
                timeout=15.0,
                follow_redirects=True
            )
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            text = soup.get_text(separator="\n", strip=True)
            # Limit content
            if len(text) > 5000:
                text = text[:5000] + "\n\n... [truncated]"
            return text
        except Exception as e:
            return f"Fetch error: {str(e)}"


# Tool definitions for Claude API
TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file from the project. Use this to examine existing code, components, styles, or config files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute or relative path to the file to read"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "list_files",
        "description": "List files in a directory. Use this to understand project structure before reading specific files. Automatically skips node_modules, .git, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Directory path to list"
                },
                "extension": {
                    "type": "string",
                    "description": "Optional file extension filter (e.g., '.tsx', '.css', '.js')"
                }
            },
            "required": ["directory"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file. Use this to output improved component code or new files. IMPORTANT: Existing files are NEVER overwritten - if the file exists, a new file with .new suffix is created instead (e.g., Component.tsx -> Component.new.tsx).",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path where the file should be written. If file exists, .new suffix will be added automatically."
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                }
            },
            "required": ["file_path", "content"]
        }
    },
    {
        "name": "search_web",
        "description": "Search the web for design inspiration, UI patterns, component libraries, or bug solutions. Use specific queries like 'modern card component animations 2024' or 'react useEffect cleanup memory leak'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query - be specific for better results"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "fetch_url",
        "description": "Fetch and read the text content from a URL. Use this to read documentation, blog posts, or examples found via search.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to fetch"
                }
            },
            "required": ["url"]
        }
    }
]
