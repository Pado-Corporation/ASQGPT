import openai
import utils.read

class Agent:
    def __init__(self, language: str= "Korean", model_type="gpt-4"):
        base_instruction = utils.read.instruction("summarizer")
        instruction = f"Respond using this language: {language}\n{base_instruction}"
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