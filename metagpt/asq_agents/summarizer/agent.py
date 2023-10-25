import openai
import utils.read

class Summarizer:
    def __init__(self, model_type="gpt-3.5-turbo"):
        instruction = utils.read.instruction("summarizer")
        self.model_type = model_type
        self.messages = [
            {
                "role": "system",
                "content": instruction
            }
        ]

    def feed(self, report) -> None:
        self.messages.append({
            "role": "user",
            "content": report
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

    def run(self, report) -> str:
        self.feed(report)
        return self.generate()