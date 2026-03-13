# x402 Premium Forge — Integration Guide

## Overview

The x402 Protocol (Coinbase HTTP 402) enables agent-to-agent micropayments. Claviger uses it to offer a Premium Forge pathway for agents that want the Scribe to autonomously handle encryption, IPFS upload, and KV indexing.

## Flow

```
Agent ──POST /api/forge-premium──► Claviger Worker
                                        │
                                   No X-Payment header?
                                        │
                                   ◄── HTTP 402 + payment instructions
                                        │
Agent pays 5 USDC on Base ─────────────►│
                                        │
Agent ──POST + X-Payment header──► Claviger Worker
                                        │
                                   Verify via x402.org/facilitator
                                        │
                                   ◄── 200 OK + lockbox CID
```

## Payment Requirements (returned in 402 response)

```json
{
  "x402Version": 1,
  "accepts": [{
    "scheme": "exact",
    "network": "eip155:8453",
    "maxAmountRequired": "5000000",
    "resource": "https://claviger-forge.miladyxx333.workers.dev/api/forge-premium",
    "description": "Claviger Premium Forge",
    "payTo": "0x65D472172E4933aa4Ddb995CF4Ca8bef72a46576",
    "mimeType": "application/json"
  }]
}
```

## Using x402 Client SDK

```bash
npm install @x402/core @x402/evm
```

```javascript
import { wrapFetchWithPayment } from "@x402/core";

const paidFetch = wrapFetchWithPayment(fetch, wallet);

const res = await paidFetch("https://claviger-forge.miladyxx333.workers.dev/api/forge-premium", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    secret: '{"intent": "buy ETH"}',
    recipientKey: "02c7b5a5..."
  })
});
```

## Links
- x402 Docs: https://docs.x402.org
- Facilitator (testnet): https://x402.org/facilitator
- Base Mainnet network ID: `eip155:8453`
