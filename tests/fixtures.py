"""
Constants and fixtures for all tests. Test files hold only the tests.
conftest.py loads this module, so every test can ask for a fixture by name.
"""
import json
from unittest.mock import MagicMock

import pytest

from checker import chain_reader

FAKE_RPC_URL = "https://rpc.invalid/secret-key"

# Values of the mainnet Spoke at block 25724454 (2026-08-10)
SPOKE_PRICE = 1020232466949343944
SPOKE_COMPUTED_AT = 1785844800
MAX_UINT64 = 2**64 - 1
CHRONICLE_PRICE = 1021003405586530000
REPLAY_TIMESTAMP = 1786363199
REPLAY_BLOCK = 25724454
LATEST_BLOCK = 26018270
WALL_CLOCK = 1789901843

# Monday 2026-08-03 00:00 UTC. SPOKE_COMPUTED_AT is Tuesday 2026-08-04 12:00 UTC
# and REPLAY_TIMESTAMP is one second before Monday 2026-08-10 12:00 UTC.
MONDAY_MIDNIGHT = 1785715200
# Monday 2026-08-10 00:00 UTC: the age of SPOKE_COMPUTED_AT is exactly 84 weekday hours
AGE_AT_LIMIT_TIMESTAMP = 1786320000


def write_run_file(directory, timestamp, computed_at, error):
    """
    Write a run file as main_collector does, with one Ethereum reading, and return its path.
    """
    run = {
        "run_at": WALL_CLOCK,
        "timestamp": timestamp,
        "mode": "replay",
        "readings": {
            "chronicle": {"status": "ok", "block": REPLAY_BLOCK, "price": str(CHRONICLE_PRICE),
                          "error": None},
            "chains": [{
                "chain_id": 1,
                "name": "ethereum",
                "status": "failed" if error else "ok",
                "block": None if error else REPLAY_BLOCK,
                "price": None if error else str(SPOKE_PRICE),
                "computed_at": computed_at,
                "error": error,
            }],
        },
        "verdicts": [],
        "overall": "no_verdict",
    }
    file_path = directory / "run.json"
    file_path.write_text(json.dumps(run))
    return str(file_path)


def fake_get_block(block_identifier):
    """
    Fake chain of 11 blocks. Block n has the time 1000 + 12 * n, so the latest block is 10 at 1120.
    """
    number = 10 if block_identifier == "latest" else block_identifier
    return {"number": number, "timestamp": 1000 + 12 * number}


@pytest.fixture
def patch_web3_with_fake_chain(monkeypatch):
    fake_web3 = MagicMock()
    fake_web3.eth.get_block = fake_get_block
    monkeypatch.setattr(chain_reader, "_create_web3_transport", lambda chain_id: fake_web3)


@pytest.fixture
def fake_spoke_web3(monkeypatch):
    """
    Fake Web3 whose Spoke returns the values above.
    """
    fake_web3 = MagicMock()
    spoke_functions = fake_web3.eth.contract.return_value.functions
    spoke_functions.pricePoolPerShare.return_value.call.return_value = SPOKE_PRICE
    spoke_functions.markersPricePoolPerShare.return_value.call.return_value = (
        SPOKE_COMPUTED_AT, MAX_UINT64, MAX_UINT64
    )
    monkeypatch.setattr(chain_reader, "_create_web3_transport", lambda chain_id: fake_web3)
    return fake_web3


@pytest.fixture
def fake_chronicle_web3(monkeypatch):
    """
    Fake Web3 whose Chronicle oracle returns CHRONICLE_PRICE.
    """
    fake_web3 = MagicMock()
    fake_web3.eth.contract.return_value.functions.read.return_value.call.return_value = (
        CHRONICLE_PRICE
    )
    monkeypatch.setattr(chain_reader, "_create_web3_transport", lambda chain_id: fake_web3)
    return fake_web3


@pytest.fixture
def patch_reads_ok(monkeypatch):
    """
    Both reads succeed with the values of block REPLAY_BLOCK.
    """
    monkeypatch.setattr(
        chain_reader, "_read_spoke_data",
        lambda chain_id, block_and_error: {
            "chain_id": chain_id, "name": "ethereum", "status": "ok",
            "block": block_and_error[0], "price": str(SPOKE_PRICE),
            "computed_at": SPOKE_COMPUTED_AT, "error": None,
        },
    )
    monkeypatch.setattr(
        chain_reader, "_read_chronicle_data",
        lambda block_and_error: {
            "status": "ok", "block": block_and_error[0], "price": str(CHRONICLE_PRICE), "error": None
        },
    )


@pytest.fixture
def patch_rpc_down(monkeypatch):
    """
    Every RPC connection fails with an error text that holds the RPC URL.
    """
    def raise_connection_error(chain_id):
        raise ConnectionError(f"cannot connect to {FAKE_RPC_URL}")

    monkeypatch.setenv("MAINNET_RPC_URL", FAKE_RPC_URL)
    monkeypatch.setattr(chain_reader, "_create_web3_transport", raise_connection_error)


@pytest.fixture
def patch_output_files_and_clock(monkeypatch, tmp_path):
    """
    Output goes to a temporary directory. The wall clock is WALL_CLOCK. The latest block is
    LATEST_BLOCK. The block of any replay time is REPLAY_BLOCK.
    """
    fake_web3 = MagicMock()
    fake_web3.eth.block_number = LATEST_BLOCK
    monkeypatch.setattr(
        chain_reader, "_find_adjacent_block", lambda timestamp, chain_id: REPLAY_BLOCK
    )
    monkeypatch.setattr(chain_reader, "_create_web3_transport", lambda chain_id: fake_web3)
    monkeypatch.setattr(chain_reader, "LATEST_FILE", tmp_path / "latest.json")
    monkeypatch.setattr(chain_reader, "REPLAY_DIRECTORY", tmp_path / "replay")
    monkeypatch.setattr(chain_reader.time, "time", lambda: WALL_CLOCK)
    return tmp_path
