import json

from checker.alert_judgement import _exclude_market_holidays_and_weekends
from checker.alert_judgement import _judge_if_compute_at_stale
from checker.alert_judgement import judge
from checker.constants import SECONDS_IN_DAY
from checker.constants import SECONDS_IN_HOUR
from tests.fixtures import AGE_AT_LIMIT_TIMESTAMP
from tests.fixtures import MONDAY_MIDNIGHT
from tests.fixtures import REPLAY_TIMESTAMP
from tests.fixtures import SPOKE_COMPUTED_AT
from tests.fixtures import write_run_file


def test_exclude_market_holidays_and_weekends_inside_one_weekday():
    monday_noon = MONDAY_MIDNIGHT + 12 * SECONDS_IN_HOUR
    assert _exclude_market_holidays_and_weekends(MONDAY_MIDNIGHT, monday_noon) == 12


def test_exclude_market_holidays_and_weekends_across_a_weekend():
    friday_noon = MONDAY_MIDNIGHT + 4 * SECONDS_IN_DAY + 12 * SECONDS_IN_HOUR
    next_monday_noon = friday_noon + 3 * SECONDS_IN_DAY
    assert _exclude_market_holidays_and_weekends(friday_noon, next_monday_noon) == 24


def test_exclude_market_holidays_and_weekends_inside_a_weekend():
    saturday_morning = MONDAY_MIDNIGHT + 5 * SECONDS_IN_DAY + 6 * SECONDS_IN_HOUR
    sunday_evening = MONDAY_MIDNIGHT + 6 * SECONDS_IN_DAY + 18 * SECONDS_IN_HOUR
    assert _exclude_market_holidays_and_weekends(saturday_morning, sunday_evening) == 0


def test_exclude_market_holidays_and_weekends_end_before_start():
    tuesday_midnight = MONDAY_MIDNIGHT + SECONDS_IN_DAY
    assert _exclude_market_holidays_and_weekends(tuesday_midnight, MONDAY_MIDNIGHT) == 0


def test_exclude_market_holidays_and_weekends_august_event():
    # Tuesday Aug 4 12:00 -> Monday Aug 10 12:00: 144 hours on the clock, 96 without the weekend
    assert _exclude_market_holidays_and_weekends(SPOKE_COMPUTED_AT, REPLAY_TIMESTAMP + 1) == 96


def test_judge_if_compute_at_stale_read_failed():
    verdict = _judge_if_compute_at_stale(None, REPLAY_TIMESTAMP)
    assert verdict == {
        "check": "spoke_price_age",
        "result": "no_verdict",
        "reason": "spoke read failed",
    }


def test_judge_if_compute_at_stale_fresh_price():
    verdict = _judge_if_compute_at_stale(SPOKE_COMPUTED_AT, SPOKE_COMPUTED_AT + SECONDS_IN_DAY)
    assert verdict == {
        "check": "spoke_price_age",
        "result": "ok",
        "age_hours": 24.0,
        "limit_hours": 84,
        "computed_at": SPOKE_COMPUTED_AT,
    }


def test_judge_if_compute_at_stale_exactly_at_limit():
    verdict = _judge_if_compute_at_stale(SPOKE_COMPUTED_AT, AGE_AT_LIMIT_TIMESTAMP)
    assert verdict["result"] == "ok"
    assert verdict["age_hours"] == 84.0


def test_judge_if_compute_at_stale_august_event():
    verdict = _judge_if_compute_at_stale(SPOKE_COMPUTED_AT, REPLAY_TIMESTAMP + 1)
    assert verdict == {
        "check": "spoke_price_age",
        "result": "alert",
        "age_hours": 96.0,
        "limit_hours": 84,
        "computed_at": SPOKE_COMPUTED_AT,
    }


def test_judge_august_event_is_alert(tmp_path):
    file_path = write_run_file(tmp_path, REPLAY_TIMESTAMP + 1, SPOKE_COMPUTED_AT, None)
    run = judge(file_path)
    assert run["overall"] == "alert"
    assert run["verdicts"] == [{
        "check": "spoke_price_age",
        "result": "alert",
        "age_hours": 96.0,
        "limit_hours": 84,
        "computed_at": SPOKE_COMPUTED_AT,
        "chain_id": 1,
    }]


def test_judge_fresh_price_is_ok(tmp_path):
    one_day_later = SPOKE_COMPUTED_AT + SECONDS_IN_DAY
    file_path = write_run_file(tmp_path, one_day_later, SPOKE_COMPUTED_AT, None)
    assert judge(file_path)["overall"] == "ok"


def test_judge_failed_read_is_no_verdict(tmp_path):
    file_path = write_run_file(tmp_path, REPLAY_TIMESTAMP, None, "ConnectionError: <RPC_URL>")
    run = judge(file_path)
    assert run["overall"] == "no_verdict"
    assert run["verdicts"] == [{
        "check": "spoke_price_age",
        "result": "no_verdict",
        "reason": "spoke read failed: ConnectionError: <RPC_URL>",
        "chain_id": 1,
    }]


def test_judge_writes_the_run_back_to_the_file(tmp_path):
    file_path = write_run_file(tmp_path, REPLAY_TIMESTAMP + 1, SPOKE_COMPUTED_AT, None)
    run = judge(file_path)
    assert json.loads(open(file_path).read()) == run
