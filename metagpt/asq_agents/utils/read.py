from metagpt.config import PROJECT_ROOT

def instruction(agent_name):
    """
    Reads the instruction prompt for the given agent name.
    :param agent_name: The name of the agent for the instruction prompt
    :type agent_name: str
    :return: The prompt
    """
    with open(f"{PROJECT_ROOT}/metagpt/asq_agents/{agent_name}/instruction.md", "r") as file:
        return file.read()

def welcome():
    with open(f"{PROJECT_ROOT}/metagpt/asq_agents/welcome.txt", "r") as file:
        return file.read()