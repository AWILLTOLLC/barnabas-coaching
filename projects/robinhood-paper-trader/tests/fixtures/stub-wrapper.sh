#!/bin/bash
# Test-only stub of an external executor wrapper: reads an order JSON from
# stdin, echoes a canned fill JSON. No chain interaction of any kind.
order=$(cat)
order_id=$(echo "$order" | grep -o '"order_id":"[^"]*"' | cut -d'"' -f4)
echo "{\"order_id\":\"$order_id\",\"status\":\"filled\",\"fill_price_usd\":0.002,\"token_amount\":4985,\"usd_value\":10,\"fee_usd\":0.03,\"tx_ref\":\"stub\"}"
