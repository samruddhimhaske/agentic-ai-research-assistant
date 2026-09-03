"""
tools/search.py - Wikipedia Search Tool
=========================================
Wikipedia REST API se directly search karta hai — no JSON parsing issues.

Original 'wikipedia' library ke badle direct REST API use kiya kyunki:
  - wikipedia library ka known JSON parsing bug hai
  - REST API zyada reliable aur fast hai
  - No extra dependencies needed (requests already installed hai)
"""

import requests


class WikipediaSearchTool:
    """
    Wikipedia REST API se information search karta hai.
    
    Usage:
        tool = WikipediaSearchTool()
        result = tool.run("agentic AI")
    """

    name: str = "WikipediaSearch"
    description: str = (
        "Searches Wikipedia to find factual information about any topic. "
        "Use this for questions about people, places, concepts, history, science, "
        "technology, or any general knowledge topic. "
        "Input should be a clear search term or topic name."
    )

    # Wikipedia REST API endpoints (no API key needed)
    SEARCH_URL  = "https://en.wikipedia.org/w/api.php"
    SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"

    # Common request headers — Wikipedia prefers a User-Agent
    HEADERS = {
        "User-Agent": "AIResearchAssistantAgent/1.0 (educational project)"
    }

    def run(self, query: str) -> str:
        """
        Search Wikipedia and return a clean summary.

        Steps:
        1. Clean + normalize the query (lowercase, stripped)
        2. Use MediaWiki API to find matching article titles
        3. Fetch the summary of the best match via REST API
        4. Return formatted result

        Args:
            query: Topic to search (e.g. "agentic AI", "quantum computing")

        Returns:
            Formatted Wikipedia summary string, or a helpful error message
        """
        # ── Normalize query ──
        query = query.strip()
        if not query:
            return "Error: No search query provided."

        # Keep only the core keywords — drop question words
        # e.g. "WHAT IS AGENTIC AI" → "agentic AI"
        query = self._clean_query(query)

        try:
            # ── Step 1: Search for matching article titles ──
            titles = self._search_titles(query)

            if not titles:
                return (
                    f"No Wikipedia articles found for '{query}'. "
                    "Try a shorter or simpler search term."
                )

            # ── Step 2: Score titles by relevance to query ──
            # Prefer titles that actually contain the query keywords
            query_words = set(query.lower().split())
            def relevance(title: str) -> int:
                title_lower = title.lower()
                return sum(1 for w in query_words if w in title_lower)

            ranked_titles = sorted(titles[:6], key=relevance, reverse=True)

            # ── Step 3: Try fetching summary for top results ──
            for title in ranked_titles[:4]:
                summary = self._fetch_summary(title)
                if summary:
                    return summary

            # All fetches failed — at least return the titles found
            suggestions = ", ".join(titles[:5])
            return (
                f"Found related topics but couldn't load summaries: {suggestions}. "
                "Try a more specific search term."
            )

        except requests.exceptions.ConnectionError:
            return (
                f"Could not connect to Wikipedia for '{query}'. "
                "Please check your internet connection."
            )
        except Exception as e:
            return f"Search error for '{query}': {str(e)}"

    # ──────────────────────────────────────────────
    # PRIVATE HELPERS
    # ──────────────────────────────────────────────

    def _clean_query(self, query: str) -> str:
        """
        Remove question words and normalize the query for Wikipedia search.

        'WHAT IS AGENTIC AI'  →  'agentic AI'
        'tell me about Python' → 'Python'
        'quantum computing'    → 'quantum computing'  (unchanged)
        """
        # Lowercase for comparison only
        lower = query.lower()

        # Drop leading question phrases
        question_phrases = [
            "what is ", "what are ", "what was ", "what were ",
            "who is ", "who was ", "who are ",
            "tell me about ", "explain ", "describe ",
            "how does ", "how do ", "how is ",
            "give me information about ", "search for ",
        ]
        for phrase in question_phrases:
            if lower.startswith(phrase):
                query = query[len(phrase):].strip()
                break

        # Trim length
        if len(query) > 200:
            query = query[:200]

        return query.strip()

    def _search_titles(self, query: str) -> list[str]:
        """
        Use Wikipedia's MediaWiki API to get a list of matching article titles.

        Returns:
            List of article title strings (could be empty)
        """
        params = {
            "action":   "opensearch",   # Simple autocomplete-style search
            "search":   query,
            "limit":    6,              # Get top 6 matches
            "format":   "json",
            "namespace": 0,             # Only main articles (no Talk, User pages)
        }

        resp = requests.get(
            self.SEARCH_URL,
            params=params,
            headers=self.HEADERS,
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()

        # opensearch returns: [query, [titles], [descriptions], [urls]]
        titles = data[1] if len(data) > 1 else []
        return titles

    def _fetch_summary(self, title: str) -> str | None:
        """
        Fetch the summary of a Wikipedia article by exact title.

        Uses the Wikipedia REST API /page/summary endpoint which returns
        clean, reliable JSON — no parsing bugs.

        Args:
            title: Exact Wikipedia article title

        Returns:
            Formatted summary string, or None if the article doesn't exist
        """
        # URL-encode the title (spaces → underscores for the API)
        encoded_title = title.replace(" ", "_")
        url = self.SUMMARY_URL.format(title=encoded_title)

        try:
            resp = requests.get(url, headers=self.HEADERS, timeout=10)

            if resp.status_code == 404:
                return None  # Article not found, try next title

            resp.raise_for_status()
            data = resp.json()

            # 'extract' is the plain-text summary Wikipedia provides
            extract = data.get("extract", "").strip()
            page_title = data.get("title", title)
            page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")

            if not extract:
                return None

            # Build a clean formatted result
            result = f"📚 Wikipedia: {page_title}\n\n{extract}"
            if page_url:
                result += f"\n\n🔗 Source: {page_url}"

            return result

        except (requests.exceptions.HTTPError, requests.exceptions.JSONDecodeError):
            return None

    def get_tool_info(self) -> dict:
        """Return tool metadata as a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "example_inputs": [
                "quantum computing",
                "Albert Einstein",
                "artificial intelligence",
                "climate change",
                "Python programming language"
            ]
        }
