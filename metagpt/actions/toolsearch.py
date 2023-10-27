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
from metagpt.actions.webresearch import get_research_system_text
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
Utilize the text in the "Reference Information" section to respond to the question "{problem}".

### Reference Information
{tool_result}

### Requirements
1. If the question cannot be directly answered using the text, but the text is related to the research topic, please provide \
a comprehensive summary of the text.
2. If the text is entirely unrelated to the research topic, please reply with a simple text "Not relevant."- Try to include important information like title.
3. Include all relevant factual information, numbers, statistics, etc., if available.
4. Even if data is not complete, you should make complete answer based on data.
5. Only use data that exists
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
- Only use data that exists

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


class ToolSetting(Action):
    def __init__(
        self,
        tool_type: str,
        serp_token=CONFIG.serpapi_api_key,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.desc = "Setup Tool Setting."
        self.tool_type = tool_type
        (
            self.tool_description,
            self.information_path,
            self.detail_path,
            self.final_path,
        ) = get_tooldescription(tool_type)
        if tool_type == "Walmart API":
            self.detail_path = f"https://serpapi.com/search.json?engine=walmart_product_reviews&product_id={self.detail_path}"
        if CONFIG.model_for_tool_setup:
            self.llm.model = CONFIG.model_for_tool_setup

    async def toolsetting(self, problem):
        prompt_template = TOOL_SETTING_PROMPT.format(
            problem=problem, description=self.tool_description
        )
        api_query = await self._aask(prompt_template)
        return api_query

    async def run(
        self,
        problem: str,
    ):
        self.problem = problem
        api_query = await self.toolsetting(problem)
        try:
            api_query = OutputParser.parse_code(api_query)
            api_query = api_query.strip().strip("'").strip('"')
        except Exception as e:
            logger.exception(f"fail to make proper serpapi query for {e}")
        logger.log("DEVELOP", api_query)
        return problem, api_query


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

    async def execute_api(self, url):
        query_url = url + f"&api_key={self.token}"
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
        prompt_template = TOOL_SUMMARY_PROMPT.format(problem=self.problem, tool_result="{}")
        if detail_name is not None:
            brief_chunk_summaries = []
            detail_chunk_summaries = []
            for brief_prompt in generate_prompt_chunk(
                str(brief_info), prompt_template, self.llm.model, system, CONFIG.max_tokens_rsp
            ):
                logger.debug(brief_prompt)
                brief_summary = await self._aask(brief_prompt)
                brief_chunk_summaries.append(brief_summary)
            for detail_prompt in generate_prompt_chunk(
                detail_name + str(detail_info),
                prompt_template,
                self.llm.model,
                "",
                CONFIG.max_tokens_rsp,
            ):
                logger.debug(detail_prompt)
                detail_summary = await self._aask(detail_prompt)
                detail_chunk_summaries.append(detail_summary)
            tool_summary = str(
                {"brief": brief_chunk_summaries, detail_name: detail_chunk_summaries}
            )
        else:
            brief_chunk_summaries = []
            for brief_prompt in generate_prompt_chunk(
                str(brief_info), prompt_template, self.llm.model, "", CONFIG.max_tokens_rsp
            ):
                logger.debug(brief_prompt)
                brief_summary = await self._aask(brief_prompt)
                brief_chunk_summaries.append(brief_summary)
            tool_summary = str({"brief": brief_chunk_summaries})
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

    async def run(
        self,
        api_query: str,
        problem: str,
        brief_search_num: int,
        detail_search_num: int,
        system_text: str,
    ):
        rsp = await self.execute_api(api_query)
        logger.info(rsp)
        if isinstance(self.information_path, str):
            if "." in self.information_path:
                path1, path2 = self.information_path.split(".")
                useful_infos = rsp[path1][path2]
            else:
                useful_infos = rsp[self.information_path]
            if self.detail_path and self.final_path:
                useful_infos = useful_infos[:detail_search_num]  # 얘네는 접속해서 데이터 긁어와서 제한 안하면 너무오래걸림.
                # detail serpapi link 접속
                tasks = [self._create_summary(info, self.execute_api) for info in useful_infos]
                output = await self.log_and_gather_results(tasks, problem)
                final_summary_prompt = FINAL_SUMMARY_PROMPT.format(
                    reference=output, problem=problem
                )
            elif self.detail_path and not self.final_path:
                useful_infos = useful_infos[:detail_search_num]
                # detail link crawling
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
                # 그냥 대표적 information 가져옴.
                useful_infos = useful_infos[:brief_search_num]
                final_summary_prompt = FINAL_SUMMARY_PROMPT.format(
                    reference=str(useful_infos), problem=problem
                )
            else:
                raise NotImplementedError

        if isinstance(self.information_path, list):
            # self.information_path가 list면 1_depth api call에 유용한 정보가 여러개있다는 것으로 해당 정보를 모두 stacking 하여 final report로 보냄.
            useful_infos = {}
            tasks = []

            for information_path in self.information_path:
                useful_info = rsp[information_path]
                useful_info = useful_info[:brief_search_num]

                # asyncio.gather를 사용하여 비동기 작업을 예약
                task = asyncio.gather(self.SummarizeToolResult(useful_info))
                tasks.append((information_path, task))

            # 비동기 작업들을 동시에 실행
            await asyncio.gather(*[task for _, task in tasks])

            # 결과를 저장
            for information_path, task in tasks:
                useful_infos[information_path] = task.result()

            logger.info(useful_infos)
            final_summary_prompt = FINAL_SUMMARY_PROMPT.format(
                reference=str(useful_infos), problem=problem
            )

        summary_report = await self._aask(final_summary_prompt, [system_text])
        return summary_report


def remove_serpapi_url(tool_summary):
    return tool_summary.replace("api.serpapi.com", "")


if __name__ == "__main__":
    import fire

    async def main(goalncontext: str, topic: str):
        print(topic)
        system_prompt = get_research_system_text(goalncontext, topic, "en")
        selected_tools = await ToolSelect().run(topic, system_prompt)
        for selected_tool in selected_tools:
            tool_query = await ToolUseSummary(tool_type=selected_tool).run(
                topic, brief_search_num=20, detail_search_num=5, system_text=system_prompt
            )
            logger.success(tool_query)

    fire.Fire(main)
