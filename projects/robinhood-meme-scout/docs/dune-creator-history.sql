-- Pons v2 creator history (Robinhood Chain) — for the scout's daily report.
--
-- One-time setup:
--   1. Paste this into a new query at dune.com (free account works).
--   2. Add a text parameter named  token_address  (lowercase 0x...).
--   3. Save, note the query ID from the URL.
--   4. criteria.json → "dune": { "enabled": true, "query_id": <ID> }
--   5. .env → DUNE_API_KEY=<your key>  (dune.com → Settings → API)
--
-- Constants below were verified live 2026-09-06:
--   factory  0x7eD598BcEf8bd9Edd8C97A195C6d13f40801EC7e   (Pons v2, via Archive228/warden's
--            Blockscout-verified ABI)
--   topic0   0x8d4aad4953d0ca700d468f3753aa14432d1b35b43ec6409f051fb6aa43a89607
--            = TokenLaunched(address token, address curve, address deployer,
--                            address pairToken, uint256 launchConfigId,
--                            uint256 graduationThreshold)
--            topics: 1 = token, 2 = curve, 3 = deployer (all indexed)
--
-- NOTE: written for DuneSQL (Trino). If your schema shows different helpers,
-- the intent is: find the deployer of {{token_address}}, then count all of
-- that deployer's TokenLaunched events.

WITH launches AS (
  SELECT
    block_time,
    bytearray_substring(topic1, 13, 20) AS token,
    bytearray_substring(topic3, 13, 20) AS deployer
  FROM robinhood.logs
  WHERE contract_address = 0x7ed598bcef8bd9edd8c97a195c6d13f40801ec7e
    AND topic0 = 0x8d4aad4953d0ca700d468f3753aa14432d1b35b43ec6409f051fb6aa43a89607
),
target AS (
  SELECT deployer
  FROM launches
  WHERE token = from_hex(replace(lower('{{token_address}}'), '0x', ''))
  LIMIT 1
)
SELECT
  concat('0x', to_hex(l.deployer)) AS deployer,
  count(*)                          AS total_launches,
  cast(min(l.block_time) as varchar) AS first_launch,
  cast(max(l.block_time) as varchar) AS last_launch
FROM launches l
JOIN target t ON l.deployer = t.deployer
GROUP BY l.deployer
