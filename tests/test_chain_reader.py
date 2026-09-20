from unittest.mock import MagicMock

import pytest
from web3 import Web3

from checker import chain_reader
from checker.chain_reader import _create_web3_transport
from checker.chain_reader import _find_adjacent_block
from checker.constants import ETHEREUM
from checker.constants import RPC_TIMEOUT_SECONDS

FAKE_RPC_URL = "https://rpc.invalid/secret-key"


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
