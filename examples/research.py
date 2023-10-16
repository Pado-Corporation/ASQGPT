#!/usr/bin/env python

import asyncio

from metagpt.roles.researcher import RESEARCH_PATH, Researcher


async def main():
    topic = "부산에 대한 관광 정보를 특히 탐색하고, 부산의 주요 관광지를 추천한다. 이 때 추천해야하는 대상은 부산의 해산물을 좋아하는 사람이며, 부산의 밤문화에 대해서도 관심이 많다."
    role = Researcher(language="kor")
    await role.run(topic)
    print(f"save report to {RESEARCH_PATH / f'{topic}.md'}.")


if __name__ == "__main__":
    asyncio.run(main())
