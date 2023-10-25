import openai
import utils.read

class Aggregator:
    """
    Generates a comprehensive report from collected materials fed into the agent.
    """
    def __init__(self, model_type="gpt-4"):
        instruction = utils.read.instruction("aggregator")
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

    def generate(self) -> str:
        response = openai.ChatCompletion.create(
            model=self.model_type,
            messages=self.messages,
            temperature=0,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        response_message = response["choices"][0]["message"]
        return response_message["content"]

    def run(self) -> str:
        return self.generate()