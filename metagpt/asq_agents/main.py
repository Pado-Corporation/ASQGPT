from boss.agent import Boss
import utils.read

def greetings():
    welcome_text = utils.read.welcome()
    print(welcome_text)

def main():
    boss_agent = Boss()
    boss_agent.run()

if __name__ == '__main__':
    greetings()
    main()
