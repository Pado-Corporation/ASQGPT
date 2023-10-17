"""
Filename: MetaGPT/examples/simple_reporter.py
Created Date: Tuesday, September 19th 2023, 7:52:25 pm
Author: garylin2099
"""
import re
import asyncio

import fire

from metagpt.actions import Action
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger


class CreateTableOfContentsnActionItems(Action):
    PROMPT_TEMPLATE = """
    Create a table of contents and Action Items for making that report. for a report with the purpose of {context}.
    Return ```python your_code_here ``` with NO other texts,
    example: 
    ```python
    # Table of Contents
    1. Report Overview
        1-1. Purpose and Scope
        1-2. Data and information sources used
        1-3. How to Organize the Report

    2. Product Overview
        2-1. Features and Benefits of Eco-friendly Plastic Products
        2-2. Main Uses and Applications of Products
        2-3. Environmental Benefits of Eco-friendly Plastics

    3. Market Analysis (Market Analysis)
        3-1. current market trends and forecasts
        3-2. Competitive Product and Brand Analysis
        3-3. Demand forecast for eco-friendly products

    4. Target Audience Analysis (Target Audience Analysis)
        4-1. Characteristics and consumption trends of major target audience groups
        4-2. Consumption habits and expectations of the target audience
        4-3. Perceptions and opinions of eco-friendly products among target audiences

    5. Marketing & Promotion Strategy (Marketing & Promotion Strategy)
        5-1. Setting up key marketing messages and points
        5-2. Select effective marketing channels and platforms
        5-3. Ideas for public relations and advertising campaigns

    6. Entry Strategy
        6-1. Product Launch and Promotion Strategy
        6-2. Pricing and Discount Strategy
        6-3. Distribution and Logistics Strategy


    # ActionItems
    1. Search the internet for data and reports on current market trends, consumer perceptions, competitive landscape, and more for green products.
    2. Gather reactions and feedback about green products on social media, forums, and review sites
    3. Researching the internet to analyze prices, features, marketing strategies, etc. of similar products
    4. Gathering information on green-related meetings, events, and seminars
    5. Search for consumer research and reports related to your key target audiences
    6. Searching for SWOT analysis reports or materials on related industries
    7. Research on effective marketing channels and platforms
    8. Search for data and tools to analyze the effectiveness and ROI of promotional and advertising campaigns
    ```
    constraint : 
    1. These action will be actioned by AI, so you all of the action should be able to be actioned by information that is on internet. For example, user interview shouldn't be included because
    it need practical action. but searching review is possbile.
    2. give me diverse ActionItem as much as possbile
    3. do self-feedback, and if you think one of actionitems needs practical action, then think again.  

    """

    def __init__(self, name="CreateTableOfContentsnActionItems", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context: str):
        prompt = self.PROMPT_TEMPLATE.format(context=context)

        rsp = await self._aask(prompt)

        table_of_contents, actionitems = CreateTableOfContentsnActionItems.parse_code(rsp)

        return table_of_contents, actionitems

    @staticmethod
    def parse_code(rsp):
        pattern = r"```python(.*)```"
        match = re.search(pattern, rsp, re.DOTALL)
        content = match.group(1) if match else rsp
        table_of_contents, actionItems = content.split("# ActionItems")
        
        return table_of_contents, actionItems

    


class SimpleReporter(Role):
    def __init__(
        self,
        name: str = "Jonas",
        profile: str = "SimpleReporter",
        **kwargs,
    ):
        super().__init__(name, profile, **kwargs)
        self._init_actions([CreateTableOfContentsnActionItems])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self._rc.todo}")
        todo = self._rc.todo

        msg = self._rc.memory.get()[-1]  # retrieve the latest memory
        context = msg.content

        if isinstance(todo, CreateTableOfContentsnActionItems):
            table_of_contents = await CreateTableOfContentsnActionItems().run(context)
            msg = Message(content=table_of_contents, role=self.profile, cause_by=todo)
\

        return msg


def main(msg="Create a report on climate change"):
    role = SimpleReporter()
    logger.info(msg)
    result = asyncio.run(role.run(msg))
    logger.info(result)


if __name__ == "__main__":
    fire.Fire(main)
