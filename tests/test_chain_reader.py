import json

import pytest
from web3 import Web3

from checker import chain_reader
from checker.chain_reader import _create_web3_transport
from checker.chain_reader import _find_adjacent_block
from checker.chain_reader import _find_block_to_read
from checker.chain_reader import _read_chronicle_data
from checker.chain_reader import _read_spoke_data
from checker.chain_reader import _redact_rpc_urls
from checker.chain_reader import main_collector
from checker.constants import ERROR_TEXT_LIMIT
from checker.constants import ETHEREUM
from checker.constants import POOL_ID
from checker.constants import RPC_TIMEOUT_SECONDS
from checker.constants import SC_ID
from tests.fixtures import CHRONICLE_PRICE
from tests.fixtures import FAKE_RPC_URL
from tests.fixtures import LATEST_BLOCK
from tests.fixtures import REPLAY_BLOCK
from tests.fixtures import REPLAY_TIMESTAMP
from tests.fixtures import SPOKE_COMPUTED_AT
from tests.fixtures import SPOKE_PRICE
from tests.fixtures import WALL_CLOCK


def test_create_web3_transport_uses_url_from_environment(monkeypatch):
    monkeypatch.setenv("MAINNET_RPC_URL", FAKE_RPC_URL)

    web3 = _create_web3_transport(ETHEREUM)

    assert isinstance(web3, Web3)
    assert web3.provider.endpoint_uri == FAKE_RPC_URL


def test_create_web3_transport_sets_request_timeout(monkeypatch):
    monkeypatch.setenv("MAINNET_RPC_URL", FAKE_RPC_URL)

    web3 = _create_web3_transport(ETHEREUM)

    assert web3.provider.get_request_kwargs()["timeout"] == RPC_TIMEOUT_SECONDS


def test_create_web3_transport_with_missing_variable(monkeypatch):
    monkeypatch.delenv("MAINNET_RPC_URL", raising=False)

    with pytest.raises(ValueError) as err:
        _create_web3_transport(ETHEREUM)

    assert err.value.args[0] == "Environment variable MAINNET_RPC_URL is not set"


def test_create_web3_transport_with_empty_variable(monkeypatch):
    monkeypatch.setenv("MAINNET_RPC_URL", "")

    with pytest.raises(ValueError) as err:
        _create_web3_transport(ETHEREUM)

    assert err.value.args[0] == "Environment variable MAINNET_RPC_URL is not set"


def test_create_web3_transport_with_unknown_chain():
    with pytest.raises(ValueError) as err:
        _create_web3_transport(999)

    assert err.value.args[0] == "Unknown chain id 999"


def test_find_adjacent_block_at_exact_block_time(patch_web3_with_fake_chain):
    assert _find_adjacent_block(1060, ETHEREUM) == 5


def test_find_adjacent_block_between_two_blocks_returns_earlier_one(patch_web3_with_fake_chain):
    assert _find_adjacent_block(1059, ETHEREUM) == 4
    assert _find_adjacent_block(1071, ETHEREUM) == 5


def test_find_adjacent_block_at_first_block(patch_web3_with_fake_chain):
    assert _find_adjacent_block(1000, ETHEREUM) == 0
    assert _find_adjacent_block(1011, ETHEREUM) == 0


def test_find_adjacent_block_at_or_after_latest_block(patch_web3_with_fake_chain):
    assert _find_adjacent_block(1120, ETHEREUM) == 10
    assert _find_adjacent_block(5000, ETHEREUM) == 10


def test_find_adjacent_block_every_second_of_the_chain(patch_web3_with_fake_chain):
    for timestamp in range(1000, 1121):
        assert _find_adjacent_block(timestamp, ETHEREUM) == (timestamp - 1000) // 12


def test_find_adjacent_block_before_first_block(patch_web3_with_fake_chain):
    with pytest.raises(ValueError) as err:
        _find_adjacent_block(999, ETHEREUM)

    assert err.value.args[0] == "Timestamp 999 is before the first block of chain 1"


def test_find_adjacent_block_with_missing_variable(monkeypatch):
    monkeypatch.delenv("MAINNET_RPC_URL", raising=False)

    with pytest.raises(ValueError) as err:
        _find_adjacent_block(1060, ETHEREUM)

    assert err.value.args[0] == "Environment variable MAINNET_RPC_URL is not set"


def test_find_block_to_read_live_returns_latest_block(patch_output_files_and_clock):
    assert _find_block_to_read(ETHEREUM, None) == (LATEST_BLOCK, None)


def test_find_block_to_read_replay_returns_block_of_timestamp(patch_output_files_and_clock):
    assert _find_block_to_read(ETHEREUM, REPLAY_TIMESTAMP) == (REPLAY_BLOCK, None)


def test_find_block_to_read_with_missing_variable(monkeypatch):
    monkeypatch.delenv("MAINNET_RPC_URL", raising=False)

    assert _find_block_to_read(ETHEREUM, None) == (
        None, "ValueError: Environment variable MAINNET_RPC_URL is not set"
    )


def test_read_spoke_data_with_read_ok(fake_spoke_web3):
    assert _read_spoke_data(ETHEREUM, (REPLAY_BLOCK, None)) == {
        "chain_id": 1,
        "name": "ethereum",
        "status": "ok",
        "block": REPLAY_BLOCK,
        "price": "1020232466949343944",
        "computed_at": SPOKE_COMPUTED_AT,
        "error": None,
    }


def test_read_spoke_data_reads_both_values_at_given_block(fake_spoke_web3):
    _read_spoke_data(ETHEREUM, (REPLAY_BLOCK, None))

    spoke_functions = fake_spoke_web3.eth.contract.return_value.functions
    spoke_functions.pricePoolPerShare.assert_called_once_with(POOL_ID, SC_ID, False)
    spoke_functions.markersPricePoolPerShare.assert_called_once_with(POOL_ID, SC_ID)
    spoke_functions.pricePoolPerShare.return_value.call.assert_called_once_with(
        block_identifier=REPLAY_BLOCK
    )
    spoke_functions.markersPricePoolPerShare.return_value.call.assert_called_once_with(
        block_identifier=REPLAY_BLOCK
    )


def test_read_spoke_data_with_price_never_set(fake_spoke_web3):
    spoke_functions = fake_spoke_web3.eth.contract.return_value.functions
    spoke_functions.pricePoolPerShare.return_value.call.return_value = 0
    spoke_functions.markersPricePoolPerShare.return_value.call.return_value = (0, 0, 0)

    reading = _read_spoke_data(ETHEREUM, (REPLAY_BLOCK, None))

    assert reading["status"] == "failed"
    assert reading["error"] == "ValueError: Spoke on chain 1 has no price for the share class"


def test_read_spoke_data_with_rpc_error(fake_spoke_web3, monkeypatch):
    monkeypatch.setenv("MAINNET_RPC_URL", FAKE_RPC_URL)
    spoke_functions = fake_spoke_web3.eth.contract.return_value.functions
    spoke_functions.pricePoolPerShare.return_value.call.side_effect = ConnectionError(
        f"cannot connect to {FAKE_RPC_URL}"
    )

    assert _read_spoke_data(ETHEREUM, (REPLAY_BLOCK, None)) == {
        "chain_id": 1,
        "name": "ethereum",
        "status": "failed",
        "block": None,
        "price": None,
        "computed_at": None,
        "error": "ConnectionError: cannot connect to <RPC_URL>",
    }


def test_read_spoke_data_with_missing_variable(monkeypatch):
    monkeypatch.delenv("MAINNET_RPC_URL", raising=False)

    reading = _read_spoke_data(ETHEREUM, (REPLAY_BLOCK, None))

    assert reading["status"] == "failed"
    assert reading["error"] == "ValueError: Environment variable MAINNET_RPC_URL is not set"


def test_read_spoke_data_with_block_not_found():
    reading = _read_spoke_data(ETHEREUM, (None, "ValueError: no block"))

    assert reading["status"] == "failed"
    assert reading["price"] is None
    assert reading["error"] == "ValueError: no block"


def test_read_chronicle_data_with_read_ok(fake_chronicle_web3):
    assert _read_chronicle_data((REPLAY_BLOCK, None)) == {
        "status": "ok",
        "block": REPLAY_BLOCK,
        "price": "1021003405586530000",
        "error": None,
    }
    oracle_functions = fake_chronicle_web3.eth.contract.return_value.functions
    oracle_functions.read.return_value.call.assert_called_once_with(block_identifier=REPLAY_BLOCK)


def test_read_chronicle_data_with_revert(fake_chronicle_web3):
    oracle_functions = fake_chronicle_web3.eth.contract.return_value.functions
    oracle_functions.read.return_value.call.side_effect = ValueError("execution reverted")

    assert _read_chronicle_data((REPLAY_BLOCK, None)) == {
        "status": "failed",
        "block": None,
        "price": None,
        "error": "ValueError: execution reverted",
    }


def test_read_chronicle_data_with_missing_variable(monkeypatch):
    monkeypatch.delenv("MAINNET_RPC_URL", raising=False)

    reading = _read_chronicle_data((REPLAY_BLOCK, None))

    assert reading["status"] == "failed"
    assert reading["error"] == "ValueError: Environment variable MAINNET_RPC_URL is not set"


def test_read_chronicle_data_with_block_not_found():
    assert _read_chronicle_data((None, "ValueError: no block")) == {
        "status": "failed",
        "block": None,
        "price": None,
        "error": "ValueError: no block",
    }


def test_redact_rpc_urls_replaces_variable_value_and_any_url(monkeypatch):
    monkeypatch.setenv("MAINNET_RPC_URL", "rpc.invalid/secret-key")
    error = ValueError("rpc.invalid/secret-key failed, also wss://other.invalid/key and text")

    assert _redact_rpc_urls(error) == "ValueError: <RPC_URL> failed, also <RPC_URL> and text"


def test_redact_rpc_urls_cuts_long_text():
    assert len(_redact_rpc_urls(ValueError("x" * 1000))) == ERROR_TEXT_LIMIT


def test_main_collector_live_writes_latest_file(patch_output_files_and_clock, patch_reads_ok):
    file_path = main_collector()

    assert file_path == str(patch_output_files_and_clock / "latest.json")
    run = json.loads(open(file_path).read())
    assert run["run_at"] == WALL_CLOCK
    assert run["timestamp"] == WALL_CLOCK
    assert run["mode"] == "live"
    assert run["readings"]["chronicle"]["block"] == LATEST_BLOCK
    assert [reading["block"] for reading in run["readings"]["chains"]] == [LATEST_BLOCK]


def test_main_collector_replay_writes_replay_file(patch_output_files_and_clock, patch_reads_ok):
    file_path = main_collector(REPLAY_TIMESTAMP)

    assert file_path == str(patch_output_files_and_clock / "replay" / "1786363199.json")
    run = json.loads(open(file_path).read())
    assert run["timestamp"] == REPLAY_TIMESTAMP
    assert run["mode"] == "replay"
    assert run["readings"]["chronicle"]["block"] == REPLAY_BLOCK


def test_main_collector_finds_block_once_per_chain(
        patch_output_files_and_clock, patch_reads_ok, monkeypatch
):
    searched = []
    monkeypatch.setattr(
        chain_reader, "_find_adjacent_block",
        lambda timestamp, chain_id: searched.append(chain_id) or REPLAY_BLOCK,
    )

    main_collector(REPLAY_TIMESTAMP)

    assert searched == [ETHEREUM]


def test_main_collector_is_not_judged_yet(patch_output_files_and_clock, patch_reads_ok):
    run = json.loads(open(main_collector()).read())

    assert run["verdicts"] == []
    assert run["overall"] == "no_verdict"


def test_main_collector_with_failed_reads_still_writes_file(
        patch_output_files_and_clock, patch_rpc_down
):
    run = json.loads(open(main_collector()).read())

    assert run["readings"]["chronicle"]["status"] == "failed"
    assert run["readings"]["chains"][0]["status"] == "failed"
    assert FAKE_RPC_URL not in json.dumps(run)
