import os
import wikipedia
from pydantic import BaseModel

from agentflow.agentflow.tools.base import BaseTool
from agentflow.agentflow.engine.factory import create_llm_engine
from agentflow.agentflow.tools.web_search.tool import Web_Search_Tool

# from web_rag import Web_Search_Tool
# from agentflow.agentflow.tools.web_search.tool import Web_Search_Tool # NOTE: Shall be used in the future

# from utilis import select_relevant_queries

from agentflow.agentflow.tools.base import BaseTool
from agentflow.agentflow.engine.factory import create_llm_engine

# Tool name mapping - this defines the external name for this tool
TOOL_NAME = "Wikipedia_RAG_Search_Tool"

LIMITATION = f"""
{TOOL_NAME} has the following limitations:
1. It is designed specifically for retrieving grounded information from Wikipedia pages only.
2. Filtering of relevant pages depends on LLM model performance and may not always select optimal pages.
3. The returned information accuracy depends on Wikipedia content quality.
"""

BEST_PRACTICE = f"""
For optimal results with {TOOL_NAME}:
1. Use specific, targeted queries rather than broad or ambiguous questions.
2. The tool automatically filters for relevant pages using LLM-based selection - trust the "relevant_pages" results.
3. If initial results are insufficient, examine the "other_pages" section for additional potentially relevant content.
4. Use this tool as part of a multi-step research process rather than a single source of truth.
5. You can use the {TOOL_NAME} to get more information from the URLs.
"""

class Select_Relevant_Queries(BaseModel):
    matched_queries: list[str]
    matched_query_ids: list[int]

def select_relevant_queries(original_query: str, query_candidates: list[str], llm_engine):

    query_candidates_str = "\n".join([f"{i}. {query}" for i, query in enumerate(query_candidates)])

    prompt = f"""
You are an expert AI assistant. Your task is to identify and select the most relevant queries from a list of Wikipedia search results that are most likely to address the user’s original question.

## Input

Original Query: `{original_query}`
Query Candidates from Wikipedia Search: `{query_candidates_str}`

## Instructions

1. Carefully read the original query and the list of query candidates.
2. Select the query candidates that are most relevant to the original query — i.e., those most likely to contain the information needed to answer the question.
3. Return the most relevant queries. If you think multiple queries are helpful, you can return up to 3 queries.

Your response MUST be a valid JSON object with these exact fields:
- "matched_queries": A list of the matched query strings (e.g. ["France"]).
- "matched_query_ids": A list of the matched query integer IDs (e.g. [1]). Do not return an empty list.

Do NOT wrap the JSON in markdown code blocks. Output ONLY the raw JSON object.

## Examples

Original Query: What is the capital of France?
Query Candidates: 0. Closed-ended question, 1. France, 2. Capital city
Output: {{"matched_queries": ["France"], "matched_query_ids": [1]}}

Original Query: What is the mass of the moon?
Query Candidates: 0. Moon, 1. Planetary-mass moon, 2. Earth mass
Output: {{"matched_queries": ["Moon", "Planetary-mass moon"], "matched_query_ids": [0, 1]}}
"""

    try:
        response = llm_engine.generate(prompt, response_format=Select_Relevant_Queries)

        # Handle different response types: Pydantic model, dict, or string
        if isinstance(response, Select_Relevant_Queries):
            matched_queries = response.matched_queries
            matched_query_ids = [int(i) for i in response.matched_query_ids]
        elif isinstance(response, dict):
            matched_queries = response.get("matched_queries", [])
            matched_query_ids = [int(i) for i in response.get("matched_query_ids", [])]
        elif isinstance(response, str):
            import json
            try:
                data = json.loads(response)
                matched_queries = data.get("matched_queries", [])
                matched_query_ids = [int(i) for i in data.get("matched_query_ids", [])]
            except json.JSONDecodeError:
                print(f"Error parsing LLM response as JSON: {response[:200]}")
                return [], []
        else:
            print(f"Unexpected response type: {type(response)}")
            return [], []

        return matched_queries, matched_query_ids
    except Exception as e:
        print(f"Error selecting relevant queries: {e}")
        return [], []

class Wikipedia_Search_Tool(BaseTool):
    def __init__(self, model_string="gpt-4o-mini", base_url: str = None, **kwargs):
        super().__init__(
            tool_name=TOOL_NAME,
            tool_description="A tool that searches Wikipedia and returns relevant pages with their page titles, URLs, abstract, and retrieved information based on a given query.",
            tool_version="1.0.0",
            input_types={
                "query": "str - The search query for Wikipedia."
            },
            output_type="dict - A dictionary containing search results, all matching pages with their content, URLs, and metadata.",
            demo_commands=[
                {
                    "command": 'execution = tool.execute(query="What is the exact mass in kg of the moon")',
                    "description": "Search Wikipedia and get the information about the mass of the moon."
                },
                {
                    "command": 'execution = tool.execute(query="Funtion of human kidney")',
                    "description": "Search Wikipedia and get the information about the function of human kidney."
                },
                {
                    "command": 'execution = tool.execute(query="When was the first moon landing?")',
                    "description": "Search Wikipedia and get the information about the first moon landing."
                }
            ],
            user_metadata = {
                "limitation": LIMITATION,
                "best_practice": BEST_PRACTICE
            }
        )
        self.model_string = model_string
        self.base_url = base_url
        self.llm_engine = create_llm_engine(
            model_string=model_string, base_url=base_url,
            temperature=0.0, top_p=1.0, frequency_penalty=0.0, presence_penalty=0.0
        )

    def _get_wikipedia_url(self, query):
        """
        Get the Wikipedia URL for a given query.
        """
        query = query.replace(" ", "_") # replace spaces with underscores
        return f"https://en.wikipedia.org/wiki/{query}"

    def search_wikipedia(self, query, max_length=100, max_pages=10):
        """
        Searches Wikipedia based on the given query and returns multiple pages with their text and URLs.

        Parameters:
            query (str): The search query for Wikipedia.

        Returns:
            tuple: (search_results, pages_data)
                - search_results: List of search result titles
                - pages_data: List of dictionaries containing page info (title, text, url, error)
        """
        try:
            search_results = wikipedia.search(query)
            if not search_results:
                return [{"title": None, "url": None, "abstract": None, "error": f"No results found for query: {query}"}]

            pages_data = []
            pages_to_process = search_results[:max_pages] if max_pages else search_results

            # get the pages datafsave
            
            for title in pages_to_process:
                try:
                    page = wikipedia.page(title)
                    text = page.content
                    url = page.url

                    if max_length != -1:
                        text = text[:max_length] + f"... [truncated]" if len(text) > max_length else text

                    pages_data.append({
                        "title": title,
                        "url": url,
                        "abstract": text
                    })
                except Exception as e:
                    pages_data.append({
                        "title": title,
                        "url": self._get_wikipedia_url(title),
                        "abstract": "Please use the URL to get the full text further if needed.",
                    })

            return pages_data
        except Exception as e:
            return [{"title": None, "url": None, "abstract": None, "error": f"Error searching Wikipedia: {str(e)}"}]

    def execute(self, query):
        """
        Searches Wikipedia based on the provided query and returns all matching pages.

        Parameters:
            query (str): The search query for Wikipedia.

        Returns:
            dict: A dictionary containing the search results and all matching pages with their content.
        """
        # First get relevant queries from the search results
        search_results = self.search_wikipedia(query)

        # Get the titles of the pages
        titles = [page["title"] for page in search_results if page["title"] is not None]
        if not titles:
            return {"query": query, "relevant_pages": [], "other_pages (may be irrelevant to the query)": search_results}

        # Select the most relevant pages
        matched_queries, matched_query_ids = select_relevant_queries(query, titles, self.llm_engine)

        # If LLM filtering failed, return all results as other_pages for the agent to use
        if not matched_query_ids:
            return {"query": query, "relevant_pages": [], "other_pages (may be irrelevant to the query)": search_results}

        # Only process the most relevant pages
        valid_ids = [i for i in matched_query_ids if i < len(search_results)]
        pages_data = [search_results[i] for i in valid_ids]
        other_pages = [search_results[i] for i in range(len(search_results)) if i not in valid_ids]

        # For each relevant page, get detailed information using Web RAG
        try:
            web_rag_tool = Web_Search_Tool(model_string=self.model_string)
        except Exception as e:
            print(f"Error creating Web RAG tool: {e}")
            return {"query": query, "relevant_pages": pages_data if pages_data else [],
                    "other_pages (may be irrelevant to the query)": search_results}

        for page in pages_data:
            url = page["url"]
            if url is None:
                continue
            try:
                execution = web_rag_tool.execute(query=query, url=url)
                page["retrieved_information"] = execution
            except Exception as e:
                page["retrieved_information"] = None

        return {
            "query": query,
            "relevant_pages (to the query)": pages_data,
            "other_pages (may be irrelevant to the query)": other_pages
        }

    def get_metadata(self):
        """
        Returns the metadata for the Wikipedia_Search_Tool.

        Returns:
            dict: A dictionary containing the tool's metadata.
        """
        metadata = super().get_metadata()
        return metadata


if __name__ == "__main__":
    # Test command:
    """
    Run the following commands in the terminal to test the script:

    cd agentflow/tools/wikipedia_search
    python tool.py
    """

    # Example usage of the Wikipedia_Search_Tool
    tool = Wikipedia_Search_Tool(model_string="gpt-4o-mini")
    # tool = Wikipedia_Search_Tool(model_string="gemini-1.5-flash")
    # tool = Wikipedia_Search_Tool(model_string="dashscope") # 

    # Get tool metadata
    metadata = tool.get_metadata()
    # print(metadata)

    # Sample query for searching Wikipedia
    # query = "Python programming language"
    # query = "what is the main function of the human kidney"
    # query = "What is the mass of the moon"
    # query = "mass of the moon"
    # query = "mass of the moon in kg"
    # query = "What is the mass of the moon (in kg)?"
    # query = "What is the capital of France"
    # query = "Who is Yann LeCun"
    # query = "What is the exact mass in kg of the moon?"
    query = "When was the first moon landing?"

    import json

    # Execute the tool with the sample query
    try:
        # Test with default parameters (all pages)
        execution = tool.execute(query=query)
        print("Execution Result (all pages):")
        print(json.dumps(execution, indent=4))

        # Save the execution result to a JSON file
        os.makedirs("logs", exist_ok=True)
        with open(f"logs/{query}.json", "w") as f:
            json.dump(execution, f, indent=4)
        
    except ValueError as e:
        print(f"Execution failed: {e}")

    print("Done!")
