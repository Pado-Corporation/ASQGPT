import re
import asyncio

import fire
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt.actions.planning import CreateTableOfContentsnActionItems, AssignActionItems
from metagpt.actions.planning import get_planning_system_text


class PlanningPM(Role):
    def __init__(
        self,
        name: str = "Jonas",
        profile: str = "PlanningPM",
        language: str = "en-us",
        **kwargs,
    ):
        super().__init__(name, profile, **kwargs)
        self._init_actions([CreateTableOfContentsnActionItems(name), AssignActionItems(name)])
        self.language = language

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self._rc.todo}")
        todo = self._rc.todo

        msg = self._rc.memory.get(k=0)[-1]  # retrieve the latest memory
        context = msg.content
        planning_system_text = get_planning_system_text(context, language=self.language)
        if isinstance(todo, CreateTableOfContentsnActionItems):
            table_of_contents, actionItems = await todo.run(context, planning_system_text)
            logger.info(f"Table Contents : \n{table_of_contents}")
            self.table_of_contents = table_of_contents
            logger.info(f"action Items : \n{actionItems}")
            self.actionItems = actionItems
            ret = Message(content=actionItems, role=self.profile, cause_by=todo)

        if isinstance(todo, AssignActionItems):
            assigned = await todo.run(context, planning_system_text)
            logger.info("Assigned Results : \n", assigned)
            ret = Message(content=assigned, role=self.profile, cause_by=todo)
        self._rc.memory.add(ret)
        return ret

    async def _think(self) -> None:
        """Determine the next action to be taken by the role."""
        if self._rc.todo is None:
            self._set_state(0)
            return

        if self._rc.state + 1 < len(self._states):
            self._set_state(self._rc.state + 1)
        else:
            self._rc.todo = None

    async def _react(self) -> Message:
        while True:
            await self._think()
            if self._rc.todo is None:
                break
            msg = await self._act()
        return msg


def main(topic="Create a report on climate change", context=None):
    role = PlanningPM()
    logger.info(f"topic: \n {topic}")
    result = asyncio.run(role.run(topic))
    return result


if __name__ == "__main__":
    fire.Fire(main)
