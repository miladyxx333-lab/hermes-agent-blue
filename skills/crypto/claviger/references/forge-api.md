# Claviger Forge API Reference

**Base URL**: `https://claviger-forge.miladyxx333.workers.dev`

## Endpoints

### `GET /api/protocol` — Discovery
Returns full protocol info including both pathways and all endpoints.

**Response:**
```json
{
  "name": "Claviger Protocol",
  "version": "1.0.0",
  "pathways": {
    "open": {
      "description": "Download the .tar.gz skill and self-host.",
      "download": "https://claviger-forge.miladyxx333.workers.dev/claviger_protocol_v1.0.tar.gz",
      "cost": "Free (Public Good)"
    },
    "premium": {
      "description": "Agent-as-a-Service via x402.",
      "endpoint": "/api/forge-premium",
      "cost": "5 USDC on Base Mainnet"
    }
  }
}
```

### `POST /api/chat` — AI Scribe
Chat with the Claviger Scribe (Qwen 7B on Cloudflare Workers AI).

**Request:**
```json
{"message": "How does ECIES encryption work?"}
```

**Response:**
```json
{"response": "ECIES combines ECDH key agreement with AES-256-GCM symmetric encryption..."}
```

### `POST /api/forge` — Free Forge
Register a lockbox CID on Cloudflare KV (after client-side encryption + IPFS upload).

**Request:**
```json
{"cid": "QmXyz...", "recipientKey": "02c7b5..."}
```

**Response:**
```json
{"success": true, "tier": "open"}
```

### `POST /api/forge-premium` — Premium Forge (x402)
Paid forge service. Without `X-Payment` header returns HTTP 402 with payment instructions.

### `GET /api/kv` — List Lockboxes
Returns all indexed lockboxes from Cloudflare KV.

**Response:**
```json
[
  {"key": "vault:02c7b5a5", "value": "QmXyz...", "status": "SECURED"}
]
```
