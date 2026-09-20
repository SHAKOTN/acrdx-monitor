"""
Constants and fixtures for all tests. Test files hold only the tests.
conftest.py loads this module, so every test can ask for a fixture by name.
"""
from unittest.mock import MagicMock

import pytest

from checker import chain_reader

FAKE_RPC_URL = "https://rpc.invalid/secret-key"

# Values of the mainnet Spoke at block 25724454 (2026-08-10)
SPOKE_PRICE = 1020232466949343944
SPOKE_COMPUTED_AT = 1785844800
MAX_UINT64 = 2**64 - 1


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
    Fake Web3 whose latest block is 500 and whose Spoke returns the values above.
    """
    fake_web3 = MagicMock()
    fake_web3.eth.block_number = 500
    spoke_functions = fake_web3.eth.contract.return_value.functions
    spoke_functions.pricePoolPerShare.return_value.call.return_value = SPOKE_PRICE
    spoke_functions.markersPricePoolPerShare.return_value.call.return_value = (
        SPOKE_COMPUTED_AT, MAX_UINT64, MAX_UINT64
    )
    monkeypatch.setattr(chain_reader, "_create_web3_transport", lambda chain_id: fake_web3)
    return fake_web3
