from metagpt.roles.planningpm import PlanningPM
from metagpt.boss_agent.boss import Boss
from metagpt.roles.researcher import Researcher
from metagpt.remoteDB import init_db
import asyncio
import fire
import openai
from metagpt.config import CONFIG
import vecs

DB_CONNECTION = CONFIG.db_addr
vx = vecs.Client(DB_CONNECTION)


async def main(request="Create a report on climate change", context=None):
    init_db()
    openai.api_key = CONFIG.openai_api_key
    boss_agent = Boss()
    goal = boss_agent.run(request)
    pm_agent = PlanningPM()
    request.info(f"topic: \n {request}")
    assigned = asyncio.run(pm_agent.run(request))
    for assign in assigned:
        if assign["type"] == "Researcher":
            role = Researcher(language="eng")
            report_content = await role.run(assign["task"])
            report_parsed = report_parse(report_content)


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
