import json

from checker.alert_judgement import judge
from checker.chain_reader import main_collector
from checker.constants import HISTORY_FILE


def main(timestamp: int | None = None) -> None:
    """
    Main entry point for the checker runner: reads the chain, judges the readings,
    appends the run to the history file as one JSON line and prints the overall result.
    Parameters:
    - timestamp: int | None - The timestamp to check. If not provided, the latest time is checked.
    """
    file_path = main_collector(timestamp)
    run = judge(file_path)
    with HISTORY_FILE.open("a") as history_file:
        history_file.write(json.dumps(run) + "\n")
    print(f"{run['mode']} run written to {file_path}: {run['overall']}")


if __name__ == "__main__":
    # Pass timestamp (replay mode); no argument means live mode
    import sys
    main(timestamp=int(sys.argv[1]) if len(sys.argv) > 1 else None)
