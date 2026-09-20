def judge(file_path: str):
    """
    Main runner that ingests data from ../data/
    Processes data, and fills in alert fields.
    """
    pass

def _judge_if_price_divergence() -> bool:
    """
    Compares Chronicle last reported price with price per share and returns True if they diverge, False otherwise.
    Mainnet price from Spoke is used as the primary reference.
    """
    pass

def _judge_if_chain_price_divergence() -> bool:
    """
    Compares Mainnet price from Spoke to all other chain prices and
    returns True if there is a mismatch, False otherwise.
    """
    pass

def _judge_if_compute_at_stale() -> bool:
    """
    Compares the compute_at with calibrated MAX_COMPUTE_AT param from constants.py
    Returns False if compute_at is within the calibrated range, True otherwise.
    """
    pass

def _exclude_market_holidays_and_weekends():
    """
    Excludes market holidays from the alert judgement.
    """
    pass
