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


def read_user_info_csv(file_path: str) -> Optional[pd.DataFrame]:
    try:
        csv_file = pd.read_csv(
            file_path,
            delimiter=",",
            header=None,
            dtype={0: str, 1: str, 2: str, 3: str},
            names=["first_name", "last_name", "username", "description"],
        )

        if csv_file.shape[0] == 0:
            print(f"CSV file '{file_path}' is empty.")
            return None

        if csv_file.isnull().values.any():
            print(
                f"CSV file '{file_path}' contains missing values. Structure: First Name, Last Name, User Name, Description."
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


async def process_sessions_csv(file_path: str) -> None:
    sessions_df = pd.read_csv(
        file_path,
        delimiter=",",
        header=None,
        dtype={0: str, 1: str, 2: str, 3: str},
        names=["phone", "session", "api_id", "api_hash"],
    )

    clients = []

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
            print(
                f"Could not update profile picture for user {user_data['username']}: {e}"
            )

    async def process_entries():
        users_data = read_user_info_csv(USERS_INFO_CSV)
        for x, session_entry in sessions_df.iterrows():
            phone = session_entry["phone"]
            print(f"Processing session for phone: {phone}")
            tg_client = TelegramClient(
                StringSession(session_entry["session"]),
                session_entry["api_id"],
                session_entry["api_hash"],
            )
            await tg_client.start()
            await change_user(tg_client, session_entry, x)

            if tg_client is not None:
                clients.append(tg_client)

    await process_entries()
    print("All users updated.")


async def main():
    if os.path.exists(SESSIONS_CSV):
        await process_sessions_csv(SESSIONS_CSV)
    else:
        print("Error. SESSIONS_CSV does not exist")


if __name__ == "__main__":
    asyncio.run(main())
