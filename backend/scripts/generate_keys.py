#!/usr/bin/env python3
"""Generate Ed25519 key pair for JWT token signing.

Usage:
    python scripts/generate_keys.py [output_directory]

Default output directory: ./keys/
"""
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization


def generate_keys(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    private_path = output_dir / "private_key.pem"
    public_path = output_dir / "public_key.pem"

    private_path.write_bytes(private_pem)
    private_path.chmod(0o600)
    public_path.write_bytes(public_pem)

    print(f"Generated Ed25519 key pair:")
    print(f"  Private key: {private_path}")
    print(f"  Public key:  {public_path}")
    print()
    print("Add to your .env:")
    print(f'  JWT_PRIVATE_KEY_PATH={private_path.resolve()}')
    print(f'  JWT_PUBLIC_KEY_PATH={public_path.resolve()}')


if __name__ == "__main__":
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("keys")
    generate_keys(output)
