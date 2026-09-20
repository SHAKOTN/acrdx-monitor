"""
Module for judging the readings.

Every judgement takes readings and returns a "verdict" dict in the format of
../data/contract.json, with "result" = ok | no_verdict | alert (constants.RESULT_*).
A judgement whose reading has status "failed" returns no_verdict, never ok.
The judgements do not read the chain, the files or the wall clock.
"""


def judge(file_path: str) -> dict:
    """
    Main runner that ingests the json written by chain_reader.main_collector.
    Processes data, fills in "verdicts" and "overall" (the worst result), writes the file back
    and returns the run.
    The clock of every judgement is the "timestamp" field of the file.
    """
    pass

def _judge_if_price_divergence(spoke_reading: dict, chronicle_reading: dict) -> dict:
    """
    Compares Chronicle last reported price with price per share (check id spoke_chronicle_divergence).
    Mainnet price from Spoke is used as the primary reference.
    Returns a verdict: alert if the divergence in percent is over
    SPOKE_CHRONICLE_DIVERGENCE_LIMIT_PCT, ok if not, no_verdict if either reading failed.
    Fields: check, chain_id, result, divergence_pct, limit_pct | reason.
    """
    pass

def _judge_if_chain_price_divergence(mainnet_reading: dict, chain_reading: dict) -> dict:
    """
    Compares Mainnet price from Spoke to the price of one other chain (check id cross_chain_price_mismatch).
    Returns a verdict: alert if there is a mismatch, ok if not, no_verdict if either reading failed.
    """
    pass

def _judge_if_compute_at_stale(chain_reading: dict, timestamp: int) -> dict:
    """
    Compares the age of computed_at at `timestamp`, weekend and market holiday hours excluded,
    with SPOKE_PRICE_AGE_LIMIT_HOURS from constants.py (check id spoke_price_age).
    Returns a verdict: alert if the age is over the limit, ok if not, no_verdict if the reading failed.
    Fields: check, chain_id, result, age_hours, limit_hours, computed_at, since | reason.
    "since" is the moment the age crossed the limit.
    """
    pass

def _exclude_market_holidays_and_weekends(start: int, end: int) -> float:
    """
    Hours between two unix timestamps (UTC), with Saturdays, Sundays and
    US market holidays (list in constants.py) excluded.
    """
    pass
