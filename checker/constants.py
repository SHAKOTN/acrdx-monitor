# Chain IDs
ETHEREUM = 1
MONAD = 143

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

CHAIN_DATA = {
    ETHEREUM: {
        "name": "ethereum",
        "rpc_env": "MAINNET_RPC_URL",
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

# Read status: the "status" field of a reading.
STATUS_OK = "ok"
STATUS_FAILED = "failed"

# Limits
# Age of the Spoke's computedAt with weekend and US market holiday hours removed.
# Calibrated by replay, Apr 3 -> Sep 18 2026: worst normal age 79 h, August event 204 h.
SPOKE_PRICE_AGE_LIMIT_HOURS = 84
# Chronicle against Spoke, in percent. First value, not calibrated by replay.
SPOKE_CHRONICLE_DIVERGENCE_LIMIT_PCT = 0.15
