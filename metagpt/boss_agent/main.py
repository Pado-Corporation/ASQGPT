import argparse
from boss import Boss


def main(request):
    boss_agent = Boss(request)
    boss_agent.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Listening to what the user wants to get done.")
    parser.add_argument('request', type=str, help='User request')
    args = parser.parse_args()
    main(args.request)
