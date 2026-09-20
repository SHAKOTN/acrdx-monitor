import pytest
from web3 import Web3

from checker.chain_reader import _create_web3_transport
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
