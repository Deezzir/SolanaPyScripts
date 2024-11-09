from os.path import join, getsize
from pathlib import Path
import os
from typing import Any, List, Optional, Set
import json
import base58
import pandas as pd
from solders.keypair import Keypair  # type: ignore

KEYS_FOLDER = Path("../../keys")
CSV_TARGET = Path("keys.csv")


def get_keypair(private_key: bytes) -> Optional[Keypair]:
    try:
        return Keypair.from_bytes(private_key)
    except Exception as e:
        print(e)
        return None


def read_files(files: List[str], root: Path) -> List[Keypair]:
    keys = []
    print(f"Checking {len(files)} files")

    for file in files:
        file_path = root / file
        if file_path.suffix == ".json":
            with open(file_path, "r") as f:
                try:
                    content = bytes(json.loads(f.read()))
                    keypair = get_keypair(content)
                    if keypair:
                        keys.append(keypair)
                except Exception as e:
                    print(f"Error occured during the read of '{file_path}': {e}")
    return keys


def read_dir(dir: Path) -> List[Keypair]:
    keys_set: Set[Keypair] = set()
    for root, _, files in os.walk(dir):
        print(f"Checking '{root}' directory")
        keys = read_files(files, Path(root))
        print(f"Found {len(keys)} keys")
        keys_set.update(set(keys))
    return list(keys_set)


def create_dataframe(raw_keys: List[Keypair]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            [
                f"wallet[{i+1}]",
                str(base58.b58encode(bytes(k)).decode("utf-8")),
                "false",
                str(k.pubkey()),
                0,
            ]
            for i, k in enumerate(raw_keys)
        ],
        columns=["name", "private_key", "is_reserve", "public_key", "created_at"],
    )


def main() -> None:
    keypairs = read_dir(KEYS_FOLDER)
    print(f"Found {len(keypairs)} unique keys")
    dt = create_dataframe(keypairs)
    dt.to_csv(CSV_TARGET, index=False, sep=",")
    print(f"Created {CSV_TARGET} with the processed keys")


if __name__ == "__main__":
    main()
