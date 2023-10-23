#!/usr/bin/env python

from __future__ import annotations

import asyncio
import json
from typing import Callable

from pydantic import parse_obj_as

from metagpt.actions import Action
from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.tools.search_engine import SearchEngine
from metagpt.tools.web_browser_engine import WebBrowserEngine, WebBrowserEngineType
from metagpt.utils.common import OutputParser
from metagpt.utils.text import generate_prompt_chunk


LANG_PROMPT = "please respond in {language}"

RESEARCH_BASE_SYSTEM = """You are an AI critical thinker research assistant. Your sole purpose is to write well \
written, critically acclaimed, objective and structured reports on the given text."""

RESEARCH_TOPIC_SYSTEM = "You are an AI researcher assistant, and your research topic is:\n{topic}\n"

SEARCH_TOPIC_PROMPT = """Please provide just upto {keyword_num} important keyword related to your research topic for Google search. \
You should imagine like human and make a keyword like human. find most nice keyword that is most efficient to find ideal result.
Your response must be in JSON format, for example: ["keyword1",...].
### Requirements : 

1. Remember you should give upto {keyword_num} keyword
2. you don't have to respond in only english, please show me mix of korean and english.
"""

# SUMMARIZE_SEARCH_PROMPT = """
# ### Requirements

# 1. The keywords related to your research topic and the search results are shown in the "Search Result Information" section.
# 2. Provide up to {decomposition_nums} queries related to your research topic base on the search results.
# 3. Please respond in the following JSON format: ["query1", "query2", "query3", ...].
# 4. you don't have to respond in english. show me result mix of korean version and english version.
# 5. It's a good idea to pick keywords that are meaningful in order to *gather as much information as possible* to achieve your topic.

# ### Search Result Information
# {search_results}
# """

COLLECT_AND_RANKURLS_PROMPT = """
Your role is ranking every url based on relevancy between query and result snippet
### Query
{query}

### The online search results
{results}

### Requirements
- rank results' indices in JSON format, like [0, 1, 3, 2, ...], without including other words.
- No explanation needed. Only give me result list. like your output only inlcude like [0,1,2,3,...]
"""

WEB_BROWSE_AND_SUMMARIZE_PROMPT = """
### Requirements
1. Utilize the text in the "Reference Information" section to respond to the question "{query}".
2. If the question cannot be directly answered using the text, but the text is related to the research topic, please provide \
a comprehensive summary of the text.
3. If the text is entirely unrelated to the research topic, please reply with a simple text "Not relevant."
4. Include all relevant factual information, numbers, statistics, etc., if available.
5. If you can't access, then Just tell me "I can't access link"

### Reference Information
{content}
"""


CONDUCT_RESEARCH_PROMPT = """
### Reference Information
{content}

### Requirements
Please provide a detailed research report in response to the following topic: "{topic}", using the information provided \
above. The report must meet the following requirements:

- Focus on directly addressing the chosen topic.
- Ensure a well-structured and in-depth presentation, incorporating relevant facts and figures where available.
- Present data and findings in an intuitive manner, utilizing feature comparative tables, if applicable.
- The report should have a minimum word count of 2,000 and be formatted with Markdown syntax following APA style guidelines.
- Include all source URLs in APA format at the end of the report.
- The above summary may not be accurate. Therefore, if you have conflicting information from different sources, use the more reliable information.
- If the numbers in summary are inconsistent with your common sense, correct them using your prior knowledge. When corrected, tag (fixed) and what indicate on report which part fixed.
- Make sure to include the essential information in each URL to create a natural logical flow.  
- Remember you should make a report.
- Make sure to include the link you referenced in, and Put all the links you refer to in the reference part.
- *Never make it up. Never Make a User review or something, Write everything based on reference information*
"""


class GetQueries(Action):
    """Action class to collect links from a search engine."""

    # 얘는 기본적으로 GPT4 이용
    def __init__(
        self,
        name: str = "",
        *args,
        rank_func: Callable[[list[str]], None] | None = None,
        **kwargs,
    ):
        super().__init__(name, *args, **kwargs)
        self.desc = "Make Proper Query from problem."
        self.search_engine = SearchEngine()
        self.rank_func = rank_func
        if CONFIG.model_for_researcher_keyword:
            self.llm.model = CONFIG.model_for_researcher_keyword
        logger.log("DEVELOP", "keyword llm model is " + self.llm.model)

    async def run(
        self,
        topic: str,
        keyword_num: int = 4,
        system_text: str | None = None,
    ) -> dict[str, list[str]]:
        """Run the action to collect links.

        Args:
            topic: The research topic.
            keyword_num: The number of search query to generate.
            url_per_query: The number of URLs to collect per search question.
            system_text: The system text.

        Returns:
            A dictionary containing the search questions as keys and the collected URLs as values.
        """
        system_text = system_text if system_text else RESEARCH_TOPIC_SYSTEM.format(topic=topic)
        search_topic_prompt = SEARCH_TOPIC_PROMPT.format(keyword_num=keyword_num)
        queries = await self._aask(search_topic_prompt, [system_text])
        logger.log("DEVELOP", queries)
        try:
            queries = OutputParser.extract_struct(queries, list)
            queries = parse_obj_as(list[str], queries)
        except Exception as e:
            logger.exception(
                f'fail to get keywords related to the research topic "{topic}" for {e}'
            )
            queries = [topic]

        return queries


class RankLinks(Action):
    """Action class to collect links from a search engine."""

    # 얘는 기본적으로 GPT4 이용
    def __init__(
        self,
        name: str = "",
        *args,
        rank_func: Callable[[list[str]], None] | None = None,
        **kwargs,
    ):
        super().__init__(name, *args, **kwargs)
        self.desc = "Do Query and get links and rank it."
        self.search_engine = SearchEngine()
        self.rank_func = rank_func
        if CONFIG.model_for_researcher_rank:
            self.llm.model = CONFIG.model_for_researcher_rank
        logger.log("DEVELOP", "rank llm model is " + self.llm.model)

    async def run(
        self,
        topic: str,
        queries: list,
        url_per_query: int = 4,
    ) -> dict[str, list[str]]:
        """Run the action to rank links.

        Args:
            topic: The research topic.
            queries: Want to Query and Rank result links
            url_per_query: The number of URLs to collect per search question.
            system_text: The system text.

        Returns:
            A dictionary containing the search questions as keys and the collected URLs as values.
        """
        ret = {}
        tasks = []
        for query in queries:
            task = self._search_and_rank_urls(topic, query, url_per_query)
            tasks.append(task)
        results = await asyncio.gather(*tasks)
        for i, query in enumerate(queries):
            ret[query] = results[i]
        return ret

    async def _search_and_rank_urls(
        self, topic: str, query: str, num_results: int = 4
    ) -> list[str]:
        """Search and rank URLs based on a query.

        Args:
            topic: The research topic.
            query: The search query.
            num_results: The number of URLs to collect. - 1

        Returns:
            A list of ranked URLs.
        """
        max_results = max(num_results * 2, 6)
        results = await self.search_engine.run(query, max_results=max_results, as_string=False)
        _results = "\n".join(f"{i}: {j}" for i, j in zip(range(max_results), results))
        prompt = COLLECT_AND_RANKURLS_PROMPT.format(topic=topic, query=query, results=_results)
        logger.debug(prompt)
        indices = await self._aask(prompt)

        try:
            indices = OutputParser.extract_struct(indices, list)
            assert all(isinstance(i, int) for i in indices)
        except Exception as e:
            logger.exception(f"fail to rank results for {e}")
            indices = list(range(max_results))
        results = [results[i] for i in indices]
        if self.rank_func:
            results = self.rank_func(results)
        return [i["link"] for i in results[:num_results]]


class WebBrowseAndSummarize(Action):
    """Action class to explore the web and provide summaries of articles and webpages."""

    def __init__(
        self,
        *args,
        browse_func: Callable[[list[str]], None] | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if CONFIG.model_for_researcher_summary:
            self.llm.model = CONFIG.model_for_researcher_summary
        self.web_browser_engine = WebBrowserEngine(
            engine=WebBrowserEngineType.CUSTOM if browse_func else None,
            run_func=browse_func,
        )
        self.desc = "Explore the web and provide summaries of articles and webpages."

    async def run(
        self,
        url: str,
        *urls: str,
        query: str,
        system_text: str = RESEARCH_BASE_SYSTEM,
    ) -> dict[str, str]:
        """Run the action to browse the web and provide summaries.

        Args:
            url: The main URL to browse.
            urls: Additional URLs to browse.
            query: The research question.
            system_text: The system text.

        Returns:
            A dictionary containing the URLs as keys and their summaries as values.
        """
        contents = await self.web_browser_engine.run(url, *urls)
        if not urls:
            contents = [contents]

        summaries = {}
        prompt_template = WEB_BROWSE_AND_SUMMARIZE_PROMPT.format(query=query, content="{}")

        async def process_content(url, content):
            content = content.inner_text
            chunk_summaries = []
            for prompt in generate_prompt_chunk(
                content, prompt_template, self.llm.model, system_text, CONFIG.max_tokens_rsp
            ):
                logger.debug(prompt)
                summary = await self._aask(prompt, [system_text])
                if summary == "Not relevant.":
                    continue
                chunk_summaries.append(summary)

            if not chunk_summaries:
                summaries[url] = None
                return

            if len(chunk_summaries) == 1:
                summaries[url] = chunk_summaries[0]
                return

            content = "\n".join(chunk_summaries)
            prompt = WEB_BROWSE_AND_SUMMARIZE_PROMPT.format(query=query, content=content)
            summary = await self._aask(prompt, [system_text])
            summaries[url] = summary

        tasks = []
        for u, content in zip([url, *urls], contents):
            tasks.append(process_content(u, content))
        await asyncio.gather(*tasks)
        return summaries


class ConductResearch(Action):
    """Action class to conduct research and generate a research report."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if CONFIG.model_for_researcher_report:
            self.llm.model = CONFIG.model_for_researcher_report

    async def run(
        self,
        topic: str,
        content: str,
        system_text: str = RESEARCH_BASE_SYSTEM,
    ) -> str:
        """Run the action to conduct research and generate a research report.

        Args:
            topic: The research topic.
            content: The content for research.
            system_text: The system text.

        Returns:
            The generated research report.
        """
        prompt = CONDUCT_RESEARCH_PROMPT.format(topic=topic, content=content)
        logger.debug(prompt)
        self.llm.auto_max_tokens = True
        await asyncio.sleep(0.5)  # For safe writing
        return await self._aask(prompt, [system_text])


def get_research_system_text(topic: str, language: str):
    """Get the system text for conducting research.

    Args:
        topic: The research topic.
        language: The language for the system text.

    Returns:
        The system text for conducting research.
    """
    return " ".join(
        (RESEARCH_TOPIC_SYSTEM.format(topic=topic), LANG_PROMPT.format(language=language))
    )
