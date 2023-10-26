from __future__ import annotations

import asyncio
from typing import Callable

from pydantic import parse_obj_as

from metagpt.actions import Action
from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.tools.web_browser_engine import WebBrowserEngine, WebBrowserEngineType
from metagpt.utils.common import OutputParser
from metagpt.utils.text import generate_prompt_chunk
from metagpt.tools.current_researchtool import CURRENT_RESEARCHTOOL, get_tooldescription
import aiohttp

LANG_PROMPT = "please act as {language} people, you must respond in {language}"

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
- Decide this information is good for user's goal and context, or not.
- Try to include important information like title.
- Never include serpapi.com. Include google url.
"""

FINAL_SUMMARY_PROMPT = """
your role is summarize information based on problem user want to solve, and context of the problem.

### Problem
{problem}
### Reference Information
{reference}

### Requirements
- Make report base on user goal and context.
- Try to include url.
- Give me your idea about the goal based on reference information.
"""


TOOL_SELCET_PROMPT_1 = """
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

TOOL_SELCET_PROMPT_2 = """
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

TOOL_SETTING_PROMPT = """
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
        toollist_prompt = TOOL_SELCET_PROMPT_1.format(topic=topic, toollist=current_toollist)
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
        if tool_type == "Walmart API":
            self.detail_path = f"https://serpapi.com/search.json?engine=walmart_product_reviews&product_id={self.detail_path}"
        if CONFIG.model_for_researcher_summary:
            self.llm.model = CONFIG.model_for_researcher_summary
        self.token = serp_token

    async def toolsetting(self, problem):
        prompt_template = TOOL_SETTING_PROMPT.format(
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

    async def SummarizeToolResult(self, brief_info, detail_name=None, detail_info=None):
        if detail_name is not None:
            brief_prompt = TOOL_SUMMARY_PROMPT.format(
                problem=self.problem, tool_result=str(brief_info)
            )
            brief_summary = await self.llm.aask(brief_prompt)
            detail_prompt = TOOL_SUMMARY_PROMPT.format(
                problem=self.problem, tool_result=detail_name + str(detail_info)
            )
            detail_summary = await self.llm.aask(detail_prompt)
            tool_summary = str({"brief": brief_summary, detail_name: detail_summary})
        else:
            brief_prompt = TOOL_SUMMARY_PROMPT.format(
                problem=self.problem, tool_result=str(brief_info)
            )
            brief_summary = await self.llm.aask(brief_prompt)
            tool_summary = str({"brief": brief_summary})
        tool_summary = remove_serpapi_url(tool_summary)
        logger.info(tool_summary)
        return tool_summary

    async def APIToolsSummarize(self, useful_info):
        try:
            detail_link = useful_info[self.detail_path]
            detail = await self.execute_api(detail_link)
            detail_info = detail[self.final_path]
            return await self.SummarizeToolResult(useful_info, self.detail_path, detail_info)
        except Exception as e:
            logger.warning(f"serp detail research fail because of {e}")
            return await self.SummarizeToolResult(useful_info)

    async def CrawlerToolsSummaize(self, useful_info):
        try:
            detail_link = useful_info[self.detail_path]
            detail_info = await WebBrowserEngine(WebBrowserEngineType("playwright")).run(
                detail_link
            )
            return await self.SummarizeToolResult(useful_info, self.detail_path, detail_info)
        except Exception as e:
            logger.warning(f"serp detail research fail because of {e}")
            return await self.SummarizeToolResult(useful_info)

    async def _create_summary(self, info, method):
        try:
            detail_link = info[self.detail_path]
            detail_info = await method(detail_link)
            return await self.SummarizeToolResult(info, self.detail_path, detail_info)
        except Exception as e:
            logger.warning(f"Detail research failed because of {e}")
            return await self.SummarizeToolResult(info)

    async def log_and_gather_results(self, tasks, problem):
        execution_results = await asyncio.gather(*tasks)
        output = ""
        for i, summary in enumerate(execution_results):
            output += f"Result.{i}\n{summary}\n------------------------------------\n"
        logger.info(output)
        return output

    async def run(self, problem: str, research_num: int, system_text: str):
        self.problem = problem
        api_query = await self.toolsetting(problem)
        try:
            api_query = OutputParser.parse_code(api_query)
            api_query = api_query.strip().strip("'").strip('"')
        except Exception as e:
            logger.exception(f"fail to make proper serpapi query for {e}")
        logger.log("DEVELOP", api_query)
        rsp = await self.execute_api(api_query, research_num)

        if isinstance(self.information_path, str):
            useful_infos = rsp[self.information_path][:research_num]
            if self.detail_path and self.final_path:
                tasks = [self._create_summary(info, self.execute_api) for info in useful_infos]
                output = await self.log_and_gather_results(tasks, problem)
                final_summary_prompt = FINAL_SUMMARY_PROMPT.format(
                    reference=output, problem=problem
                )
            elif self.detail_path and not self.final_path:
                tasks = [
                    self._create_summary(
                        info, WebBrowserEngine(WebBrowserEngineType("playwright")).run
                    )
                    for info in useful_infos
                ]
                output = await self.log_and_gather_results(tasks, problem)
                final_summary_prompt = FINAL_SUMMARY_PROMPT.format(
                    reference=output, problem=problem
                )
            elif not self.detail_path and not self.final_path:
                final_summary_prompt = FINAL_SUMMARY_PROMPT.format(
                    reference=str(useful_infos), problem=problem
                )
            else:
                raise NotImplementedError

        if isinstance(self.information_path, list):
            # self.information_path가 list면 1_depth api call에 유용한 정보가 여러개있다는 것으로 해당 정보를 모두 stacking 하여 final report로 보냄.
            useful_infos = {}
            for information_path in self.information_path:
                useful_infos_rsp = rsp[information_path]
                useful_infos_rsp = useful_infos_rsp[:research_num]
                useful_infos[information_path] = useful_infos_rsp
            logger.info(useful_infos)
            final_summary_prompt = FINAL_SUMMARY_PROMPT.format(
                reference=str(useful_infos), problem=problem
            )

        summary_report = await self.llm.aask(final_summary_prompt, [system_text])
        return summary_report


def remove_serpapi_url(tool_summary):
    return tool_summary.replace("api.serpapi.com", "")


if __name__ == "__main__":
    import fire

    async def main(topic: str):
        print(topic)
        selected_tools = await ToolSelect().run(topic)
        for selected_tool in selected_tools:
            tool_query = await ToolUseSummary(tool_type=selected_tool).run(topic, 5)
            logger.success(tool_query)

    fire.Fire(main)
