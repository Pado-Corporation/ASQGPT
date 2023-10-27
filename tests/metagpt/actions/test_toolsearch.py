import pytest
import asyncio
from metagpt.actions.toolsearch import ToolSelect, ToolUseSummary, ToolSetting
from metagpt.actions.webresearch import get_research_system_text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "Analyze Google's stock price over the last 5 years",
        "Find the cheapest flight tickets to Paris",
        "What's the weather like in New York?",
        "Find property prices in San Francisco",
        "Find a recipe for chocolate cake",
        "Find reviews for the movie Inception",
        "Compare iPhone 12 and iPhone 13",
    ],
)
async def test_toolselect_run(query, capsys):
    tool_select = ToolSelect()
    output = await tool_select.run(query)
    print(f"For query '{query}', the output is: {output}")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tool_type, topic",
    [
        ("Google Maps API", "Find restaurants in New York"),
        ("Google Shopping API", "Compare prices of iPhone 13"),
        ("Google Jobs API", "Software Engineer jobs in San Francisco"),
        ("Google News API", "Latest news on COVID-19"),
        ("Google Trends API", "Search trends on electric cars"),
        ("Google Finance STOCK API", "Research about Tesla stock."),
        ("Google Finance News and Financials API", "Research about tesla"),
        ("Walmart API", "Laptop prices at Walmart"),
        ("YouTube Search API", "Top trending videos"),
        (
            "Google Flight API",
            "Cheapest flights From korea to Paris, I'll leave korea end of 2023.",
        ),
        ("Google Event API", "Upcoming events in London"),
    ],
)
async def test_toolusesummary_run(tool_type, topic):
    tool_query = await ToolSetting(tool_type=tool_type).run(problem=topic)
    tool_query = tool_query[1]
    print(f"For tool '{tool_type}' and topic '{topic}', the output is: {tool_query}")
    system_prompt = get_research_system_text(topic, "en")
    tool_result = await ToolUseSummary(tool_type=tool_type).run(
        tool_query, topic, brief_search_num=20, detail_search_num=5, system_text=system_prompt
    )
    print(f"For tool '{tool_type}' and topic '{topic}', the output is: {tool_result}")
