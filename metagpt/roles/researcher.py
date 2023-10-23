#!/usr/bin/env python

import asyncio


from metagpt.actions.research import GetQueries, RankLinks, ConductResearch, WebBrowseAndSummarize
from metagpt.actions.research import get_research_system_text
from metagpt.const import RESEARCH_PATH
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message, Report
from metagpt.remoteDB.reportdb import DBReport
from metagpt.remoteDB import SESSION


class Researcher(Role):
    def __init__(
        self,
        name: str = "David",
        profile: str = "Researcher",
        goal: str = "Gather information and conduct research",
        constraints: str = "Ensure accuracy and relevance of information",
        language: str = "en-us",
        **kwargs,
    ):
        super().__init__(name, profile, goal, constraints, **kwargs)
        self._init_actions(
            [GetQueries(name), RankLinks(name), WebBrowseAndSummarize(name), ConductResearch(name)]
        )
        self.language = language
        if language not in ("en-us", "zh-cn"):
            logger.warning(f"The language `{language}` has not been tested, it may not work.")

    async def _think(self) -> None:
        if self._rc.todo is None:
            self._set_state(0)
            return

        if self._rc.state + 1 < len(self._states):
            self._set_state(
                self._rc.state + 1
            )  # 아 얘네 state 0 부터 차례대로 진행시키겠다는 의미네 0 -> 1 -> 2 -> 3....
        else:
            self._rc.todo = None

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self._rc.todo}")
        todo = self._rc.todo
        msg = self._rc.memory.get(k=1)[0]  # 가장 최근의 메모리를 불러온다.
        if isinstance(msg.instruct_content, Report):
            instruct_content = msg.instruct_content
            topic = instruct_content.topic
        else:
            topic = msg.content

        research_system_text = get_research_system_text(topic, self.language)
        if isinstance(todo, GetQueries):
            queries = await todo.run(topic, 5)
            report = Report(
                topic=topic, queries=queries, write_by=self._agent_id, report_type="GetQueries"
            )
            ret = Message(
                "",
                report,
                role=self.profile,
                cause_by=type(todo),
            )  # Message의 instruct_content에 Report type을 넣는다. topic을 계속해서 같은걸로 유지한다.
        elif isinstance(todo, RankLinks):
            queries = instruct_content.queries
            links = await todo.run(topic, queries, 5)
            report = Report(
                topic=topic, links=links, write_by=self._agent_id, report_type="RankLinks"
            )
            ret = Message(
                "",
                report,
                role=self.profile,
                cause_by=type(todo),
            )
        elif isinstance(todo, WebBrowseAndSummarize):
            links = instruct_content.links
            todos = (
                todo.run(*url, query=query, system_text=research_system_text)
                for (query, url) in links.items()
            )
            summaries = await asyncio.gather(*todos)
            summaries = list(
                (url, summary) for i in summaries for (url, summary) in i.items() if summary
            )
            report = Report(
                topic=topic,
                summaries=summaries,
                write_by=self._agent_id,
                report_type="WebBrowseAndSummarize",
            )
            ret = Message(
                "",
                report,
                role=self.profile,
                cause_by=type(todo),
            )
        else:
            summaries = instruct_content.summaries
            summary_text = "\n---\n".join(
                f"url: {url}\nsummary: {summary}" for (url, summary) in summaries
            )
            content = await self._rc.todo.run(topic, summary_text, system_text=research_system_text)
            report = Report(
                topic=topic,
                content=content,
                write_by=self._agent_id,
                report_type="ConductResearch",
            )
            ret = Message(
                "",
                report,
                role=self.profile,
                cause_by=type(self._rc.todo),
            )
        self._rc.memory.add(ret)
        db_report = DBReport(**report.dict())
        SESSION.add(db_report)
        SESSION.commit()
        return ret

    async def _react(self) -> Message:
        while True:
            await self._think()
            if self._rc.todo is None:
                break
            msg = await self._act()
        report = msg.instruct_content
        self.write_report(report.topic, report.content)
        return msg

    def write_report(self, topic: str, content: str):
        if not RESEARCH_PATH.exists():
            RESEARCH_PATH.mkdir(parents=True)
        filepath = RESEARCH_PATH / f"{topic}.md"
        filepath.write_text(content)


if __name__ == "__main__":
    import fire

    async def main(topic: str, language="en-us"):
        role = Researcher(topic, language=language)
        await role.run(topic)

    fire.Fire(main)
