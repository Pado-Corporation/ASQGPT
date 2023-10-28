import openai
from metagpt.config import CONFIG, PROJECT_ROOT
from metagpt.logs import logger
from metagpt.asq_agents.combiner import agent as Combiner
import os
import glob


def configurate() -> None:
    openai.api_key = CONFIG.openai_api_key


def read_search_reports(directory: str) -> None:
    os.chdir(f"{PROJECT_ROOT}/metagpt/asq_agents/combiner/test/{directory}/")
    files_content = {}
    for file in glob.glob("*.md"):
        if file != "toc.md":
            with open(file, "r", encoding="utf-8") as f:
                files_content[file] = f.read()
    return files_content


def read_toc(directory: str) -> None:
    with open(
        f"{PROJECT_ROOT}/metagpt/asq_agents/combiner/test/{directory}/toc.md", "r", encoding="utf-8"
    ) as f:
        return f.read()


def summarization_pipeline() -> None:
    search_reports = read_search_reports("documents")
    toc = read_toc("documents")
    print(toc)
    combiner_agent = Combiner.Agent(
        "The user wants to create a corporate analysis report on Microsoft to help with an investment decision.",
        toc,
        language="English",
    )
    for file_name, file_content in search_reports.items():
        logger.info(f"Research Report: {file_name}")
        combiner_agent.feed(file_content)
    final_report = combiner_agent.run()
    print("Final report is being saved...")
    final_report_file = open(
        f"{PROJECT_ROOT}/metagpt/asq_agents/combiner/test/outputs/final_report.md", "w"
    )
    final_report_file.write(final_report)
    final_report_file.close()
    print("Final report is now saved!")


if __name__ == "__main__":
    configurate()
    summarization_pipeline()
