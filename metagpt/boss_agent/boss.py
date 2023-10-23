import os
import openai
import sys
from metagpt.config import CONFIG


openai.api_key = CONFIG.openai_api_key


class Boss:
    def __init__(self, request, model_type="gpt-4"):
        self.model_type = model_type
        self.messages = [
            {
                "role": "system",
                "content": "You are a friendly consultant that has a task oriented dialogue with the user. Follow these rules:\n- Find what the user wants to achieve by asking under ten questions.\n- One question must be asked for each step.\n- Filter out irrelevant information regarding the goal.\n- If you find the goal, print it in this format: [GOAL] The user wants to ...\n- If the user does not cooperate with finding the goal, end the conversation and print [GOAL] N/A.",
            },
            {"role": "user", "content": request},
        ]

    def listen(self):
        try:
            message = input("User: ").strip()
            if not message:
                self.listen()
            else:
                self.messages.append({"role": "user", "content": message})
        except KeyboardInterrupt:
            print("\nASQ: Good talk! I'll see you later :)")
            sys.exit(1)

    def check_completion(self, message):
        if "[GOAL]" in message:
            sys.exit()

    def speak(self):
        response = openai.ChatCompletion.create(
            model=self.model_type,
            messages=self.messages,
            temperature=0,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        response_message = response["choices"][0]["message"]
        print(f'ASQ: {response_message["content"]}')
        self.check_completion(response_message["content"])
        self.messages.append(response_message)

    def conversation(self):
        self.speak()
        self.listen()
        self.conversation()

    def run(self):
        self.conversation()
