import asyncio
import aiohttp
import os
import subprocess
from dotenv import load_dotenv
import re
from solders.pubkey import Pubkey  # type: ignore
from typing import Dict, Optional, Union

load_dotenv()

TWITTER_USERS: list[str] = []


URL: str = "https://twitter154.p.rapidapi.com/user/tweets"

QUERY: Dict[str, str] = {
    "limit": "10",
    "include_replies": "false",
    "include_pinned": "true",
}

HEADERS: Dict[str, str] = {
    "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY", ""),
    "X-RapidAPI-Host": "twitter154.p.rapidapi.com",
}

DESKTOP_PATH: str = os.path.join(os.path.expanduser("~"), "Desktop")
DIR: str = os.path.join(DESKTOP_PATH, "scripts", "solana-bots")
FILE_NAME: str = "pair.txt"
FILE_PATH: str = os.path.join(DIR, FILE_NAME)

try:
    os.makedirs(DIR, exist_ok=True)
except Exception as e:
    print(f"Error creating directory: {e}")
    exit(1)

SCRIPT_PATH = os.path.join(
    DESKTOP_PATH, "scripts", "solana-bots", "scripts", "!1open-all-profiles-test.scpt"
)
COMMAND = ["osascript", SCRIPT_PATH]


async def expand_url(short_url: str) -> str:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(short_url, allow_redirects=True) as response:
                return str(response.url)
    except aiohttp.ClientError as e:
        print(f"Error expanding URL: {e}")
        return short_url


async def replace_short_urls(text: str) -> str:
    URL_PATTERN = re.compile(r"(https?://t\.co/\S+?)([\.,!?]*)(?:\s|$)")

    matches = URL_PATTERN.findall(text)
    tasks = [expand_url(url) for url, _ in matches]
    expanded_urls = await asyncio.gather(*tasks)

    for (short_url, punctuation), expanded_url in zip(matches, expanded_urls):
        text = text.replace(short_url, expanded_url + punctuation)

    return text


def extract_and_validate_mint_address(text: str) -> Optional[str]:
    url_pattern = re.compile(r"https:\/\/(www\.)?pump\.fun\/[A-Za-z0-9]+")
    pubkey_pattern = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{43,44}\b")

    url_match = url_pattern.search(text)
    pubkey_match = pubkey_pattern.search(text)

    if not url_match and not pubkey_match:
        return None

    mint_address = None

    if pubkey_match:
        mint_address = pubkey_match.group(0)
    elif url_match:
        url = url_match.group(0)
        mint_address = url.split("/")[-1]

    if not mint_address:
        return None

    try:
        Pubkey.from_string(mint_address)
        return mint_address
    except Exception as e:
        return None


async def snipe_consume() -> Optional[str]:
    while True:
        for username in TWITTER_USERS:
            async with aiohttp.ClientSession() as session:
                try:
                    query = QUERY.copy()
                    query["username"] = username
                    async with session.get(
                        URL, headers=HEADERS, params=query
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            tweets = data["results"][:3]
                            for tweet in tweets:
                                text = tweet["text"]
                                text = await replace_short_urls(text)
                                print(f"Tweet: {text}")
                                mint = extract_and_validate_mint_address(text)
                                if mint:
                                    return mint
                except aiohttp.ClientError as e:
                    print(f"Client error: {e}")
                except Exception as e:
                    print(f"Unexpected error: {e}")
            await asyncio.sleep(0.3)
        await asyncio.sleep(0.5)
        print("\n\n")


def run_script() -> None:
    try:
        subprocess.run(COMMAND, check=True)
        print("AppleScript executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing the AppleScript: {e}")


def get_pair(mint: str) -> str:
    pair, _ = Pubkey.find_program_address(
        [
            bytes([98, 111, 110, 100, 105, 110, 103, 45, 99, 117, 114, 118, 101]),
            bytes(Pubkey.from_string(mint)),
        ],
        Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"),
    )
    return str(pair)


async def main() -> None:
    users = ", ".join(TWITTER_USERS)
    print(f"Sniping {users}...")

    mint = await snipe_consume()

    if not mint:
        print("Failed to find mint.")
        return

    PAIR = get_pair(mint)
    print("Pair:", PAIR)
    with open(FILE_PATH, "w") as f:
        f.write(
            f"https://photon-sol.tinyastro.io/en/lp/{PAIR}?handle=4070371e951586cba5f04"
        )
    run_script()


if __name__ == "__main__":
    asyncio.run(main())
