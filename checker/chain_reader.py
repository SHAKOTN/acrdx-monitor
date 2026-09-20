"""
Module for reading on chain data.

A read returns plain values as a tuple and raises on any failure.
main_collector is the only place that catches: it turns a result into a "reading" with
status "ok", and an error into a "reading" with status "failed", an error text
(RPC URLs redacted) and null values. Format: ../data/contract.json.
"""

import os

from web3 import Web3

from checker.constants import CHAIN_DATA
from checker.constants import RPC_TIMEOUT_SECONDS


def main_collector(timestamp: int | None = None) -> str:
    """
    Main collector function that reads on chain data and stores it in json format in ../data/
    Parameters:
        timestamp (int | None): Timestamp to read on chain data from. If None, reads the latest time.
    Returns:
        str: path of the json file that was written (input of alert_judgement.judge).
    """
    # TODO:
        # Read _read_chronicle_price_per_share
        # Read _read_spoke_price_per_share for every chain in constants.CHAIN_DATA
        # Catch the error of each read on its own: one failed read must not stop the others
        # Store results in ../data/ in the format of ../data/contract.json:
        #   run_at, timestamp, mode, readings.chronicle, readings.chains[]
        # Live mode (timestamp is None): "timestamp" is the time of the latest Ethereum block.

def _read_spoke_price_per_share(
        chain_id: int,
        timestamp: int | None = None,
) -> tuple[int, int, int]:
    """
    Read the price per share of ACRDX stored in the Spoke Contract, and its computedAt.

    Args:
        chain_id (int): The chain ID of the Spoke Contract.
        timestamp (int | None): Timestamp to read on chain data from. If None, reads the latest time.

    Returns:
        tuple[int, int, int]: (block, price, computed_at)
            block: the block that both values were read at.
            price: the raw uint128 (18 decimals), never a float.
            computed_at: unix time of the price.
    Raises on any failure (missing RPC variable, RPC error, revert).
    """
    # Read pricePoolPerShare(poolId, scId, false) and computedAt from
    # markersPricePoolPerShare function, both at the same block
    # function markersPricePoolPerShare(PoolId poolId, ShareClassId scId)
    #        external
    #        view
    #        returns (uint64 computedAt, uint64 maxAge, uint64 validUntil)

def _read_chronicle_price_per_share(
        timestamp: int | None = None,
) -> tuple[int, int]:
    """
    Read the price per share of ACRDX from the Chronicle contract (read(), plain eth_call
    at a pinned block; address(0) is on the oracle's allow-list).

    Returns:
        tuple[int, int]: (block, price); price is the raw uint256 (18 decimals).
    Raises on any failure (missing RPC variable, RPC error, revert).
    """

def _create_web3_transport(chain_id: int) -> Web3:
    """
    Create a Web3 object for the chain. The RPC URL comes from the environment variable
    named in constants.CHAIN_DATA[chain_id]["rpc_env"].
    Raises ValueError if the chain is unknown or the variable is missing;
    main_collector turns that into a "failed" reading. The URL is never put in a message.
    """
    if chain_id not in CHAIN_DATA:
        raise ValueError(f"Unknown chain id {chain_id}")
    rpc_env = CHAIN_DATA[chain_id]["rpc_env"]
    rpc_url = os.getenv(rpc_env)
    if not rpc_url:
        raise ValueError(f"Environment variable {rpc_env} is not set")
    return Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": RPC_TIMEOUT_SECONDS}))

def _find_adjacent_block(timestamp: int, chain_id: int) -> int:
    """
    Find the last block at or before the given timestamp on the given chain.
    Never returns a later block: that would read the future.
    Raises if the chain cannot serve it; main_collector turns that into a "failed" reading.
    """
