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


async def main(language="en-us"):
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
            research_report = await role.run(assign["task"])
            logger.info(f"Research Report: {research_report}")
            summarizer_agent = Summarizer.Agent()
            research_summary = summarizer_agent.run(research_report)
            combiner_agent.feed(research_summary)
    final_report = combiner_agent.run()
    print("Final report is being saved...")
    final_report_file = open("example.md", "w")
    final_report_file.write(final_report)
    final_report_file.close()
    print("Final report is now saved!")


def report_parse(text):
    section_indices = [m.start() for m in re.finditer(r"\n## ", text)]

    # 각 섹션을 추출
    sections = [
        text[section_indices[i] : section_indices[i + 1]].strip()
        for i in range(len(section_indices) - 1)
    ]
    sections.append(text[section_indices[-1] :].strip())  # 마지막 섹션을 추가
    return sections


def upload_to_vectordb(split_corpus: list[str]):
    dataset = split_corpus

    embeddings = []

    for sentence in dataset:
        response = openai.Embedding.create(model="text-embedding-ada-002", input=[sentence])
        embeddings.append((sentence, response["data"][0]["embedding"], {}))

    # create vector store client

    # create a collection named 'sentences' with 1536 dimensional vectors (default dimension for text-embedding-ada-002)
    sentences = vx.get_or_create_collection(name="report_vectorsplit", dimension=1536)

    # upsert the embeddings into the 'sentences' collection
    sentences.upsert(records=embeddings)

    # create an index for the 'sentences' collection
    sentences.create_index()


def query_from_vectordb(query: str, result_num: int):
    sentences = vx.get_collection(name="report_vectorsplit", dimension=1536)
    # create an embedding for the query sentence
    response = openai.Embedding.create(model="text-embedding-ada-002", input=[query])
    query_embedding = response["data"][0]["embedding"]

    # query the 'sentences' collection for the most similar sentences
    results = sentences.query(data=query_embedding, limit=result_num, include_value=True)
    return results


if __name__ == "__main__":
    fire.Fire(main)
