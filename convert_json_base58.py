from os.path import join, getsize
from pathlib import Path
import os
from typing import Any, List, Set
import json
import base58
import pandas as pd
from solders.keypair import Keypair # type: ignore

KEYS_FOLDER = Path("keys")
CSV_TARGET = Path("keys.csv")

def validate_private_key(private_key: bytes):
    try:
        Keypair.from_bytes(private_key)
        return True
    except Exception as e:
        print(e)
        return False

def read_files(files: List[str], root: Path) -> List[str]:
    keys = []
    print(f"Checking {len(files)} files")

    for file in files:
        file_path = root / file
        if file_path.suffix == ".json":
            with open(file_path, "r") as f:
                try:
                    content = bytes(json.loads(f.read()))
                    if validate_private_key(content):
                        keys.append(str(base58.b58encode(content)))
                except Exception as e:
                    print(F"Error occured during the read of '{file_path}': {e}")
    return keys

def read_dir(dir: Path) -> List[str]:
    keys_set: Set[str] = set()

    for root, dirs, files in os.walk(dir):
        print(f"Checking '{root}' directory")
        keys = read_files(files, Path(root))
        print(f"Found {len(keys)} keys")
        keys_set.update(set(keys))
    return list(keys_set)

def create_dataframe(raw_keys: List[str]) -> pd.DataFrame:
    rows = []
    for raw_key in raw_keys:
        rows.append([raw_key, False])
    return pd.DataFrame(rows, columns=["key", "is_reserve"])

def main() -> None:
    raw_keys = read_dir(KEYS_FOLDER)
    print(f"Found {len(raw_keys)} unique keys")
    dt = create_dataframe(raw_keys)
    dt.to_csv(CSV_TARGET, index=False, sep=",")
    print(f"Created {CSV_TARGET} with the processed keys")

if __name__ == "__main__":
    main()
