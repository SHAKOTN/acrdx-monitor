"""
Module for reading on chain data.

main_collector finds one block for each chain, reads the Spoke and the Chronicle oracle
at that block and writes the json file (format: ../data/contract.json).
The _read_*_data functions never raise: an error gives a "reading" with status "failed",
an error text (RPC URLs redacted) and null values.
"""

import json
import os
import re
import time

from web3 import Web3

from checker.constants import CHAIN_DATA
from checker.constants import CHRONICLE_ABI
from checker.constants import CHRONICLE_MAINNET_ORACLE_ADDRESS
from checker.constants import ERROR_TEXT_LIMIT
from checker.constants import ETHEREUM
from checker.constants import LATEST_FILE
from checker.constants import MODE_LIVE
from checker.constants import MODE_REPLAY
from checker.constants import REPLAY_FILE
from checker.constants import RESULT_NO_VERDICT
from checker.constants import RPC_TIMEOUT_SECONDS
from checker.constants import SPOKE_ABI
from checker.constants import STATUS_FAILED
from checker.constants import STATUS_OK


def main_collector(timestamp: int | None = None) -> str:
    """
    Main collector function that reads on chain data and stores it in json format in ../data/
    Parameters:
        timestamp (int | None): Timestamp to read on chain data from. If None, reads the latest time.
    Returns:
        str: path of the json file that was written (input of alert_judgement.judge).
    """
    # Find the block of every chain once, here. Every read below gets a block, not a timestamp.
    blocks = {chain_id: _find_block_to_read(chain_id, timestamp) for chain_id in CHAIN_DATA}
    run_at = int(time.time())

    run = {
        "run_at": run_at,
        "timestamp": timestamp or run_at,
        "mode": MODE_LIVE if timestamp is None else MODE_REPLAY,
        "readings": {
            "chronicle": _read_chronicle_data(blocks[ETHEREUM]),
            "chains": [_read_spoke_data(chain_id, blocks[chain_id]) for chain_id in CHAIN_DATA],
        },
        # alert_judgement.judge fills these in. Until then the run says "not judged", never "ok".
        "verdicts": [],
        "overall": RESULT_NO_VERDICT,
    }

    file_path = LATEST_FILE if timestamp is None else REPLAY_FILE
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(run, indent=2) + "\n")
    return str(file_path)


def _find_block_to_read(chain_id: int, timestamp: int | None) -> tuple[int | None, str | None]:
    """
    The block that every read of this chain uses, as (block, error).
    Live: the latest block. Replay: the last block at or before the timestamp.
    Never raises: on an error the block is None and the error is the redacted text.
    """
    try:
        if timestamp is None:
            return _create_web3_transport(chain_id).eth.block_number, None
        return _find_adjacent_block(timestamp, chain_id), None
    except Exception as error:
        return None, _redact_rpc_urls(error)


def _read_spoke_data(
        chain_id: int,
        block_and_error: tuple[int | None, str | None],
) -> dict[str, int | str | None]:
    """
    Read the price per share of ACRDX and its computedAt from the Spoke of one chain,
    both at the same block, and return the reading for the json file.
    block_and_error is the result of _find_block_to_read for this chain.
    Never raises: an error gives status "failed" with the redacted error text.
    """
    block, block_error = block_and_error
    chain = CHAIN_DATA[chain_id]
    reading = {
        "chain_id": chain_id,
        "name": chain["name"],
        "status": STATUS_FAILED,
        "block": None,
        "price": None,
        "computed_at": None,
        "error": block_error,
    }
    if block is None:
        return reading
    try:
        web3 = _create_web3_transport(chain_id)
        spoke = web3.eth.contract(address=chain["spoke_contract"], abi=SPOKE_ABI)
        # checkValidity is False: the call must return the stored price, not revert on an old one
        price = spoke.functions.pricePoolPerShare(
            chain["poolId"], chain["scId"], False
        ).call(block_identifier=block)
        computed_at, _max_age, _valid_until = spoke.functions.markersPricePoolPerShare(
            chain["poolId"], chain["scId"]
        ).call(block_identifier=block)
        if computed_at == 0:
            raise ValueError(f"Spoke on chain {chain_id} has no price for the share class")
    except Exception as error:
        reading["error"] = _redact_rpc_urls(error)
        return reading
    reading["status"] = STATUS_OK
    reading["block"] = block
    reading["price"] = str(price)
    reading["computed_at"] = computed_at
    return reading


def _read_chronicle_data(
        block_and_error: tuple[int | None, str | None],
) -> dict[str, int | str | None]:
    """
    Read the price per share of ACRDX from the Chronicle oracle (read(), plain eth_call at a
    pinned Ethereum block) and return the reading for the json file.
    block_and_error is the result of _find_block_to_read for Ethereum.
    Never raises: an error gives status "failed" with the redacted error text.
    """
    ethereum_block, block_error = block_and_error
    reading = {"status": STATUS_FAILED, "block": None, "price": None, "error": block_error}
    if ethereum_block is None:
        return reading
    try:
        web3 = _create_web3_transport(ETHEREUM)
        oracle = web3.eth.contract(address=CHRONICLE_MAINNET_ORACLE_ADDRESS, abi=CHRONICLE_ABI)
        # No "from" address: the call comes from address(0), which the oracle allows to read
        price = oracle.functions.read().call(block_identifier=ethereum_block)
    except Exception as error:
        reading["error"] = _redact_rpc_urls(error)
        return reading
    reading["status"] = STATUS_OK
    reading["block"] = ethereum_block
    reading["price"] = str(price)
    return reading


def _redact_rpc_urls(error: Exception) -> str:
    """
    Error text that is safe to publish: the error type and message, with every URL
    and every RPC variable value replaced, cut to ERROR_TEXT_LIMIT characters.
    """
    text = f"{type(error).__name__}: {error}"
    for chain in CHAIN_DATA.values():
        rpc_url = os.getenv(chain["rpc_env"])
        if rpc_url:
            text = text.replace(rpc_url, "<RPC_URL>")
    text = re.sub(r"(https?|wss?)://[^\s'\"]+", "<RPC_URL>", text)
    return text[:ERROR_TEXT_LIMIT]


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
    web3 = _create_web3_transport(chain_id)
    latest_block = web3.eth.get_block("latest")
    if timestamp >= latest_block["timestamp"]:
        return latest_block["number"]
    if timestamp < web3.eth.get_block(0)["timestamp"]:
        raise ValueError(f"Timestamp {timestamp} is before the first block of chain {chain_id}")

    # Binary search. Always true: time of block `low` <= timestamp < time of block `high`
    low = 0
    high = latest_block["number"]
    while high - low > 1:
        middle = (low + high) // 2
        if web3.eth.get_block(middle)["timestamp"] <= timestamp:
            low = middle
        else:
            high = middle
    return low
