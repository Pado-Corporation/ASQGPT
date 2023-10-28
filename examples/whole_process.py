from metagpt.roles.planningpm import PlanningPM
from metagpt.roles.researcher import Researcher
from metagpt.remoteDB import init_db
import asyncio
import fire
import openai
from metagpt.config import CONFIG
import vecs
from metagpt.logs import logger
from metagpt.asq_agents.boss import agent as Boss
from metagpt.asq_agents.summarizer import agent as Summarizer
from metagpt.asq_agents.combiner import agent as Combiner


DB_CONNECTION = CONFIG.db_addr
vx = vecs.Client(DB_CONNECTION)

pass_boss = """[GOAL] The user wants to deliver a structured and effective presentation on ILM powered multi-agent systems and AGI to students.
[CONTEXT] The user's presentation is about ILM powered multi-agent systems and their relation to AGI. The key points to be highlighted are the possibility of AGI, elements of AGI, and companies that are developing AGI. The user does not have a specific structure in mind for the presentation and there are no time constraints. The user needs help with the delivery of the presentation, specifically in making it more structured."""


async def main(language="en-us", output_path="example.md"):
    init_db()
    openai.api_key = CONFIG.openai_api_key
    boss_agent = Boss.Agent(language=language)
    goalncontext = boss_agent.run()
    pm_agent = PlanningPM(language=language)
    logger.info(f"{goalncontext}")
    assigned = await pm_agent.run(goalncontext)
    # TODO: `toc` needs to be delivered to the Combiner.
    combiner_agent = Combiner.Agent(goalncontext, toc, language="English")
    for assign in assigned.content:
        if assign["type"] == "Researcher":
            role = Researcher(language=language)
            report_summary = await role.run(assign["task"])
            logger.info(f"Research Report: {report_summary}")
            combiner_agent.feed(report_summary)
    final_report = combiner_agent.run()
    print("Final report is being saved...")
    final_report_file = open(output_path, "w")
    final_report_file.write(final_report)
    final_report_file.close()
    print("Final report is now saved!")


if __name__ == "__main__":
    fire.Fire(main)
