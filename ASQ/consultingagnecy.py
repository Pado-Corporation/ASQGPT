import asyncio
from roles import (
    BossAgent,
    ProjectOwnerAgent,
    QueueManagerAgent,
    SummerizerAgent,
)  # Importing agent classes

from ASQ.logs import logger


class ConsultingAgency:
    def __init__(self):
        self.agents = {
            "boss": BossAgent(agency=self),
            "project_owner": ProjectOwnerAgent(agency=self),
            "queue_manager": QueueManagerAgent(agency=self),
            "summerizer": SummerizerAgent(agent=self),
            "researcher": [],
            "analyzer": [],
            "visualizer": [],
            # ... other agents ...
        }
        self.history = Information(data={})
        self.memory = Information(data={})
        self.goal = None
        self.context = None
        self.toc = None
        self.action_items = None
        self.output = None
        self.feedback = []
        self.output = []
        logger.info("Agency Made")

    def get_agents(self, agent_name):
        return self.agents.get(agent_name)

    def hire(self, agent_list):
        for agent in agent_list:
            agent_type = type(agent).__name__.lower()
            self.agents[agent_type].append(agent)

    async def run(self, user_input, max_iter):
        self.user_input = user_input

        goal, context = await self.agents["boss"].interact_with_user(user_input=user_input)
        self.goal = goal
        self.context = context

        toc, action_items = await self.agents["project_owner"].extract_toc_action_items()
        self.toc = toc
        self.action_items = action_items

        need_to_hire = await self.agents["queue_manager"].assign_action_items()
        self.hire(need_to_hire)

        await self.agents["queue_manager"].order_action_items()

        output = await self.agents["summerizer"].summerize()
        self.output.append(output)

        feedback = await self.agents["boss"].brief_to_user(output)
        self.feedback.append(feedback)

        for i in range(max_iter):
            need_to_hire = await self.agents["project_owner"].extract_toc_action_items_feedback(
                feedback
            )
            self.hire(need_to_hire)
            await self.agents["queue_manager"].order_action_items_feedback()

            output = await self.agents["summerizer"].summerize_feedback()
            self.output.append(output)

            feedback = await self.agents["boss"].brief_to_user_feedback(output)
            self.feedback.append(feedback)

            if feedback is None:
                break
        logger.info("Project Ended")

    def get_action_queues(self):
        return self.agents["queue_manager"].get_queues()
