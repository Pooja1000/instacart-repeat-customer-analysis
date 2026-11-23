# Metrics Tree

## North Star

**Repeat orders per user** — the total number of orders a user places after
their initial purchase period.

## Input Metrics

```mermaid
flowchart TD
    NS["🎯 North Star\nRepeat orders per user"]
    NS --> RR["Reorder rate\n(share of items reordered)"]
    NS --> BS["Basket size\n(items per order)"]
    NS --> DBO["Days between orders\n(cadence)"]

    RR --> RR_desc["Higher reorder rate → more habitual\npurchasing, associated with more\nreturn visits"]
    BS --> BS_desc["Larger baskets → user is consolidating\nshopping, treating the platform\nas primary grocery source"]
    DBO --> DBO_desc["Shorter gaps → more frequent\nordering, higher lifetime\norder count"]

    NS -.-> G1["🛡 Guardrail\nBasket size not shrinking"]
    NS -.-> G2["🛡 Guardrail\nOrder frequency quality"]

    G1 --> G1_desc["Nudges should not drive tiny\ntop-up orders that inflate\nfrequency but reduce basket value"]
    G2 --> G2_desc["Frequency not inflated by\nsplit baskets or accidental\nduplicate orders"]
```

## Guardrails

| Guardrail | What it protects against |
|-----------|------------------------|
| **Basket size not shrinking** | Nudges that drive tiny top-up orders, inflating frequency at the cost of basket value. |
| **Order frequency quality** | Frequency gains that come from split baskets rather than genuine additional shopping trips. |

## How to use this tree

1. **Track the North Star** at the cohort level after any intervention.
2. **Diagnose** changes by looking at the input metrics: did repeat orders go
   up because of more reordering, bigger baskets, or faster cadence?
3. **Watch guardrails**: if basket size drops or order frequency rises without
   proportional basket sizes, the nudge may be gaming the metric.
