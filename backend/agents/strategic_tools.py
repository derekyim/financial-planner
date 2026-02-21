"""Tools available to the Strategic Guidance agent.

Includes Tavily web search for real-time industry and financial news.
"""

import os
from datetime import date
from langchain_core.tools import tool


@tool
def web_search(query: str) -> str:
    """Search the web for RECENT information about business trends, industry news,
    financial analysis, ecommerce, Amazon, Shopify, TikTok Shop, advertising,
    and other relevant topics.

    The search automatically restricts results to the last 90 days to ensure
    you get current data. You do NOT need to add a year to the query.

    Args:
        query: The search query. Be specific and include relevant keywords.

    Returns:
        Search results with summaries and source URLs.
    """
    from tavily import TavilyClient

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Tavily API key not configured. Unable to perform web search."

    today = date.today()
    year = today.year
    month = today.strftime("%B")
    dated_query = f"{query} {month} {year}"

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=dated_query,
            search_depth="advanced",
            max_results=5,
            include_answer=True,
            days=90,
        )

        parts = [f"(Search date: {today.isoformat()} — results from the last 90 days)\n"]
        if response.get("answer"):
            parts.append(f"**Summary**: {response['answer']}\n")

        parts.append("**Sources**:")
        for result in response.get("results", []):
            title = result.get("title", "Untitled")
            url = result.get("url", "")
            content = result.get("content", "")[:300]
            published = result.get("published_date", "")
            date_tag = f" [{published}]" if published else ""
            parts.append(f"\n- **{title}**{date_tag}\n  {url}\n  {content}")

        return "\n".join(parts)
    except Exception as e:
        return f"Web search error: {str(e)}"


STRATEGIC_TOOLS = [web_search]
