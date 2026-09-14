# Executor Contract

The paper trader terminates every money-touching action at one seam: an
**executor** that receives an order and returns a fill. This file is the
contract your `external` executor must satisfy.

**Boundary:** this project never constructs or broadcasts an on-chain
transaction. When `strategy.json` sets `executor.type = "external"`, the tool
spawns your `command`, writes one order JSON object to its **stdin**, and reads
one fill JSON object from its **stdout**. Everything on the other side of that
pipe — RPC endpoints, calldata, signing, keys, whether it hits an anvil fork or
mainnet — is yours, authored and operated entirely outside this codebase.

## Invocation

- The tool runs `command` with no arguments, `shell: false`.
- It writes the order as a single line of JSON to stdin, then closes stdin.
- Your process writes exactly one JSON object to stdout and exits 0.
- **Timeout** (`executor.timeout_ms`, default 30000ms), **nonzero exit**,
  **unparseable stdout**, or a **mismatched `order_id`** are all treated as a
  failed fill. The tool never throws; a failed sell escalates slippage and
  retries next cycle, a failed buy simply records the rejection.
- stdout is parsed as data only. Nothing your wrapper prints is executed or
  interpreted as instructions.

## Order (tool → wrapper stdin)

```json
{
  "order_id": "o_1726340000000_3_a1b2",
  "side": "buy",
  "token_address": "0x16391c40e85fb2246a2c8c17bfa2594c5d3ef84b",
  "ticker": "GRASS",
  "amount_usd": 10,
  "token_amount": null,
  "ref_price_usd": 0.0063,
  "max_slippage_pct": 5,
  "deadline_s": 1800
}
```

| field | meaning |
|---|---|
| `order_id` | opaque; echo it back verbatim |
| `side` | `"buy"` or `"sell"` |
| `token_address` | the token to buy/sell (quote asset is the chain's wrapped native) |
| `amount_usd` | BUY only: USD notional to spend (null on sells) |
| `token_amount` | SELL only: tokens to sell (null on buys) |
| `ref_price_usd` | the tool's current mark; derive min-out from it |
| `max_slippage_pct` | reject/return failed if the realized price is worse than this |
| `deadline_s` | swap deadline in seconds (add to `now` for the router deadline arg) |

Min-out you should enforce:
- BUY: `min_tokens = (amount_usd / ref_price_usd) × (1 − max_slippage_pct/100)`
- SELL: `min_usd  = (token_amount × ref_price_usd) × (1 − max_slippage_pct/100)`

## Fill (wrapper stdout → tool)

```json
{
  "order_id": "o_1726340000000_3_a1b2",
  "status": "filled",
  "fill_price_usd": 0.00641,
  "token_amount": 1554.2,
  "usd_value": 9.97,
  "fee_usd": 0.03,
  "tx_ref": "0x… (optional)",
  "error": null
}
```

| field | meaning |
|---|---|
| `status` | `"filled"` or `"failed"` |
| `fill_price_usd` | realized per-token USD price |
| `token_amount` | tokens actually bought (buy) or sold (sell) |
| `usd_value` | BUY: USD spent; SELL: USD received (after fees) |
| `fee_usd` | fees paid (optional, default 0) |
| `tx_ref` | optional tx hash / reference for your own audit |
| `error` | on failure, a short reason string |

A `"failed"` status (or any of the failure conditions above) tells the tool the
swap did not happen; it will not update the position as if it did.

## Anvil paper-mode note

An anvil fork of Robinhood Chain with prefunded unlocked accounts is a valid
paper venue: identical `cast` syntax, fake money, `--rpc-url http://localhost:PORT`.
Your wrapper is where those commands live. This project ships no transaction
code and takes no position on whether your wrapper is pointed at a fork or
elsewhere — that choice and its consequences are yours.
