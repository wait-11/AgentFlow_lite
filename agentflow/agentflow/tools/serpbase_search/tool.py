import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(_env_path)

from agentflow.agentflow.tools.base import BaseTool

TOOL_NAME = "SerpBase_Search_Tool"

LIMITATIONS = """
1. Requires a valid SERPBASE_API_KEY from serpbase.dev.
2. Free tier has usage limits; check your SerpBase dashboard for quota.
3. Results depend on SerpBase's upstream search providers.
"""

BEST_PRACTICES = """
1. Use this tool for general web search through SerpBase's Google-compatible API.
2. Keep queries concise and keyword-rich for best results.
3. Supports language (`hl`) and region (`gl`) parameters for localized results.
4. Results include titles, URLs, and snippets from search engine results.
"""


class SerpBase_Search_Tool(BaseTool):
    def __init__(self, model_string=None, base_url=None, **kwargs):
        super().__init__(
            tool_name=TOOL_NAME,
            tool_description="A web search tool powered by SerpBase API that returns Google-style search results with titles, URLs, and snippets.",
            tool_version="1.0.0",
            input_types={
                "query": "str - The search query to find information on the web.",
                "count": "int - Number of results to return (1-10, default 5).",
                "hl": "str - Language code (e.g., 'en', 'zh-CN'). Default 'en'.",
                "gl": "str - Region code (e.g., 'us', 'cn'). Default 'us'.",
            },
            output_type="str - Formatted search results with titles, URLs, and snippets.",
            demo_commands=[
                {
                    "command": 'execution = tool.execute(query="What is the capital of France?")',
                    "description": "Search for general information with default 5 results."
                },
                {
                    "command": 'execution = tool.execute(query="python asyncio tutorial", count=10)',
                    "description": "Search for programming tutorial with 10 results."
                },
            ],
            user_metadata={
                "limitations": LIMITATIONS,
                "best_practices": BEST_PRACTICES,
            }
        )
        self.max_retries = 3

        api_key = os.getenv("SERPBASE_API_KEY")
        if not api_key:
            raise Exception("SerpBase API key not found. Please set the SERPBASE_API_KEY environment variable in .env file.")
        self.api_key = api_key
        self.endpoint = "https://api.serpbase.dev/google/search"

    def _execute_search(self, query: str, count: int = 5, hl: str = "en", gl: str = "us"):
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }

        payload = {
            "q": query,
            "hl": hl,
            "gl": gl,
            "page": 1,
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.endpoint,
                    headers=headers,
                    json=payload,
                    timeout=15,
                )
                response.raise_for_status()
                data = response.json()

                # Parse organic results
                results = []
                organic = data.get("organic", []) if isinstance(data, dict) else []

                for i, item in enumerate(organic):
                    if i >= count:
                        break
                    title = item.get("title", "No title")
                    url = item.get("link", item.get("url", ""))
                    snippet = item.get("snippet", item.get("description", item.get("snippet", "No description")))

                    # Remove HTML tags from snippet
                    import re
                    snippet = re.sub(r'<[^>]+>', '', snippet)

                    results.append(f"{i + 1}. {title}\n   URL: {url}\n   {snippet}")

                if not results:
                    return f"No results found for query: {query}"

                return "\n\n".join(results)

            except requests.exceptions.RequestException as e:
                print(f"SerpBase Search attempt {attempt + 1} failed: {str(e)}. Retrying...")
                if attempt == self.max_retries - 1:
                    return f"SerpBase Search failed after {self.max_retries} attempts. Error: {str(e)}"

        return "SerpBase Search failed to get a valid response"

    def execute(self, query: str, count: int = 5, hl: str = "en", gl: str = "us"):
        """
        Execute the SerpBase search tool.

        Parameters:
            query (str): The search query.
            count (int): Number of results to return (1-10, default 5).
            hl (str): Language code (e.g., 'en', 'zh-CN').
            gl (str): Region code (e.g., 'us', 'cn').

        Returns:
            str: The search results.
        """
        return self._execute_search(query, count, hl, gl)

    def get_metadata(self):
        return super().get_metadata()


if __name__ == "__main__":
    """
    Test:
    cd agentflow/agentflow/tools/serpbase_search
    python tool.py
    """
    def print_json(result):
        import json
        print(json.dumps(result, indent=4))

    tool = SerpBase_Search_Tool()

    metadata = tool.get_metadata()
    print("Tool Metadata:")
    print_json(metadata)

    examples = [
        {'query': 'What is the capital of France?', 'count': 3},
        {'query': 'python asyncio tutorial', 'count': 3},
    ]

    for example in examples:
        print(f"\nExecuting search: {example['query']}")
        try:
            result = tool.execute(**example)
            print("Search Result:")
            print(result)
        except Exception as e:
            print(f"Error: {str(e)}")
        print("-" * 50)

    print("Done!")
