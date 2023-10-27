import openai
import utils.read
from metagpt.logs import logger

class Agent:
    def __init__(self, goal: str, toc: str, language: str= "Korean", model_type: str ="gpt-4") -> None:
        """Generates a comprehensive report from collected materials fed into the agent.


        Args:
            goal (str): Human user's goal that needs to be achieved
            toc (str): Table of contents for the final report
            model_type (str, optional): The language model for the agent. Defaults to "gpt-4".
        """
        base_instruction = utils.read.instruction("combiner")
        instruction = f"Respond using this language: {language}\n{base_instruction}"
        self.model_type = model_type
        self.messages = [
            {
                "role": "system",
                "content": instruction
            }
        ]

    def feed(self, summary) -> None:
        self.messages.append({
            "role": "user",
            "content": summary
        })

    def combine(self) -> str:
        logger.info("Combiner / ASQ is generating final report...")
        response = openai.ChatCompletion.create(
            model=self.model_type,
            messages=self.messages,
            temperature=0,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        logger.info("Combiner / ASQ generated the final report")
        response_message = response["choices"][0]["message"]
        return response_message["content"]

    def run(self) -> str:
        return self.combine()