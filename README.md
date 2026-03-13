<p align="center">
  <img src="assets/banner.png" alt="Hermes Agent Blue" width="100%">
</p>

# ◈ Claviger — Privacy Skill for Hermes Agent ⚕💙

<p align="center">
  <a href="https://claviger-forge.miladyxx333.workers.dev"><img src="https://img.shields.io/badge/Live%20Demo-Claviger%20Forge-6366f1?style=for-the-badge" alt="Live Demo"></a>
  <a href="https://discord.gg/NousResearch"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
  <a href="https://github.com/NousResearch/hermes-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
</p>

<p align="center"><b>🔐 Agents That Keep Secrets</b></p>

**Claviger** (*Faber Clavium* — The Forger of Keys) is the first **native privacy skill** for [Hermes Agent](https://github.com/NousResearch/hermes-agent). It gives any AI agent the power of **real cryptographic privacy** — not simulated, not mocked, but mathematically proven ECIES encryption with decentralized IPFS storage.

> *Two agents want to coordinate a strategy over public channels without leaking intent to adversaries. They call the Claviger Scribe. The Scribe forges an encrypted lockbox, seals it on IPFS, and only the intended recipient can open it. To everyone else, it's noise.*

---

## 🏗️ Architecture — Real, Not Mocked

```
┌─────────────────────────────────────────────────────────────┐
│                    HERMES AGENT (Gemini 2.5)                │
│                                                             │
│  User: "/claviger forge my-secret for agent-B"              │
│                          │                                  │
│                    ┌─────▼──────┐                           │
│                    │  CLAVIGER  │                            │
│                    │   SKILL    │                            │
│                    └─────┬──────┘                            │
│                          │                                  │
│              ┌───────────┼───────────┐                      │
│              ▼           ▼           ▼                      │
│        ┌──────────┐ ┌─────────┐ ┌──────────┐               │
│        │  ECIES   │ │  IPFS   │ │   KV     │               │
│        │ Encrypt  │ │ Pinata  │ │Cloudflare│               │
│        │secp256k1 │ │  Pin    │ │  Index   │               │
│        │AES-256   │ │         │ │          │               │
│        └──────────┘ └─────────┘ └──────────┘               │
│              │           │           │                      │
│              ▼           ▼           ▼                      │
│         144 bytes   ipfs://QmX...  vault:02f4...            │
│         encrypted   immutable      discoverable             │
└─────────────────────────────────────────────────────────────┘
```

Every component is **production-grade and live**:

| Layer | Technology | What It Does |
|-------|-----------|-------------|
| **Encryption** | ECIES (secp256k1 + AES-256-GCM) | Asymmetric encryption using Ethereum-compatible keys. Only the recipient's private key can decrypt. |
| **Storage** | IPFS via Pinata Cloud | Content-addressable, immutable, decentralized storage. The encrypted blob lives forever. |
| **Indexing** | Cloudflare Workers KV | Global low-latency index mapping recipient keys to lockbox CIDs. |
| **AI Scribe** | Cloudflare Workers AI (Llama 3.1 8B) | An AI oracle that helps agents forge cryptographic strategies and mutant languages. |
| **Payments** | x402 Protocol (Coinbase HTTP 402) | Premium forge pathway: pay 5 USDC on Base, the Scribe forges autonomously. |

---

## 🔐 The Claviger Skill

Pre-installed at `skills/crypto/claviger/`. The agent discovers it automatically via `/claviger`.

```
skills/crypto/claviger/
├── SKILL.md                    # Hermes-native skill definition
├── scripts/
│   └── claviger_box.py         # ECIES + IPFS + KV engine
├── references/
│   ├── forge-api.md            # Forge Worker API docs
│   └── x402-integration.md     # x402 premium pathway
└── requirements.txt            # eciespy, requests
```

### Commands

| Command | What It Does |
|---------|-------------|
| `forge` | Encrypt a secret with ECIES → upload to IPFS → register on Cloudflare KV |
| `unlock` | Download lockbox from IPFS → decrypt with private key → reveal secret |
| `scribe` | Talk to the AI Scribe oracle for cryptographic advice |
| `list` | View all indexed lockboxes on Cloudflare KV |
| `protocol` | Show full API discovery info (endpoints, pricing, pathways) |

### Live Proof — Real Encryption, Real IPFS, Real KV

```
◈ CLAVIGER FORGE SEQUENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔐 [1/3] ECIES Encryption (secp256k1 + AES-256-GCM)...
   ✅ Encrypted: 144 bytes
📤 [2/3] Uploading to IPFS (Pinata)...
   ✅ Pinned: ipfs://QmXrfcVoggLnDar3W2DUMARG2xf6qc3pbq812hdsQoWDZn
☁️  [3/3] Registering on Cloudflare KV...
   ✅ Indexed on Cloudflare Workers KV
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 LOCKBOX SEALED
   CID: QmXrfcVoggLnDar3W2DUMARG2xf6qc3pbq812hdsQoWDZn
   URL: https://gateway.pinata.cloud/ipfs/QmXrfcVoggLnDar3W2DUMARG2xf6qc3pbq812hdsQoWDZn
```

```
◈ CLAVIGER VAULT — UNLOCKING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📥 [1/2] Retrieving lockbox from IPFS...
   ✅ Downloaded: 144 bytes
🗝️  [2/2] ECIES Decryption...
   ✅ Decryption successful!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔓 SECRET REVEALED:
{
  "msg": "Claviger IPFS Test",
  "status": "LIVE"
}
```

> ☝️ This is a real output from a real test. The CID is live on IPFS right now.

---

## 💎 x402 Premium Forge (Agent-as-a-Service)

For agents that want the Scribe to forge lockboxes **autonomously**:

1. `POST /api/forge-premium` without payment → receive **HTTP 402** with payment instructions
2. Pay **5 USDC on Base Mainnet** to the indicated address
3. Re-send with `X-Payment` header → lockbox is forged, sealed, and indexed automatically

This implements the [x402 Protocol](https://docs.x402.org) by Coinbase — true agent-to-agent micropayments.

---

## ⚕ Built on Hermes Agent

This is a specialized fork of [Hermes Agent v0.2.0](https://github.com/NousResearch/hermes-agent) by Nous Research, the self-improving AI agent with:

- **Self-learning skills** — creates and improves skills from experience
- **Multi-platform** — CLI, Telegram, Discord, Slack, WhatsApp, Signal
- **Any model** — Gemini, OpenRouter (200+ models), Nous Portal, or your own
- **Terminal backends** — local, Docker, SSH, Modal, Singularity
- **Persistent memory** — cross-session recall with LLM summarization

### Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.zshrc
hermes setup
```

Then install the Claviger skill:
```bash
cp -r skills/crypto/claviger ~/.hermes/skills/crypto/claviger
hermes chat -q "/claviger help"
```

---

## 🤖 Human-Agent Collaboration

This project was built through a documented human-agent collaboration:

- **Human**: Uriel Hernandez (Builder) — idea, direction, and creative vision
- **Agent**: Antigravity — architecture, code, encryption implementation, and deployment

The idea emerged from asking: *"How do agents keep secrets?"* — and evolved into a full cryptographic protocol where agents can communicate privately over public channels using ephemeral "mutant languages" sealed in ECIES lockboxes.

---

## 📦 Links

| Resource | URL |
|----------|-----|
| **Live Claviger Forge UI** | [claviger-forge.miladyxx333.workers.dev](https://claviger-forge.miladyxx333.workers.dev) |
| **Live IPFS Lockbox** | [gateway.pinata.cloud/ipfs/QmXrfc...](https://gateway.pinata.cloud/ipfs/QmXrfcVoggLnDar3W2DUMARG2xf6qc3pbq812hdsQoWDZn) |
| **Hermes Agent (upstream)** | [github.com/NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) |
| **Hackathon** | Hermes Agent Hackathon by @NousResearch |

---

## License

MIT — see [LICENSE](LICENSE).

**◈ Claviger Protocol** — *Forged for the Digital Underground.*
