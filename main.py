import asyncio
import fire
from ASQ import ConsultingAgency  # Import the ConsultingAgency class from your module


async def run_consulting_agency(
    user_input: str,
    max_iter: int,
):
    """Run a consulting agency. Solve user problems."""
    agency = ConsultingAgency()

    await agency.run(user_input)


def main(
    user_input: str,
    max_iter: int = 5,
):
    """
    We are a consulting agency comprised of AI. By working with us,
    you are empowering a future filled with limitless possibilities.
    :param user_input: Your current problem or situation to be solved.
    :return:
    """
    asyncio.run(run_consulting_agency(user_input, max_iter))


if __name__ == "__main__":
    fire.Fire(main)
