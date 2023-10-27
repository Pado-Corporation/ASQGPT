import openai
import sys
from metagpt.config import CONFIG
import utils.read

class Agent:
    """
    Investigates the user's true intention and 
    """
    def __init__(self, language="Korean"):
        instruction = utils.read.instruction("boss")
        if CONFIG.model_for_boss:
            self.model_type = CONFIG.model_for_boss
        else:
            self.model_type = "gpt-4"
        language_instruction = f"Respond using the following language: {language}\n" + instruction
        self.messages = [{"role": "system", "content": language_instruction}]

    def listen(self):
        """
        The agent waits and listens to the user's message.
        :return:
        """
        try:
            message = input("User: ").strip()
            if not message:
                self.listen()
            else:
                self.messages.append({"role": "user", "content": message})
        except KeyboardInterrupt:
            print("\nASQ: Good talk! I'll see you later :)")
            sys.exit(1)

    def speak(self):
        """
        The agent responds to the user's message.
        :return: True if B0$$ has reached the goal.
        """
        # Receive a chat completion object from the OpenAI API.
        response = openai.ChatCompletion.create(
            model=self.model_type,
            messages=self.messages,
            temperature=0,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        response_message = response["choices"][0]["message"]
        msg = response_message["content"]
        # Show the boss' response to the user.
        print(f"ASQ: {msg}")
        self.messages.append(response_message)

        return "[GOAL]" in msg, msg

    def conversation(self):
        """
        The agent has a conversation with the user.
        :return:
        """
        finished = False
        while not finished:
            self.listen()
            print("---")
            finished, msg = self.speak()
        return msg

    def run(self):
        """
        The agent starts to have a conversation.
        :return:
        """
        self.greetings()
        return self.conversation()
