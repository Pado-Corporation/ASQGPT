from pathlib import Path
from random import random
from tempfile import TemporaryDirectory

import pytest

from metagpt.roles import researcher


async def mock_llm_ask(self, prompt: str, system_msgs):
    if "Please provide up to 2 necessary keywords" in prompt:
        return '["dataiku", "datarobot"]'
    elif "Provide up to 4 queries related to your research topic" in prompt:
        return (
            '["Dataiku machine learning platform", "DataRobot AI platform comparison", '
            '"Dataiku vs DataRobot features", "Dataiku and DataRobot use cases"]'
        )
    elif "sort the remaining search results" in prompt:
        return "[1,2]"
    elif "Not relevant." in prompt:
        return "Not relevant" if random() > 0.5 else prompt[-100:]
    elif "provide a detailed research report" in prompt:
        return f"# Research Report\n## Introduction\n{prompt}"
    return ""


@pytest.mark.asyncio
async def test_researcher():
    with TemporaryDirectory() as dirname:
        topic = "dataiku vs. datarobot"
        mocker.patch("metagpt.provider.base_gpt_api.BaseGPTAPI.aask", mock_llm_ask)
        researcher.RESEARCH_PATH = Path(dirname)
        await researcher.Researcher().run(topic)
        assert (
            (researcher.RESEARCH_PATH / f"{topic}.md").read_text().startswith("# Research Report")
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "Artificial Intelligence in Healthcare",
        "Blockchain in Supply Chain Management",
        "Impact of Climate Change on Marine Ecosystems",
    ],
)
async def test_researcher_withexample(query, capsys):
    role = researcher.Researcher(query, language="English")
    output = await role.run(query)
    print(f"For query '{query}', the output is: {output}")
