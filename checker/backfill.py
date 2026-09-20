import time

from checker.constants import BACKFILL_START_TIMESTAMP
from checker.constants import BACKFILL_STEP_SECONDS
from checker.main import main


def backfill(start: int, end: int) -> None:
    """
    Runs the checker for every BACKFILL_STEP_SECONDS from start (included) to end (excluded).
    Every run goes to the history file, as any other run.
    """
    for timestamp in range(start, end, BACKFILL_STEP_SECONDS):
        main(timestamp)


if __name__ == "__main__":
    backfill(BACKFILL_START_TIMESTAMP, int(time.time()))
