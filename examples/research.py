#!/usr/bin/env python

import asyncio

from metagpt.roles.researcher import RESEARCH_PATH, Researcher


async def main():
    topic = "Search the internet for data and reports on current market trends, consumer perceptions, competitive landscape, and more for gel type toothpaste"
    role = Researcher(language="eng")
    await role.run(topic)
    print(f"save report to {RESEARCH_PATH / f'{topic}.md'}.")


if __name__ == "__main__":
    asyncio.run(main())
