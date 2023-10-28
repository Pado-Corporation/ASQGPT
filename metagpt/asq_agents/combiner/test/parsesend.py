import os
import openai
from metagpt.config import CONFIG
import vecs
from vecs import Collection
import logging
import re

DB_CONNECTION = CONFIG.db_addr
vx = vecs.Client(DB_CONNECTION)
openai.api_key = CONFIG.openai_api_key


def upload_to_vectordb(split_corpus: list[str], workflow_name: str):
    dataset = split_corpus
    print(split_corpus)

    embeddings = []

    for sentence in dataset:
        response = openai.Embedding.create(model="text-embedding-ada-002", input=[sentence])
        embeddings.append((sentence, response["data"][0]["embedding"], {"workflow": workflow_name}))

    # create vector store client

    # create a collection named 'sentences' with 1536 dimensional vectors (default dimension for text-embedding-ada-002)
    sentences = vx.get_or_create_collection(name="new_pipelinetest", dimension=1536)

    # upsert the embeddings into the 'sentences' collection
    sentences.upsert(records=embeddings)

    # create an index for the 'sentences' collection
    sentences.create_index()


def query_from_vectordb(collection: Collection, query: str, result_num: int, workflow_name: str):
    # create an embedding for the query sentence
    response = openai.Embedding.create(model="text-embedding-ada-002", input=[query])
    query_embedding = response["data"][0]["embedding"]

    # query the 'sentences' collection for the most similar sentences
    results = collection.query(
        data=query_embedding,
        limit=result_num,
        include_value=True,
        include_metadata=True,
        filters={"workflow": {"$eq": workflow_name}},
    )
    return results


def report_parse(text, seperator="\n\n"):
    section_indices = [m.start() for m in re.finditer(r"\n## ", text)]

    # 각 섹션을 추출
    sections = [
        text[section_indices[i] : section_indices[i + 1]].strip()
        for i in range(len(section_indices) - 1)
    ]
    sections.append(text[section_indices[-1] :].strip())  # 마지막 섹션을 추가
    return sections


def get_file_location():
    return os.path.abspath(__file__)


def main():
    folder_path = "/Users/parkgyutae/dev/Pado/ASQGPT/metagpt/asq_agents/combiner/test/documents"

    # for filename in os.listdir(folder_path):
    #     file_path = os.path.join(folder_path, filename)
    #     if os.path.isfile(file_path):
    #         with open(file_path, "r") as f:
    #             content = f.read()
    #             contents = content.split("\n\n")
    #             upload_to_vectordb(contents, workflow_name="test")

    questions = [
        "When was Microsoft founded?",
        "Who were the founders?",
        "What was Microsoft's initial goal or vision?",
        "If your boss appreciates creative thinking, could you tell me about the creative strategies or ideas Microsoft used to break into the market in its early days?",
        "What product lineup did Microsoft have initially, and how has it evolved?",
        "How did Microsoft grow through significant events or partnerships?",
        "What is the company's culture or philosophy, and how has it influenced the company's growth?",
        "How did Microsoft differentiate itself from competitors?",
        "Who were the key individuals or events that contributed to the company's early growth?",
        "What technology played a significant role in determining Microsoft's early success?",
    ]
    a = []
    collection = vx.get_or_create_collection(name="new_pipelinetest", dimension=1536)
    for question in questions:
        q = {}
        queryResult = query_from_vectordb(
            collection, query=question, result_num=2, workflow_name="test"
        )
        q["query"] = question
        q["queryResult"] = queryResult
        print(queryResult)
        a.append(q)
    print(a)
    vx.disconnect()


if __name__ == "__main__":
    main()
