import pytest
from web3 import Web3

from checker import chain_reader
from checker.chain_reader import _create_web3_transport
from checker.chain_reader import _find_adjacent_block
from checker.chain_reader import _read_spoke_price_per_share
from checker.constants import ETHEREUM
from checker.constants import POOL_ID
from checker.constants import RPC_TIMEOUT_SECONDS
from checker.constants import SC_ID
from tests.fixtures import FAKE_RPC_URL
from tests.fixtures import SPOKE_COMPUTED_AT
from tests.fixtures import SPOKE_PRICE


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


def test_read_spoke_price_per_share_live_reads_latest_block(fake_spoke_web3):
    assert _read_spoke_price_per_share(ETHEREUM) == (500, SPOKE_PRICE, SPOKE_COMPUTED_AT)


def test_read_spoke_price_per_share_replay_reads_block_of_timestamp(fake_spoke_web3, monkeypatch):
    monkeypatch.setattr(chain_reader, "_find_adjacent_block", lambda timestamp, chain_id: 123)

    assert _read_spoke_price_per_share(ETHEREUM, timestamp=1786363199) == (
        123, SPOKE_PRICE, SPOKE_COMPUTED_AT
    )


def test_read_spoke_price_per_share_reads_both_values_at_same_block(fake_spoke_web3):
    _read_spoke_price_per_share(ETHEREUM)

    spoke_functions = fake_spoke_web3.eth.contract.return_value.functions
    spoke_functions.pricePoolPerShare.assert_called_once_with(POOL_ID, SC_ID, False)
    spoke_functions.markersPricePoolPerShare.assert_called_once_with(POOL_ID, SC_ID)
    spoke_functions.pricePoolPerShare.return_value.call.assert_called_once_with(
        block_identifier=500
    )
    spoke_functions.markersPricePoolPerShare.return_value.call.assert_called_once_with(
        block_identifier=500
    )


def test_read_spoke_price_per_share_with_price_never_set(fake_spoke_web3):
    spoke_functions = fake_spoke_web3.eth.contract.return_value.functions
    spoke_functions.pricePoolPerShare.return_value.call.return_value = 0
    spoke_functions.markersPricePoolPerShare.return_value.call.return_value = (0, 0, 0)

    with pytest.raises(ValueError) as err:
        _read_spoke_price_per_share(ETHEREUM)

    assert err.value.args[0] == "Spoke on chain 1 has no price for the share class"


def test_read_spoke_price_per_share_with_rpc_error(fake_spoke_web3):
    spoke_functions = fake_spoke_web3.eth.contract.return_value.functions
    spoke_functions.pricePoolPerShare.return_value.call.side_effect = ConnectionError("rpc down")

    with pytest.raises(ConnectionError):
        _read_spoke_price_per_share(ETHEREUM)


def test_read_spoke_price_per_share_with_missing_variable(monkeypatch):
    monkeypatch.delenv("MAINNET_RPC_URL", raising=False)

    with pytest.raises(ValueError) as err:
        _read_spoke_price_per_share(ETHEREUM)

    assert err.value.args[0] == "Environment variable MAINNET_RPC_URL is not set"
