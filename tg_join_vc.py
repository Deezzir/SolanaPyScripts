import random
import time
from typing import Dict, List, Optional
import pandas as pd
import os
import asyncio
from pytgcalls import idle  # type: ignore
from pytgcalls import PyTgCalls  # type: ignore
from pytgcalls.types import MediaStream  # type: ignore
from telethon.sync import TelegramClient, errors  # type: ignore
from telethon.sessions import StringSession  # type: ignore
from telethon.tl.functions.messages import ImportChatInviteRequest  # type: ignore

PHONES_CSV: str = "./assets/phones.csv"
SESSIONS_CSV: str = "./assets/sessions.csv"
GROUP_ID: int = -1002193610260
INVITE_LINK: str = "https://t.me/+pX_jSF5o3FAwZGIx"


def read_phones_csv(file_path: str) -> Optional[pd.DataFrame]:
    try:
        csv_file = pd.read_csv(
            file_path,
            delimiter=",",
            header=None,
            dtype={0: str, 1: str, 2: str, 3: str},
            names=["phone", "password", "api_id", "api_hash"],
        )

        if csv_file.shape[0] == 0:
            print(f"CSV file '{file_path}' is empty.")
            return None

        if csv_file.isnull().values.any():
            print(
                f"CSV file '{file_path}' contains missing values. Structure: Phone, Password, API ID, API Hash."
            )
            return None

        print(f"Read {csv_file.shape[0]} phone entries")

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


async def join_tg_call(tg_client: TelegramClient, phone: str) -> Optional[PyTgCalls]:
    print(f"Joining call with phone: {phone}")
    call_client = PyTgCalls(tg_client)

    try:
        await call_client.start()
        await call_client.play(GROUP_ID, None)
        await call_client.mute_stream(GROUP_ID)
    except Exception as e:
        print(f"Error joining call: {e}")
        return None

    return call_client


async def join_tg_group(
    tg_client: TelegramClient, invite_link: str, phone: str
) -> None:
    print(f"Joining group with phone: {phone}")

    try:
        chat = await tg_client.get_entity(invite_link)
        print(f"Already in the chat: {chat.title}")
    except errors.UserAlreadyParticipantError:
        print("You are already a participant of this chat.")
    except errors.InviteHashInvalidError:
        print("The invite link is invalid.")
    except errors.InviteHashExpiredError:
        print("The invite link has expired.")
    except Exception as e:
        try:
            hash = invite_link.split("/")[-1].replace("+", "")
            await tg_client(ImportChatInviteRequest(hash))
            print("Successfully joined the group.")
        except errors.InviteHashInvalidError:
            print("The invite link is invalid.")
        except errors.InviteHashExpiredError:
            print("The invite link has expired.")
        except Exception as e:
            print(f"Failed to join the group: {e}")


def process_sessions_csv(file_path: str) -> None:
    sessions_df = pd.read_csv(
        file_path,
        delimiter=",",
        header=None,
        dtype={0: str, 1: str, 2: str, 3: str},
        names=["phone", "session", "api_id", "api_hash"],
    )

    clients = []
    loop = asyncio.get_event_loop()

    async def process_entries():
        for _, session_entry in sessions_df.iterrows():
            phone = session_entry["phone"]
            print(f"Processing session for phone: {phone}")
            tg_client = TelegramClient(
                StringSession(session_entry["session"]),
                session_entry["api_id"],
                session_entry["api_hash"],
            )
            await tg_client.start()
            await join_tg_group(tg_client, INVITE_LINK, phone)
            client = await join_tg_call(tg_client, phone)
            if client is not None:
                clients.append(client)

    loop.run_until_complete(process_entries())

    idle()

    for client in clients:
        try:
            client.leave_call(GROUP_ID)
        except Exception as e:
            print(f"Error leaving call: {e}")
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
