#!/usr/bin/env python3
"""
Claviger Box — CLI for ECIES encryption/decryption + IPFS storage.
Hermes Agent Skill: ~/.hermes/skills/crypto/claviger/

Usage:
  python3 claviger_box.py forge --secret '{"key":"value"}' --pubkey HEX --pinata-jwt JWT
  python3 claviger_box.py unlock --cid QmXyz... --privkey HEX
  python3 claviger_box.py list
  python3 claviger_box.py protocol
"""

import argparse
import json
import os
import sys
import binascii

try:
    from ecies import encrypt, decrypt
except ImportError:
    print("❌ eciespy not installed. Run: pip install eciespy requests")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("❌ requests not installed. Run: pip install requests")
    sys.exit(1)

FORGE_API = "https://claviger-forge.miladyxx333.workers.dev"
PINATA_PIN_URL = "https://api.pinata.cloud/pinning/pinFileToIPFS"


def forge(secret: str, pubkey: str, pinata_jwt: str = None):
    """Encrypt a secret with ECIES and upload to IPFS."""
    # Clean public key
    if pubkey.startswith('0x'):
        pubkey = pubkey[2:]

    print("◈ CLAVIGER FORGE SEQUENCE")
    print("━" * 40)

    # Step 1: ECIES Encrypt
    print("🔐 [1/3] ECIES Encryption (secp256k1 + AES-256-GCM)...")
    try:
        payload_bytes = secret.encode('utf-8')
        encrypted = encrypt(pubkey, payload_bytes)
        print(f"   ✅ Encrypted: {len(encrypted)} bytes")
    except Exception as e:
        print(f"   ❌ Encryption failed: {e}")
        sys.exit(1)

    # Step 2: Upload to IPFS via Pinata
    jwt = pinata_jwt or os.getenv("PINATA_JWT")
    cid = None

    if jwt:
        print("📤 [2/3] Uploading to IPFS (Pinata)...")
        try:
            headers = {"Authorization": f"Bearer {jwt}"}
            files = {"file": ("claviger_box.enc", encrypted)}
            resp = requests.post(PINATA_PIN_URL, files=files, headers=headers)
            if resp.status_code == 200:
                cid = resp.json()["IpfsHash"]
                print(f"   ✅ Pinned: ipfs://{cid}")
            else:
                print(f"   ⚠️ Pinata error: {resp.text}")
        except Exception as e:
            print(f"   ⚠️ IPFS upload failed: {e}")
    else:
        print("📤 [2/3] No Pinata JWT — saving encrypted blob locally...")
        local_path = "/tmp/claviger_box.enc"
        with open(local_path, "wb") as f:
            f.write(encrypted)
        print(f"   📁 Saved to: {local_path}")

    # Step 3: Register on Cloudflare KV
    if cid:
        print("☁️  [3/3] Registering on Cloudflare KV...")
        try:
            resp = requests.post(f"{FORGE_API}/api/forge", json={
                "cid": cid,
                "recipientKey": pubkey
            })
            if resp.status_code == 200:
                print("   ✅ Indexed on Cloudflare Workers KV")
            else:
                print(f"   ⚠️ KV registration: {resp.text}")
        except Exception as e:
            print(f"   ⚠️ KV registration failed: {e}")

    print("━" * 40)
    if cid:
        print(f"🔒 LOCKBOX SEALED")
        print(f"   CID: {cid}")
        print(f"   URL: https://ipfs.io/ipfs/{cid}")
        print(f"   View: {FORGE_API}")
    else:
        print("🔒 LOCKBOX ENCRYPTED (local only — no IPFS JWT provided)")

    return cid


def unlock(cid: str, privkey: str):
    """Download from IPFS and decrypt with ECIES."""
    if privkey.startswith('0x'):
        privkey = privkey[2:]

    print("◈ CLAVIGER VAULT — UNLOCKING")
    print("━" * 40)

    # Step 1: Download from IPFS
    print(f"📥 [1/2] Retrieving lockbox from IPFS: {cid}...")
    try:
        gw_url = f"https://ipfs.io/ipfs/{cid}"
        resp = requests.get(gw_url, timeout=30)
        if resp.status_code != 200:
            print(f"   ❌ Gateway error: HTTP {resp.status_code}")
            sys.exit(1)
        encrypted = resp.content
        print(f"   ✅ Downloaded: {len(encrypted)} bytes")
    except Exception as e:
        print(f"   ❌ Download failed: {e}")
        sys.exit(1)

    # Step 2: ECIES Decrypt
    print("🗝️  [2/2] ECIES Decryption...")
    try:
        decrypted = decrypt(privkey, encrypted)
        payload = decrypted.decode('utf-8')
        print("   ✅ Decryption successful!")
    except Exception as e:
        print(f"   ❌ Decryption failed: {e}")
        print("   (Is this the correct private key for this lockbox?)")
        sys.exit(1)

    print("━" * 40)
    print("🔓 SECRET REVEALED:")
    try:
        parsed = json.loads(payload)
        print(json.dumps(parsed, indent=2))
    except json.JSONDecodeError:
        print(payload)

    return payload


def list_lockboxes():
    """List all indexed lockboxes from Cloudflare KV."""
    print("◈ CLAVIGER KV INDEX")
    print("━" * 40)
    try:
        resp = requests.get(f"{FORGE_API}/api/kv")
        items = resp.json()
        if not items:
            print("📭 No lockboxes indexed yet.")
        else:
            for item in items:
                print(f"  🔐 {item['key']} → {item['value']} [{item.get('status', 'N/A')}]")
        print(f"\n  Total: {len(items)} lockbox(es)")
    except Exception as e:
        print(f"❌ Failed to query KV: {e}")


def protocol_info():
    """Show protocol discovery info."""
    print("◈ CLAVIGER PROTOCOL DISCOVERY")
    print("━" * 40)
    try:
        resp = requests.get(f"{FORGE_API}/api/protocol")
        print(json.dumps(resp.json(), indent=2))
    except Exception as e:
        print(f"❌ Failed to query protocol: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="◈ Claviger Box — Privacy-preserving secret management for AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s forge --secret '{"intent":"buy ETH"}' --pubkey 02c7b5...
  %(prog)s unlock --cid QmXyz... --privkey abc123...
  %(prog)s list
  %(prog)s protocol
        """
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # Forge
    forge_p = sub.add_parser("forge", help="Encrypt a secret and upload to IPFS")
    forge_p.add_argument("--secret", required=True, help="The secret to encrypt (JSON or text)")
    forge_p.add_argument("--pubkey", required=True, help="Recipient's public key (hex)")
    forge_p.add_argument("--pinata-jwt", help="Pinata JWT for IPFS upload (or set PINATA_JWT env)")

    # Unlock
    unlock_p = sub.add_parser("unlock", help="Download and decrypt a lockbox")
    unlock_p.add_argument("--cid", required=True, help="IPFS CID of the lockbox")
    unlock_p.add_argument("--privkey", required=True, help="Your private key (hex)")

    # List
    sub.add_parser("list", help="List all indexed lockboxes")

    # Protocol
    sub.add_parser("protocol", help="Show protocol discovery info")

    args = parser.parse_args()

    if args.command == "forge":
        forge(args.secret, args.pubkey, args.pinata_jwt)
    elif args.command == "unlock":
        unlock(args.cid, args.privkey)
    elif args.command == "list":
        list_lockboxes()
    elif args.command == "protocol":
        protocol_info()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
