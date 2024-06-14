import base58
from solders.keypair import Keypair
import json
import os


def convert_private_key_to_file(base58_private_key, file_path):
    decoded_key = base58.b58decode(base58_private_key)
    key_numbers = list(decoded_key)
    with open(file_path, "w") as f:
        json.dump(key_numbers, f, separators=(",", ":"))
    print(f"Private key saved to {file_path}")


def process_private_keys_file(input_file):
    os.makedirs("keys", exist_ok=True)

    with open(input_file, "r") as f:
        private_keys = f.readlines()

    for idx, base58_private_key in enumerate(private_keys, start=11):
        if len(base58_private_key) < 10:
            continue
        base58_private_key = base58_private_key.strip()
        file_path = f"./keys/key{idx}.json"
        convert_private_key_to_file(base58_private_key, file_path)


if __name__ == "__main__":
    input_file = "./private.txt"  # Replace with your input file path
    process_private_keys_file(input_file)
