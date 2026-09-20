# acrdx-monitor

Live page: https://shakotn.github.io/acrdx-monitor/

## What is this?

A monitor for the on-chain price of the ACRDX token (`0x9477724bb54ad5417de8baff29e59df3fb4da74f`),
a Centrifuge V3 share token.

Every 12 hours it reads the price from the Centrifuge `Spoke` contract on Ethereum, Plume, Optimism and Base,
and from the Chronicle oracle on Ethereum. Then it runs two checks:

- **Time since the last price update.** Alert when the `Spoke` price is older than 84 hours, weekends not counted.
- **Difference between Spoke and Chronicle price.** Alert when the two prices differ by more than 0.15%.

Each check gives `ok`, `alert` or `no_verdict`. A read that fails gives `no_verdict`, never `ok`:
"could not check" is not "fine". The page shows "Monitor not running" when the last run is older than 20 hours.

The history is prefilled from 2026-08-01: one run every 12 hours, each read at the block of that time.
The live runs come after it, also every 12 hours.

- `checker/`: Python package that reads the chains, judges the readings and writes `data/`.
- `data/`: `latest.json` (the last run), `history.jsonl` (one run per line), `contract.json` (the format).
- `dashboard/`: static page that reads `data/`. No build step.
- `.github/workflows/monitor.yml`: one run every 12 hours; commits `data/` and publishes the page.

## How to run locally

Needs Docker. Create `.env` with one archive RPC URL per chain:

```
MAINNET_RPC_URL=
PLUME_RPC_URL=
OPTIMISM_RPC_URL=
BASE_RPC_URL=
```

```bash
docker compose build
docker compose run --rm checker python -m checker.main              # one live run → data/latest.json
docker compose run --rm checker python -m checker.main 1786363200   # one run at a past time (unix seconds)
docker compose run --rm checker python -m checker.backfill          # one run every 12 hours from 2026-08-01
docker compose up -d dashboard                                      # page on http://localhost:8080
docker compose up -d scheduler                                      # one live run every 12 hours
```

## How to run tests

```bash
docker compose run --rm checker pytest -q
```
