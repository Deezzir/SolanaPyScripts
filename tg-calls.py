import random
import time
from typing import Dict, List, Optional
import pandas as pd
import os
import asyncio
from pytgcalls import idle  # type: ignore
from pytgcalls import PyTgCalls  # type: ignore
from pytgcalls.types import MediaStream  # type: ignore
from telethon.sync import TelegramClient  # type: ignore
from telethon.sessions import StringSession  # type: ignore

PHONES_CSV: str = "./assets/phones.csv"
SESSIONS_CSV: str = "./assets/sessions.csv"
GROUP_ID: int = -100123456789  # replace with your group id


def read_phones_csv(file_path: str) -> Optional[pd.DataFrame]:
    try:
        csv_file = pd.read_csv(
            file_path,
            delimiter=",",
            header=None,
            dtype={0: str, 1: str, 2: str, 3: str},
            names=["phone", "password", "api_id", "api_hash"],
        )
        return csv_file
    except FileNotFoundError as e:
        print(f"File '{file_path}' not found: {e}")
        return None
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None


def create_sessions_csv(file_path: str, phones_df: pd.DataFrame) -> None:
    sessions: List[Dict[str, str]] = []

    for _, phone_entry in phones_df.iterrows():
        try:
            print(f"Creating session for phone: {phone_entry['phone']}")
            client = TelegramClient(
                StringSession(), phone_entry["api_id"], phone_entry["api_hash"]
            )
            client.start(phone=phone_entry["phone"], password=phone_entry["password"])
            session_str = client.session.save()
            sessions.append(
                {
                    "phone": phone_entry["phone"],
                    "session": session_str,
                    "api_id": phone_entry["api_id"],
                    "api_hash": phone_entry["api_hash"],
                }
            )
        except KeyboardInterrupt:
            print("Interrupted")
            return
        except Exception as e:
            print(f"Error creating TelegramClient: {e}")
            continue

    sessions_df = pd.DataFrame(sessions)
    if len(sessions_df) == 0:
        print("No sessions created")
        return
    sessions_df.to_csv(file_path, index=False, header=False)


def join_tg_call(
    phone: str, session: str, api_id: str, api_hash: str
) -> Optional[PyTgCalls]:
    print(f"Joining call with phone: {phone}")
    tg_client = TelegramClient(StringSession(session), api_id, api_hash)
    call_client = PyTgCalls(tg_client)

    # sleep random time to avoid flood wait
    # time.sleep(random.randint(1, 5))

    try:
        call_client.start()
        call_client.play(GROUP_ID, None)
        call_client.mute_stream(GROUP_ID)
    except Exception as e:
        print(f"Error joining call: {e}")
        return None

    return call_client


def process_sessions_csv(file_path: str) -> None:
    sessions_df = pd.read_csv(
        file_path,
        delimiter=",",
        header=None,
        dtype={0: str, 1: str, 2: str, 3: str},
        names=["phone", "session", "api_id", "api_hash"],
    )

    clients = []
    for _, session_entry in sessions_df.iterrows():
        client = join_tg_call(
            session_entry["phone"],
            session_entry["session"],
            session_entry["api_id"],
            session_entry["api_hash"],
        )
        if client is not None:
            clients.append(client)

    idle()

    for client in clients:
        client.leave_call(GROUP_ID)
    print("All calls done")


def main():
    if not os.path.exists(SESSIONS_CSV):
        if not os.path.exists(PHONES_CSV):
            print("phones.csv not found")
            return
        phones_df = read_phones_csv(PHONES_CSV)
        if phones_df is None:
            print("Failed to process phones.csv")
            return
        create_sessions_csv(SESSIONS_CSV, phones_df)
    else:
        process_sessions_csv(SESSIONS_CSV)


if __name__ == "__main__":
    main()
