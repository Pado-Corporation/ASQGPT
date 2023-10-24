from __future__ import annotations

import asyncio
from typing import Callable

from pydantic import parse_obj_as

from metagpt.actions import Action
from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.tools.search_engine import SearchEngine
from metagpt.tools.web_browser_engine import WebBrowserEngine, WebBrowserEngineType
from metagpt.utils.common import OutputParser
from metagpt.utils.text import generate_prompt_chunk
from metagpt.tools.current_researchtool import CURRENT_RESEARCHTOOL

LANG_PROMPT = "please respond in {language}"

RESEARCH_BASE_SYSTEM = """You are an AI critical thinker research assistant. Your sole purpose is to write well \
written, critically acclaimed, objective and structured reports on the given text."""

RESEARCH_TOPIC_SYSTEM = "You are an AI researcher assistant, and your research topic is:\n{topic}\n"


SEARCH_TOPIC_PROMPT = """Please provide just upto {keyword_num} important keyword related to your research topic for Google search. \
You should imagine like human and make a keyword like human. find most nice keyword that is most efficient to find ideal result.
Your response must be in JSON format, for example: ["keyword1",...].
### Requirements : 

1. Remember you should give upto {keyword_num} keyword
"""


TOOLSELCET_PROMPT = """
Your role is selecting proper tool based on Action you should do.
### Action
{topic}

### Tool List
{toollist}

### Requirements
- Respond in json form with name of it like ['Websearch',...], without including other words.
- No explanation needed. Only give me result list. 
- You can choose tools upto 2
- If, it is best tool, then just use one tool.
- If not, First, choose most proper tool not websearch. if you think there is no proper tool or it's not enough then add websearch.
"""


class ToolSelect(Action):
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
        system_text: str | None = None,
    ) -> list[str]:
        """Run the action to collect links.

        Args:
            topic: The research topic.
            system_text: The system text.

        Returns:
            selected tools list.
        """
        system_text = system_text if system_text else RESEARCH_TOPIC_SYSTEM.format(topic=topic)
        current_toollist = str(CURRENT_RESEARCHTOOL)
        toollist_prompt = TOOLSELCET_PROMPT.format(topic=topic, toollist=current_toollist)
        selected_tools = await self._aask(toollist_prompt, [system_text])
        logger.log("DEVELOP", selected_tools)
        try:
            selected_tools = OutputParser.extract_struct(selected_tools, list)
            selected_tools = parse_obj_as(list[str], selected_tools)
        except Exception as e:
            logger.exception(f'fail to get tools related to the research topic "{topic}" for {e}')
            selected_tools = None

        return selected_tools


class QuerySummary(Action):
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


if __name__ == "__main__":
    import fire

    async def main(topic: str, language="en-us"):
        print(topic)
        await ToolSelect().run(topic)

    fire.Fire(main)
