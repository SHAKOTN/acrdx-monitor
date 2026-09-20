import json

from checker.backfill import backfill
from checker.constants import BACKFILL_STEP_SECONDS
from tests.fixtures import MONDAY_MIDNIGHT


def test_backfill_writes_one_history_line_per_step(patch_output_files_and_clock, patch_reads_ok):
    backfill(MONDAY_MIDNIGHT, MONDAY_MIDNIGHT + 2 * BACKFILL_STEP_SECONDS)

    lines = (patch_output_files_and_clock / "history.jsonl").read_text().splitlines()
    timestamps = [json.loads(line)["timestamp"] for line in lines]
    assert timestamps == [MONDAY_MIDNIGHT, MONDAY_MIDNIGHT + BACKFILL_STEP_SECONDS]


def test_backfill_end_before_start_writes_nothing(patch_output_files_and_clock, patch_reads_ok):
    backfill(MONDAY_MIDNIGHT, MONDAY_MIDNIGHT - 1)

    assert not (patch_output_files_and_clock / "history.jsonl").exists()
