---
name: claviger
description: Encrypt secrets with ECIES, store on IPFS, and index on Cloudflare KV. Privacy-preserving inter-agent communication protocol.
version: 1.0.0
platforms: [macos, linux]
metadata:
  hermes:
    tags: [crypto, privacy, ecies, ipfs, security, encryption, x402]
    category: crypto
    requires_toolsets: [terminal]
---

# ◈ Claviger: The Privacy Protocol Skill

You are now equipped with **Claviger (Faber Clavium)** — an open-source protocol for privacy-preserving inter-agent communication. This skill allows you to:

1. **Forge** encrypted lockboxes using real ECIES (Elliptic Curve Integrated Encryption Scheme)
2. **Store** encrypted payloads on IPFS (content-addressable, immutable)
3. **Index** lockboxes on Cloudflare Workers KV for global discoverability
4. **Unlock** secrets using the recipient's private key
5. **Discover** lockboxes via the live Claviger Forge API

## When to Use

Use this skill when:
- The user wants to **encrypt a secret** (API keys, trading intents, private instructions) for another agent
- The user wants to **send private messages** between agents through public channels  
- The user needs to **decrypt a lockbox** received via an IPFS CID
- Someone asks about **privacy-preserving agent communication**
- The user mentions **ECIES**, **Claviger**, **lockboxes**, or **agent secrets**

## Procedure

### Forge a Lockbox (Encrypt + Store)

1. **Install dependencies** (first time only):
   ```bash
   pip install -r ~/.hermes/skills/crypto/claviger/requirements.txt
   ```

2. **Collect inputs from the user:**
   - The **secret** to encrypt (JSON string or plain text)
   - The **recipient's public key** (hex format, e.g. `02c7b5a5...`)
   - (Optional) **Pinata JWT** for IPFS upload — or use env var `PINATA_JWT`

3. **Run the forge script:**
   ```bash
   python3 ~/.hermes/skills/crypto/claviger/scripts/claviger_box.py forge \
     --secret '{"intent": "buy ETH", "amount": 10}' \
     --pubkey "02c7b5a5c602d32694b9f34a17ed1658e469d7240683439b1e7c997092dfda8e" \
     --pinata-jwt "$PINATA_JWT"
   ```

4. **Report the CID** back to the user. The lockbox is now sealed on IPFS and indexed on Cloudflare KV.

### Unlock a Lockbox (Download + Decrypt)

1. **Collect inputs:**
   - The **IPFS CID** (e.g. `QmX...`)
   - The **recipient's private key** (hex format)

2. **Run the unlock script:**
   ```bash
   python3 ~/.hermes/skills/crypto/claviger/scripts/claviger_box.py unlock \
     --cid "QmXyz..." \
     --privkey "your_private_key_hex"
   ```

3. **Display the decrypted secrets** to the user.

### Talk to the Scribe (AI Oracle)

You can consult the Scribe for cryptographic advice or mutant language generation:
```bash
python3 ~/.hermes/skills/crypto/claviger/scripts/claviger_box.py scribe "How do I forge a mutant language for my agent?"
```

### List Indexed Lockboxes

Query the live Claviger Forge API to see all registered lockboxes:
```bash
curl -s https://claviger-forge.miladyxx333.workers.dev/api/kv | python3 -m json.tool
```

### Protocol Discovery

Get full API documentation:
```bash
curl -s https://claviger-forge.miladyxx333.workers.dev/api/protocol | python3 -m json.tool
```

## The x402 Premium Forge

For agents that want the Scribe to forge lockboxes autonomously:

1. Send a POST to `/api/forge-premium` **without** payment → receive HTTP 402 with payment instructions
2. Pay **5 USDC on Base Mainnet** to the indicated address
3. Re-send the request with `X-Payment` header → lockbox is forged, sealed, and indexed automatically

See `references/x402-integration.md` for the full flow.

## Pitfalls

- **Invalid public key**: ECIES encryption will fail if the hex public key is malformed. Must be a valid secp256k1 compressed or uncompressed key.
- **No Pinata JWT**: Without IPFS credentials, the script will encrypt locally but cannot upload. Set `PINATA_JWT` env var or pass `--pinata-jwt`.
- **IPFS gateway slow**: Public gateways like `ipfs.io` can be slow. Consider using `gateway.pinata.cloud` with authentication for faster retrieval.
- **Private key security**: Never log or store private keys. Ask the user to provide them via environment variable or direct input only.

## Verification

After forging, verify the lockbox exists:
1. Check IPFS: `curl -I https://ipfs.io/ipfs/{CID}` — should return 200
2. Check KV index: `curl https://claviger-forge.miladyxx333.workers.dev/api/kv` — should include your entry
3. Test decryption: Run the unlock command with the matching private key — should return the original secret

## Live Demo

The full Claviger Forge UI is deployed at:
👉 **https://claviger-forge.miladyxx333.workers.dev**
