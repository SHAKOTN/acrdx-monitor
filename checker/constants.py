import tempfile
from pathlib import Path

# Chain IDs. Monad (143) also has ACRDX but is not read: no archive RPC for the replay.
ETHEREUM = 1
OPTIMISM = 10
BASE = 8453
PLUME = 98866

# ACRDX share token. Same address on Ethereum, Base and Plume;
# Optimism and Monad use 0x2fabf1c784b8583d63c00c5c9c0377d8cf1a3245.
ACRDX_ADDRESS = "0x9477724bb54ad5417de8baff29e59df3fb4da74f"
CHRONICLE_MAINNET_ORACLE_ADDRESS = "0x9a3bF392f86acd1b1EC07d026B326302eAED7488"

# poolId and scId identify ACRDX on the hub and are the same on every chain.
# The Spoke has the same address on every chain.
POOL_ID = 281474976710664
SC_ID = "0x00010000000000080000000000000001"
SPOKE_ADDRESS = "0xEC3582fcDc34078a4B7a8c75a5a3AE46f48525aB"

PRICE_DECIMALS = 18

# Output files. Live mode writes LATEST_FILE; replay mode writes REPLAY_FILE, a temporary file.
# Every judged run, live or replay, is appended to HISTORY_FILE as one JSON line.
DATA_DIRECTORY = Path(__file__).parent.parent / "data"
LATEST_FILE = DATA_DIRECTORY / "latest.json"
HISTORY_FILE = DATA_DIRECTORY / "history.jsonl"
REPLAY_FILE = Path(tempfile.gettempdir()) / "checker_replay_run.json"

# Longest error text that is stored in a reading
ERROR_TEXT_LIMIT = 300

# The Chronicle read function that the checker calls
CHRONICLE_ABI = [
    {
        "name": "read",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "value", "type": "uint256"}],
    },
]

# The two Spoke read functions that the checker calls
SPOKE_ABI = [
    {
        "name": "pricePoolPerShare",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {"name": "poolId", "type": "uint64"},
            {"name": "scId", "type": "bytes16"},
            {"name": "checkValidity", "type": "bool"},
        ],
        "outputs": [{"name": "price", "type": "uint128"}],
    },
    {
        "name": "markersPricePoolPerShare",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {"name": "poolId", "type": "uint64"},
            {"name": "scId", "type": "bytes16"},
        ],
        "outputs": [
            {"name": "computedAt", "type": "uint64"},
            {"name": "maxAge", "type": "uint64"},
            {"name": "validUntil", "type": "uint64"},
        ],
    },
]

# Seconds before an RPC request gives up. A timeout gives a "failed" reading.
RPC_TIMEOUT_SECONDS = 20

CHAIN_DATA = {
    ETHEREUM: {
        "name": "ethereum",
        "rpc_env": "MAINNET_RPC_URL",
        "poolId": POOL_ID,
        "scId": SC_ID,
        "spoke_contract": SPOKE_ADDRESS,
    },
    PLUME: {
        "name": "plume",
        "rpc_env": "PLUME_RPC_URL",
        "poolId": POOL_ID,
        "scId": SC_ID,
        "spoke_contract": SPOKE_ADDRESS,
    },
    OPTIMISM: {
        "name": "optimism",
        "rpc_env": "OPTIMISM_RPC_URL",
        "poolId": POOL_ID,
        "scId": SC_ID,
        "spoke_contract": SPOKE_ADDRESS,
    },
    BASE: {
        "name": "base",
        "rpc_env": "BASE_RPC_URL",
        "poolId": POOL_ID,
        "scId": SC_ID,
        "spoke_contract": SPOKE_ADDRESS,
    },
}

# Check ids: the "check" field of a verdict in the output JSON.
CHECK_SPOKE_PRICE_AGE = "spoke_price_age"
CHECK_SPOKE_CHRONICLE_DIVERGENCE = "spoke_chronicle_divergence"
CHECK_CROSS_CHAIN_PRICE_MISMATCH = "cross_chain_price_mismatch"  # when other chains are added
CHECK_SHARE_SUPPLY_MISMATCH = "share_supply_mismatch"  # reserved

# Results: the "result" field of a verdict. "overall" is the worst one, in this order.
RESULT_OK = "ok"
RESULT_NO_VERDICT = "no_verdict"
RESULT_ALERT = "alert"
RESULT_SEVERITY = [RESULT_OK, RESULT_NO_VERDICT, RESULT_ALERT]

# Run mode: the "mode" field of a run.
MODE_LIVE = "live"
MODE_REPLAY = "replay"

# Read status: the "status" field of a reading.
STATUS_OK = "ok"
STATUS_FAILED = "failed"

# Time
SECONDS_IN_HOUR = 3600
SECONDS_IN_DAY = 86400
SATURDAY = 5  # datetime.weekday(): Monday is 0, Saturday is 5, Sunday is 6

# Backfill of the history: one run every 12 hours, from 2026-08-01 00:00 UTC until now.
# Scheduled live runs are every hour.
BACKFILL_START_TIMESTAMP = 1785542400
BACKFILL_STEP_SECONDS = 12 * SECONDS_IN_HOUR

# Limits
# Age of the Spoke's computedAt with weekend hours removed.
# Replay, Apr 3 -> Sep 18 2026: the August event alerts from Aug 10 00:15 UTC.
# Known cost: 2 false alerts after a holiday (Jun 23, Sep 8); a limit of 104 h removes them.
SPOKE_PRICE_AGE_LIMIT_HOURS = 84
# Chronicle against Spoke, in percent. First value, not calibrated by replay.
SPOKE_CHRONICLE_DIVERGENCE_LIMIT_PCT = 0.15
