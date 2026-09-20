from checker.alert_judgement import _exclude_market_holidays_and_weekends
from checker.constants import SECONDS_IN_DAY
from checker.constants import SECONDS_IN_HOUR
from tests.fixtures import MONDAY_MIDNIGHT
from tests.fixtures import REPLAY_TIMESTAMP
from tests.fixtures import SPOKE_COMPUTED_AT


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
