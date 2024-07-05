import base58
from solders.keypair import Keypair  # type: ignore
import json
import os
import csv

TARGET_FOLDER = "./keys"


def convert_private_key_to_file(base58_private_key, file_path) -> None:
    decoded_key = base58.b58decode(base58_private_key)
    key_numbers = list(decoded_key)
    with open(file_path, "w") as f:
        json.dump(key_numbers, f, separators=(",", ":"))
    print(f"Private key saved to {file_path}")


def process_keys_txt(input_file) -> None:
    with open(input_file, "r") as f:
        private_keys = f.readlines()

    for idx, base58_private_key in enumerate(private_keys, start=1):
        if len(base58_private_key) < 10:
            continue
        base58_private_key = base58_private_key.strip()
        file_path = f"./keys/key{idx}.json"
        convert_private_key_to_file(base58_private_key, file_path)


def process_keys_csv(input_file) -> None:
    with open(input_file, "r") as f:
        private_keys = csv.reader(f, delimiter=",")

        next(private_keys)  # Skip header

        for idx, row in enumerate(private_keys, start=1):
            base58_private_key = row[1]
            file_path = f"./keys/key{idx}.json"
            convert_private_key_to_file(base58_private_key, file_path)


if __name__ == "__main__":
    input_file = "./private.txt"

    os.makedirs(TARGET_FOLDER, exist_ok=True)
    _, ext = os.path.splitext(input_file)
    if ext == ".txt":
        process_keys_txt(input_file)
    elif ext == ".csv":
        process_keys_csv(input_file)
    else:
        print("Unsupported file format")
        exit(1)
