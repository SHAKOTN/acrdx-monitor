"""
Module for reading on chain data
"""

from weakref import WeakKeyDictionary

from typing_extensions import Optional


def main_collector(timestamp: Optional[int] = None) -> None:
    """
    Main collector function that reads on chain data and stores it in json format in ../data/
    Parameters:
        timestamp (Optional[int]): Timestamp to read on chain data from. If None, reads the latest time.
    """
    # TODO:
        # Read _read_chronicle_price_per_share
        # Read _read_spoke_price_per_share
        # Store results in ../data/
        # Format json output as this format:
            # {
            #     "timestamp": ,
            #     "chronicle_price_per_share": ,
            #     "chains": [
            #         {
            #             "chain_id": ,
            #             "spoke_price_per_share":
            #             "computedAt": ,
            #         }
            #     ]
            # }

def _read_spoke_price_per_share(chain_id: int, timestamp: Optional[int] = None) -> [float, int]:
    """
    Read the price per share of ACRDX store in the Spoke Contract.

    Args:
        chain_id (int): The chain ID of the Spoke Contract.
        timestamp (Optional[int]): Timestamp to read on chain data from. If None, reads the latest time.


    Returns:
        float: The price per share of ACRDX.
        int:
    """
    # Fill in constants.py with ACRDX address (same on all chains):
        # - Mapping of chain_id: Spoke Contract address
        # - Mapping: chain_id: scId
        # - Mapping: chain_id: poolId
    # Then read the price per share from the Spoke Contract and computedAt param from
    # markersPricePoolPerShare function
    # function markersPricePoolPerShare(PoolId poolId, ShareClassId scId)
    #        external
    #        view
    #        returns (uint64 computedAt, uint64 maxAge, uint64 validUntil)

def _read_chronicle_price_per_share(timestamp: Optional[int] = None) -> float:
    """
    Read the price per share of ACRDX from the Chronicle contract.
    """
    # TODO: Add chronicle contract address to constants.py
    # Read the price per share from the Chronicle contract

def _create_web3_transport(chain_id: int) -> Web3:
    """
    Create a Web3 transport object.
    """
    # TODO: Install the Web3 provider and return it as a Web3 object based on the chain_id
    # Use <CHAIN>_RPC_URL from environment variables to create the transport

def _find_adjacent_block(timestamp: int, chain_id: int) -> int:
    """
    Find the adjacent block to the given timestamp on the given chain.
    """
