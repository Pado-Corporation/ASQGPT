#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/6/6 12:38
@Author  : alexanderwu
@File    : test_skill_manager.py
"""
from metagpt.actions import WritePRD, WriteTest
from metagpt.logs import logger
from metagpt.management.skill_manager import SkillManager


def test_skill_manager():
    manager = SkillManager()
    logger.info(manager._store)

    write_prd = WritePRD("WritePRD")
    write_prd.desc = "Write PRD based on user needs"
    write_test = WriteTest("WriteTest")
    write_test.desc = "Write Test based on project"
    manager.add_skill(write_prd)
    manager.add_skill(write_test)

    skill = manager.get_skill("WriteTest")
    logger.info(skill)

    rsp = manager.retrieve_skill("Write PRD")
    logger.info(rsp)
    assert rsp[0] == "WritePRD"

    rsp = manager.retrieve_skill("Write Testcase")
    logger.info(rsp)
    assert rsp[0] == "WriteTest"

    rsp = manager.retrieve_skill_scored("Write PRD")
    logger.info(rsp)


if __name__ == "__main__":
    manager = SkillManager()
    manager.generate_skill_desc(Action())
