import json

from checker.main import main
from tests.fixtures import REPLAY_TIMESTAMP


def test_main_replay_of_august_event_is_alert(patch_output_files_and_clock, patch_reads_ok):
    main(REPLAY_TIMESTAMP)

    file_path = patch_output_files_and_clock / "replay.json"
    run = json.loads(file_path.read_text())
    assert run["overall"] == "alert"
    assert run["verdicts"][0]["check"] == "spoke_price_age"


def test_main_with_rpc_down_is_no_verdict(patch_output_files_and_clock, patch_rpc_down):
    main()

    run = json.loads((patch_output_files_and_clock / "latest.json").read_text())
    assert run["overall"] == "no_verdict"
    assert "<RPC_URL>" in run["verdicts"][0]["reason"]


def test_main_appends_every_run_to_the_history(patch_output_files_and_clock, patch_reads_ok):
    main(REPLAY_TIMESTAMP)
    main()

    lines = (patch_output_files_and_clock / "history.jsonl").read_text().splitlines()
    latest_run = json.loads((patch_output_files_and_clock / "latest.json").read_text())
    assert [json.loads(line)["mode"] for line in lines] == ["replay", "live"]
    assert json.loads(lines[1]) == latest_run
