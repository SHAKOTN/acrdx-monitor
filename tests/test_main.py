import json

from checker.main import main
from tests.fixtures import REPLAY_TIMESTAMP


def test_main_replay_of_august_event_is_alert(patch_output_files_and_clock, patch_reads_ok):
    main(REPLAY_TIMESTAMP)

    file_path = patch_output_files_and_clock / "replay" / f"{REPLAY_TIMESTAMP}.json"
    run = json.loads(file_path.read_text())
    assert run["overall"] == "alert"
    assert run["verdicts"][0]["check"] == "spoke_price_age"


def test_main_with_rpc_down_is_no_verdict(patch_output_files_and_clock, patch_rpc_down):
    main()

    run = json.loads((patch_output_files_and_clock / "latest.json").read_text())
    assert run["overall"] == "no_verdict"
    assert "<RPC_URL>" in run["verdicts"][0]["reason"]
