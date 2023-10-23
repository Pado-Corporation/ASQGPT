#!/usr/bin/env python

import asyncio

from metagpt.roles.researcher import RESEARCH_PATH, Researcher
from metagpt.remoteDB import init_db


async def main():
    init_db()
    topic = "Search the trend of acne patch for to do market research"
    role = Researcher(language="eng")
    await role.run(topic)
    print(f"save report to {RESEARCH_PATH / f'{topic}.md'}.")


if __name__ == "__main__":
    asyncio.run(main())
