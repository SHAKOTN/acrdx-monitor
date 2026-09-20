from typing import Optional


def main(timestamp: Optional[int] = None):
    """
    Main entry point for the checker runner.
    Parameters:
    - timestamp: Optional[int] - The timestamp to check. If not provided, the latest timestamp will be checked.
    """

if __name__ == "__main__":
    # Pass timestamp (replay mode); no argument means live mode
    import sys
    main(timestamp=int(sys.argv[1]) if len(sys.argv) > 1 else None)
