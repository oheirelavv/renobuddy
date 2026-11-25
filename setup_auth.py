#!/usr/bin/env python3
"""Set up RenoBuddy authentication credentials.

Run this script to create .streamlit/secrets.toml with securely hashed passwords.
Passwords are entered via the terminal and never stored in plaintext.
"""

import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.auth import hash_new_password

SECRETS_DIR = Path(__file__).parent / ".streamlit"
SECRETS_PATH = SECRETS_DIR / "secrets.toml"


def main():
    print("=" * 50)
    print("RenoBuddy — Authentication Setup")
    print("=" * 50)
    print()

    if SECRETS_PATH.exists():
        answer = input("secrets.toml already exists. Overwrite? (y/N): ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return

    # Admin account
    print("--- Admin account ---")
    admin_user = input("Admin username [admin]: ").strip() or "admin"
    admin_pw = getpass.getpass("Admin password: ")
    if not admin_pw:
        print("Error: password cannot be empty.")
        return
    admin_pw2 = getpass.getpass("Confirm admin password: ")
    if admin_pw != admin_pw2:
        print("Error: passwords do not match.")
        return
    admin_hash = hash_new_password(admin_pw)

    print()

    # User account
    print("--- User account ---")
    user_name = input("User username [user]: ").strip() or "user"
    user_pw = getpass.getpass("User password: ")
    if not user_pw:
        print("Error: password cannot be empty.")
        return
    user_pw2 = getpass.getpass("Confirm user password: ")
    if user_pw != user_pw2:
        print("Error: passwords do not match.")
        return
    user_hash = hash_new_password(user_pw)

    # Read existing OpenAI key if present
    openai_key = ""
    if SECRETS_PATH.exists():
        with open(SECRETS_PATH) as f:
            for line in f:
                if line.strip().startswith("OPENAI_API_KEY"):
                    openai_key = line.strip().split("=", 1)[1].strip().strip('"')
                    break

    if not openai_key:
        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.strip().startswith("OPENAI_API_KEY"):
                        openai_key = line.strip().split("=", 1)[1].strip().strip('"')
                        break

    if not openai_key:
        openai_key = "your-openai-api-key-here"

    # Write secrets.toml
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)

    content = f'''OPENAI_API_KEY = "{openai_key}"

[auth]
admin_username = "{admin_user}"
admin_password_hash = "{admin_hash}"
user_username = "{user_name}"
user_password_hash = "{user_hash}"
'''

    with open(SECRETS_PATH, "w") as f:
        f.write(content)

    os.chmod(SECRETS_PATH, 0o600)

    print()
    print(f"secrets.toml created at: {SECRETS_PATH}")
    print("File permissions set to owner-only (600).")
    print()
    print("You can now start RenoBuddy:")
    print("  streamlit run app/Home.py")


if __name__ == "__main__":
    main()
