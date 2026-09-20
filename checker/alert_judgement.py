"""
Module for judging the readings.

Every judgement takes plain values (a price or a time; None means "the read failed")
and returns a "verdict" dict in the format of ../data/contract.json,
with "result" = ok | no_verdict | alert (constants.RESULT_*).
A judgement that gets None returns no_verdict, never ok.
judge() takes the values out of the readings and adds "chain_id" and the read error to the verdict.
The judgements do not read the chain, the files or the wall clock.
"""

import json
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any

from checker.constants import CHECK_SPOKE_CHRONICLE_DIVERGENCE
from checker.constants import CHECK_SPOKE_PRICE_AGE
from checker.constants import ETHEREUM
from checker.constants import RESULT_ALERT
from checker.constants import RESULT_NO_VERDICT
from checker.constants import RESULT_OK
from checker.constants import RESULT_SEVERITY
from checker.constants import SATURDAY
from checker.constants import SECONDS_IN_DAY
from checker.constants import SECONDS_IN_HOUR
from checker.constants import SPOKE_CHRONICLE_DIVERGENCE_LIMIT_PCT
from checker.constants import SPOKE_PRICE_AGE_LIMIT_HOURS


def judge(file_path: str) -> dict[str, Any]:
    """
    Main runner that ingests the json written by chain_reader.main_collector.
    Processes data, fills in "verdicts" and "overall" (the worst result), writes the file back
    and returns the run.
    The clock of every judgement is the "timestamp" field of the file.
    """
    run = json.loads(Path(file_path).read_text())
    chronicle = run["readings"]["chronicle"]
    chronicle_price = int(chronicle["price"]) if chronicle["price"] else None
    verdicts = []
    for reading in run["readings"]["chains"]:
        spoke_price = int(reading["price"]) if reading["price"] else None
        chain_verdicts = [_judge_if_compute_at_stale(reading["computed_at"], run["timestamp"])]
        if reading["chain_id"] == ETHEREUM:
            chain_verdicts.append(_judge_if_price_divergence(spoke_price, chronicle_price))
        for verdict in chain_verdicts:
            verdict["chain_id"] = reading["chain_id"]
            if "reason" in verdict:
                verdict["reason"] += f": {reading['error'] or chronicle['error']}"
        verdicts += chain_verdicts
    run["verdicts"] = verdicts
    run["overall"] = max(
        (verdict["result"] for verdict in verdicts),
        key=RESULT_SEVERITY.index,
        default=RESULT_NO_VERDICT,
    )
    Path(file_path).write_text(json.dumps(run, indent=2) + "\n")
    return run

def _judge_if_price_divergence(
        spoke_price: int | None,
        chronicle_price: int | None,
) -> dict[str, int | float | str | None]:
    """
    Compares Chronicle last reported price with price per share (check id spoke_chronicle_divergence).
    Mainnet price from Spoke is used as the primary reference.
    Returns a verdict: alert if the divergence in percent is over
    SPOKE_CHRONICLE_DIVERGENCE_LIMIT_PCT, ok if not, no_verdict if either price is None.
    Prices are raw integers with 18 decimals.
    Fields: check, result, divergence_pct, limit_pct | reason.
    """
    if not spoke_price or not chronicle_price:
        return {
            "check": CHECK_SPOKE_CHRONICLE_DIVERGENCE,
            "result": RESULT_NO_VERDICT,
            "reason": "spoke or chronicle read failed",
        }
    divergence_pct = abs(chronicle_price - spoke_price) / spoke_price * 100
    over_limit = divergence_pct > SPOKE_CHRONICLE_DIVERGENCE_LIMIT_PCT
    return {
        "check": CHECK_SPOKE_CHRONICLE_DIVERGENCE,
        "result": RESULT_ALERT if over_limit else RESULT_OK,
        "divergence_pct": round(divergence_pct, 4),
        "limit_pct": SPOKE_CHRONICLE_DIVERGENCE_LIMIT_PCT,
    }

def _judge_if_chain_price_divergence(
        mainnet_price: int | None,
        chain_price: int | None,
) -> dict[str, int | float | str | None]:
    """
    Compares Mainnet price from Spoke to the price of one other chain (check id cross_chain_price_mismatch).
    Returns a verdict: alert if there is a mismatch, ok if not, no_verdict if either price is None.
    """
    pass

def _judge_if_compute_at_stale(
        computed_at: int | None,
        timestamp: int,
) -> dict[str, int | float | str | None]:
    """
    Compares the age of computed_at at `timestamp`, weekend hours excluded,
    with SPOKE_PRICE_AGE_LIMIT_HOURS from constants.py (check id spoke_price_age).
    Returns a verdict: alert if the age is over the limit, ok if not, no_verdict if computed_at is None.
    Fields: check, result, age_hours, limit_hours, computed_at | reason.
    """
    if computed_at is None:
        return {
            "check": CHECK_SPOKE_PRICE_AGE,
            "result": RESULT_NO_VERDICT,
            "reason": "spoke read failed",
        }
    age_hours = _exclude_market_holidays_and_weekends(computed_at, timestamp)
    return {
        "check": CHECK_SPOKE_PRICE_AGE,
        "result": RESULT_ALERT if age_hours > SPOKE_PRICE_AGE_LIMIT_HOURS else RESULT_OK,
        "age_hours": round(age_hours, 2),
        "limit_hours": SPOKE_PRICE_AGE_LIMIT_HOURS,
        "computed_at": computed_at,
    }

def _exclude_market_holidays_and_weekends(start: int, end: int) -> float:
    """
    Hours between two unix timestamps (UTC), with Saturdays and Sundays excluded.
    Returns 0 if end is not after start.
    """
    weekday_seconds = 0
    day_start = start - start % SECONDS_IN_DAY
    while day_start < end:
        day_end = day_start + SECONDS_IN_DAY
        if datetime.fromtimestamp(day_start, tz=timezone.utc).weekday() < SATURDAY:
            weekday_seconds += min(end, day_end) - max(start, day_start)
        day_start = day_end
    return weekday_seconds / SECONDS_IN_HOUR
