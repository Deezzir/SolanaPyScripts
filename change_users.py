import random
import time
from typing import Dict, List, Optional
import pandas as pd
import os
import asyncio
from pytgcalls import idle  # type: ignore
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.account import UpdateUsernameRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest
from pytgcalls import PyTgCalls  # type: ignore
from pytgcalls.types import MediaStream  # type: ignore
from telethon.sync import TelegramClient, errors  # type: ignore
from telethon.sessions import StringSession  # type: ignore
from telethon.tl.functions.messages import ImportChatInviteRequest  # type: ignore


USERS_INFO_CSV: str = "./assets/users_info.csv"
PHONES_CSV: str = "./assets/phones.csv"
SESSIONS_CSV: str = "./assets/sessions.csv"
GROUP_ID: int = -2342342342
INVITE_LINK: str = ""


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

    async def change_user(tg_client: TelegramClient, user_data, x):
        
        # about, name, last name
        try:
            await tg_client(UpdateProfileRequest(about=user_data["description"],first_name=user_data["first_name"],last_name=user_data["last_name"]))
        except:
            print('Could not update user info for user ',user_data["username"])

        # username
        try:
            await tg_client(UpdateUsernameRequest(user_data["username"]))
        except:
            print('Could not update username for user ',user_data["username"])

        # photo
        try:
            input_file = await tg_client.upload_file(f"./assets/photos/{x}.png")
            print(input_file)
            await tg_client(UploadProfilePhotoRequest(file=input_file))
        except Exception as e:
            print(f'Could not update profile picture for user {user_data["username"]}: {e}')


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

            ##### UPDATE USER #####
            user = users_data.iloc[x]
            await change_user(tg_client,user,x)

            if tg_client is not None:
                clients.append(tg_client)

    print("All users updated.")


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
        print('here')
        process_sessions_csv(SESSIONS_CSV)


if __name__ == "__main__":
    main()
