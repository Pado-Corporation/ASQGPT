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
from metagpt.tools.current_researchtool import CURRENT_RESEARCHTOOL, get_tooldescription
import aiohttp

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

TOOL_SUMMARY_PROMPT = """
your role is summarize information based on problem user want to solve, and context of it.

### Problem
{problem}
### Information
{tool_result}

### Requirements
- Always indicate this data was come from google search
- Decide this information is good for user's goal and context, or not.
- Try to include important information like title.
- Never include serpapi.com. Include google url.
"""

FINAL_SUMMARY_PROMT = """
your role is summarize information based on problem user want to solve, and context of it.

### Problem
{problem}
### Reference Information
{reference}

### Requirements
- Make report base on user goal and context.
- Try to include url.
- Give me your comparision based on goal and context
"""


TOOLSELCET_PROMPT_1 = """
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

TOOLSELCET_PROMPT_2 = """
Your role is selecting proper tool based on Action you should do.
### Action
{topic}

### Tool List
{toollist}

### Requirements
- Respond in json form with name of it like ['Websearch',...], without including other words.
- No explanation needed. Only give me result list. 
- You can choose just one best tool for your situation.
"""

TOOLSELECT_PROMPT = """
Your role is making appropriate query for problem I want to solve based on the api description i'll give you.

## problem
{problem}

## API description
{description}

# Requirments
- No explanation needed. Only give me result. 
- You should wrap your result query in python code block

# Format Example
```python```
https://serpapi.com/search.json?engine=google_maps&q=pizza+store&ll=@40.7455096,-74.0083012,15.1z&type=search
```

"""


class ToolSelect(Action):
    """Action class to tool select from a search engine."""

    def __init__(
        self,
        name: str = "",
        *args,
        rank_func: Callable[[list[str]], None] | None = None,
        **kwargs,
    ):
        super().__init__(name, *args, **kwargs)
        self.desc = "Make Proper tool select from problem."
        if CONFIG.model_for_researcher_keyword:
            self.llm.model = CONFIG.model_for_researcher_keyword
        logger.log("DEVELOP", "toolselect llm model is " + self.llm.model)

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
        toollist_prompt = TOOLSELCET_PROMPT_2.format(topic=topic, toollist=current_toollist)
        selected_tools = await self._aask(toollist_prompt, [system_text])
        logger.log("DEVELOP", selected_tools)
        try:
            selected_tools = OutputParser.extract_struct(selected_tools, list)
            selected_tools = parse_obj_as(list[str], selected_tools)
        except Exception as e:
            logger.exception(f'fail to get tools related to the research topic "{topic}" for {e}')
            selected_tools = None

        return selected_tools


class ToolUseSummary(Action):
    def __init__(
        self,
        tool_type: str,
        serp_token=CONFIG.serpapi_api_key,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.desc = "Explore the web and provide summaries of articles and webpages."
        self.tool_type = tool_type
        (
            self.tool_description,
            self.information_path,
            self.detail_path,
            self.final_path,
        ) = get_tooldescription(tool_type)
        if CONFIG.model_for_researcher_summary:
            self.llm.model = CONFIG.model_for_researcher_summary
        self.token = serp_token

    async def toolsetting(self, problem):
        prompt_template = TOOLSELECT_PROMPT.format(
            problem=problem, description=self.tool_description
        )
        api_query = await self.llm.aask(prompt_template)
        return api_query

    async def execute_api(self, url, result_num=5):
        query_url = url + f"&api_key={self.token}&num={result_num}"
        logger.log("DEVELOP", query_url)
        async with aiohttp.ClientSession() as session:
            async with session.get(query_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"Failed to get data from API. Status Code: {response.status}")
                    return None

    async def SummarizeOneResult(self, useful_info, problem):
        try:
            detail_link = useful_info[self.detail_path]
            detail = await self.execute_api(detail_link)
            detail_info = detail[self.final_path]
            page_result = str({"brief": useful_info, self.detail_path: detail_info})

        except Exception as e:
            logger.warning(f"serp detail research fail because of {e}")
            page_result = str({"brief": useful_info})

        tool_summary_prompt = TOOL_SUMMARY_PROMPT.format(problem=problem, tool_result=page_result)
        tool_summary = await self.llm.aask(tool_summary_prompt)
        tool_summary = remove_serpapi_url(tool_summary)
        logger.info(tool_summary)
        return tool_summary

    async def run(self, problem: str, research_num: int):
        api_query = await self.toolsetting(problem)
        try:
            api_query = OutputParser.parse_code(api_query)
            api_query = api_query.strip().strip("'").strip('"')
        except Exception as e:
            logger.exception(f"fail to make proper serpapi query for {e}")
        logger.log("DEVELOP", api_query)
        rsp = await self.execute_api(api_query, research_num)
        useful_infos = rsp[self.information_path]
        useful_infos = useful_infos[:research_num]
        tasks = [
            self.SummarizeOneResult(useful_info=info, problem=problem) for info in useful_infos
        ]
        execution_results = await asyncio.gather(*tasks)
        output = ""
        for i, summary in enumerate(execution_results):
            output += f"Result.{i}\n{summary}\n------------------------------------\n"
        logger.info(output)
        final_summary_prompt = FINAL_SUMMARY_PROMT.format(reference=output, problem=problem)
        summary_report = await self.llm.aask(final_summary_prompt)
        return summary_report


def remove_serpapi_url(tool_summary):
    return tool_summary.replace("serpapi.com", "")


if __name__ == "__main__":
    import fire

    async def main(topic: str):
        print(topic)
        selected_tools = await ToolSelect().run(topic)
        for selected_tool in selected_tools:
            tool_query = await ToolUseSummary(tool_type=selected_tool).run(topic, 5)
            logger.success(tool_query)

    fire.Fire(main)
