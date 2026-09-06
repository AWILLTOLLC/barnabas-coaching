# Infrastructure Flywheel Scanner - Overview Plan

## Feature Summary

A new scanner module that identifies infrastructure projects on emerging chains that are building liquidity aggregation flywheels — distinct from the meme coin watcher, this targets utility projects with real economic engines.

---

## Core Thesis

Infrastructure projects on new chains often get overlooked because:
- The chain/ecosystem is new and unfamiliar
- Fundamentals haven't peaked yet (market pricing future growth)
- They're not "memes" — boring but valuable

These projects can capture significant value if the ecosystem grows and they're positioned as liquidity infrastructure.

---

## Detection Criteria

### Primary Filters

| Criterion | Range | Rationale |
|-----------|-------|----------|
| **Chain Age** | < 12 months | New ecosystem, early infrastructure |
| **Market Cap** | $20M - $100M | Room to grow, not micro-cap noise |
| **Protocol-Owned Liquidity** | $500K+ (warn if >10% of MC) | Meaningful commitment, verify composition if very high |
| **Pool/Pair Count** | 25+ | Aggregating fragmented liquidity |
| **Fundamental Trend** | Up 3+ months | Engine actually working |

### Secondary Signals (Bonus Points)

- **Price/Fundamental Divergence**: Price flat/down while fundamentals up (value setup)
- **Ecosystem Backing**: Integration with credible protocols or entities
- **Exchange Presence**: Listed on 5+ exchanges (some tier-1/2)
- **Fee Generation**: Actual revenue from cross-asset trading

### Risk Flags (Must Report)

- **Upcoming Unlocks**: >5% monthly unlock schedule
- **Exchange Openings**: Withdrawals opening within 30 days
- **Holder Concentration**: Top 10 holders > 40% of supply

---

## Output Format

```
🏗️ INFRASTRUCTURE FLYWHEEL MATCH

Project: $NAME on Chain

Metrics:
  • MC: $X M
  • PSL: $Y K (Z% of MC)
  • Pools: N pools (M priced)
  • Trend: Fundamentals ↑ for X months

Why it matches:
  • [Criterion 1]: [Value]
  • [Criterion 2]: [Value]
  • [Criterion 3]: [Value]

Risk factors:
  • [Risk 1]
  • [Risk 2]

Narrative: [1-2 sentence summary]
```

---

## Technical Architecture

### Data Sources Needed

1. **Chain/Ecosystem Data**: Identify new chains (< 12 months)
2. **Token Metrics**: MC, PSL, pool count, holder data
3. **Volume/Fee Trends**: 3+ month historical data
4. **Unlock Schedules**: Tokenomics data
5. **Exchange Listings**: Exchange presence data

### Integration Points

- Reuse existing data pipelines where possible
- Add new filters for infrastructure-specific criteria
- Separate alert channel from meme coin watcher
- Different visual styling (🏗️ vs 🚀)

---

## Implementation Notes

### What Makes This Different from Meme Watcher

| Aspect | Meme Watcher | Infrastructure Flywheel |
|--------|--------------|----------------------|
| **Target** | Viral potential | Economic engine |
| **Metrics** | Social, volume spikes | PSL, pools, fees, trends |
| **Timeframe** | Short-term momentum | Medium-term fundamentals |
| **Risk Profile** | High volatility | Fundamentals + ecosystem risk |

### Ponytail Principles Apply

- **YAGNI**: Only track metrics that matter for this thesis
- **Stdlib first**: Reuse existing data sources before adding new ones
- **No over-engineering**: Simple filters, clear output
- **One job**: This scanner does ONE thing — find infrastructure flywheels

---

## Success Criteria

The scanner is working when:

1. ✅ It identifies projects matching the criteria
2. ✅ It reports risk factors (unlocks, etc.)
3. ✅ Output is clear and actionable
4. ✅ It doesn't overlap with meme coin watcher
5. ✅ It runs efficiently without excessive API calls

---

## Next Steps

1. Review existing data sources and identify gaps
2. Design filter pipeline
3. Implement with ponytail principles
4. Test against known examples (SHROOM, etc.)
5. Deploy and monitor
