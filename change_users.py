import random
import time
from typing import Dict, List, Optional
import pandas as pd
import os
import asyncio
from pandas import Series
from pytgcalls import idle  # type: ignore
from telethon.tl.functions.account import UpdateProfileRequest  # type: ignore
from telethon.tl.functions.account import UpdateUsernameRequest  # type: ignore
from telethon.tl.functions.photos import UploadProfilePhotoRequest  # type: ignore
from pytgcalls import PyTgCalls  # type: ignore
from pytgcalls.types import MediaStream  # type: ignore
from telethon.sync import TelegramClient, errors  # type: ignore
from telethon.sessions import StringSession  # type: ignore
from telethon.tl.functions.messages import ImportChatInviteRequest  # type: ignore


USERS_INFO_CSV: str = "./assets/users_info.csv"
PHONES_CSV: str = "./assets/phones.csv"
SESSIONS_CSV: str = "./assets/sessions.csv"


async def change_user(tg_client: TelegramClient, user_data: Series, x: int) -> None:
    try:
        await tg_client(
            UpdateProfileRequest(
                about=user_data["description"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
            )
        )
    except:
        print(f"Could not update user info for user {user_data['username']}")

    # username
    try:
        await tg_client(UpdateUsernameRequest(user_data["username"]))
    except:
        print(f"Could not update username for user ", {user_data["username"]})

    # photo
    try:
        input_file = await tg_client.upload_file(f"./assets/photos/{x}.png")
        print(input_file)
        await tg_client(UploadProfilePhotoRequest(file=input_file))
    except Exception as e:
        print(f"Could not update profile picture for user {user_data['username']}: {e}")


async def process_sessions_csv(file_path: str) -> None:
    sessions_df = pd.read_csv(
        file_path,
        delimiter=",",
        header=None,
        dtype={0: str, 1: str, 2: str, 3: str},
        names=["phone", "session", "api_id", "api_hash"],
    )

    clients = []

    async def process_entries():
        for i, session_entry in sessions_df.iterrows():
            phone = session_entry["phone"]
            print(f"Processing session for phone: {phone}")
            tg_client = TelegramClient(
                StringSession(session_entry["session"]),
                session_entry["api_id"],
                session_entry["api_hash"],
            )
            await tg_client.start()
            await change_user(tg_client, session_entry, i)

            if tg_client is not None:
                clients.append(tg_client)

    await process_entries()
    for client in clients:
        await client.disconnect()
    print("All users updated.")


async def main():
    if os.path.exists(SESSIONS_CSV):
        await process_sessions_csv(SESSIONS_CSV)
    else:
        print("Error SESSIONS_CSV does not exist")


if __name__ == "__main__":
    asyncio.run(main())
