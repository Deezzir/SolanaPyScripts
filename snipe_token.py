import asyncio
import aiohttp
from dotenv import load_dotenv
import socketio  # type: ignore
import subprocess
import os
from typing import Optional
from aiohttp import ClientSession
from asyncstdlib import enumerate
from jsonrpcclient import request, parse, Ok
from solana.rpc.async_api import AsyncClient
from solana.rpc.websocket_api import connect as ws_connect
from solders.pubkey import Pubkey  # type: ignore
from solders.signature import Signature  # type: ignore
from solders.keypair import Keypair  # type: ignore
from solana.rpc.types import MemcmpOpts, Commitment
from solders.transaction_status import (  # type: ignore
    UiTransaction,
    EncodedTransactionWithStatusMeta,
    UiPartiallyDecodedInstruction,
)
from solders.transaction_status import ParsedInstruction, ParsedAccount  # type: ignore
from solders.rpc.responses import GetTransactionResp  # type: ignore
from solders.rpc.config import RpcTransactionLogsFilterMentions  # type: ignore
from spl.token.async_client import AsyncToken
from spl.token.constants import TOKEN_PROGRAM_ID
import logging
import base58
from construct import Struct, Int8ul, Int32ul, Bytes, GreedyBytes, Int16ul

load_dotenv()
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("snipe_token")


NAME = "TESTBABA"
TICKER = "BABUN"


SIO = socketio.AsyncClient()
RPC = os.getenv("RPC", "")
MINT: Optional[str] = None
PAIR: Optional[str] = None
SUBSCRIPTION_ID: Optional[int] = None

desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
directory = os.path.join(desktop_path, "scripts", "solana-bots")
file_name = "pair.txt"
file_path = os.path.join(directory, file_name)
os.makedirs(directory, exist_ok=True)
script_path = os.path.join(
    desktop_path, "scripts", "solana-bots", "scripts", "!1open-all-profiles-test.scpt"
)
command = ["osascript", script_path]

METADATA_SCHEMA = Struct(
    "key" / Int8ul,
    "name_length" / Int32ul,
    "name" / Bytes(lambda this: this.name_length),
    "symbol_length" / Int32ul,
    "symbol" / Bytes(lambda this: this.symbol_length),
    "uri_length" / Int32ul,
    "uri" / Bytes(lambda this: this.uri_length),
    "other" / GreedyBytes,
)


def deserialize_metadata(data_base58: str) -> tuple:
    metadata_bytes = base58.b58decode(data_base58)
    metadata = METADATA_SCHEMA.parse(metadata_bytes)

    name = metadata.name.decode("utf-8")
    symbol = metadata.symbol.decode("utf-8")
    uri = metadata.uri.decode("utf-8")

    return name, symbol, uri


def find_instruction_by_program_id(
    transaction: EncodedTransactionWithStatusMeta, target_program_id: Pubkey
) -> Optional[str]:
    if not transaction.meta or not transaction.meta.inner_instructions:
        return None

    for inner_instruction in transaction.meta.inner_instructions:
        for instruction in inner_instruction.instructions:
            if (
                isinstance(instruction, UiPartiallyDecodedInstruction)
                and instruction.program_id == target_program_id
            ):
                return instruction.data

    return None


async def process_log(client: AsyncClient, log: dict) -> bool:
    global MINT

    value = log[0].result.value
    if value.err:
        return False
    if "Program log: Instruction: Create" in value.logs:
        sig = value.signature
        if sig == Signature.from_string(
            "1111111111111111111111111111111111111111111111111111111111111111"
        ):
            return False
        await asyncio.sleep(0.5)
        tx = GetTransactionResp(None)
        while True:
            tx = await client.get_transaction(
                sig, "jsonParsed", Commitment("confirmed"), 0
            )
            if tx != GetTransactionResp(None):
                break
            else:
                LOGGER.warning(f"Failed to get transaction {sig}, retrying...")
                await asyncio.sleep(0.5)
        if (
            tx.value
            and tx.value.transaction
            and isinstance(tx.value.transaction.transaction, UiTransaction)
        ):
            print(f"Found the create token tx: {sig}")
            instruction_data = find_instruction_by_program_id(
                tx.value.transaction,
                Pubkey.from_string("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s"),
            )
            if instruction_data:
                name, symbol, _ = deserialize_metadata(instruction_data)
                print(f"CHECKING Token: {name} | Ticker: {symbol} (Program Logs)")
                if name.lower() == NAME.lower() and symbol.lower() == TICKER.lower():
                    pubkeys_parsed = (
                        tx.value.transaction.transaction.message.account_keys
                    )
                    if isinstance(pubkeys_parsed[1], Pubkey):
                        MINT = str(pubkeys_parsed[1])
                    elif isinstance(pubkeys_parsed[1], ParsedAccount):
                        MINT = str(pubkeys_parsed[1].pubkey)
                    print(f"PROGRAM LOGS: Found the token {MINT}")
                    return True
    return False


@SIO.event
async def connect() -> None:
    LOGGER.info("Connection to API WS established")


@SIO.event
async def newCoinCreated(data) -> None:
    global NAME
    global TICKER
    global MINT

    name = data["name"]
    ticker = data["symbol"]
    if ticker[0] == "$":
        ticker = ticker[1:]

    print(f"CHECKING Token: {name} | Ticker: {ticker} (Api Logs)")

    if name.lower() == NAME.lower() and ticker.lower() == TICKER.lower():
        MINT = data["mint"]
        print(f"API LOGS: Found the token {MINT}")
        await SIO.disconnect()


async def snipe_program_logs():
    global SUBSCRIPTION_ID

    async with AsyncClient(f"https://{RPC}") as client:
        async with ws_connect(f"wss://{RPC}") as websocket:
            try:
                await websocket.logs_subscribe(
                    RpcTransactionLogsFilterMentions(
                        Pubkey.from_string(
                            "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
                        )
                    ),
                    "confirmed",
                )
                LOGGER.info("Subscribed to logs. Waiting for messages...")
                first_resp = await websocket.recv()
                SUBSCRIPTION_ID = first_resp[0].result

                async for log in websocket:
                    found = await process_log(client, log)
                    if found:
                        return
            except KeyboardInterrupt:
                LOGGER.info("Keyboard interrupt received. Cancelling tasks...")
            except asyncio.CancelledError:
                LOGGER.info("Program Logs Task was cancelled.")
            finally:
                if SUBSCRIPTION_ID:
                    await websocket.logs_unsubscribe(SUBSCRIPTION_ID)
                LOGGER.info("Cleaned up resources.")


@SIO.event
async def disconnect() -> None:
    LOGGER.info("Disconnected from server")


async def snipe_api_logs() -> bool:
    try:
        await SIO.connect(
            "https://frontend-api.pump.fun?offset=0&limit=100&sort=last_trade_timestamp&order=DESC&includeNsfw=true",
            transports=["websocket"],
            socketio_path="/socket.io/",
        )
        LOGGER.info("Connected, waiting for messages...")
        await SIO.wait()
    except asyncio.CancelledError:
        LOGGER.info("Api Logs Task was cancelled.")
        return False
    return True


def get_pair(mint: str) -> str:
    pair, _ = Pubkey.find_program_address(
        [
            bytes([98, 111, 110, 100, 105, 110, 103, 45, 99, 117, 114, 118, 101]),
            bytes(Pubkey.from_string(mint)),
        ],
        Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"),
    )
    return str(pair)


def run_script() -> None:
    try:
        subprocess.run(command, check=True)
        LOGGER.info("AppleScript executed successfully.")
    except subprocess.CalledProcessError as e:
        LOGGER.error(f"An error occurred while executing the AppleScript: {e}")


async def main() -> None:
    LOGGER.info(f"Sniping: Token {NAME} | Ticker: (${TICKER})")

    snipe_program_logs_task = asyncio.create_task(snipe_program_logs())
    snipe_api_logs_task = asyncio.create_task(snipe_api_logs())

    try:
        await asyncio.wait(
            [snipe_program_logs_task, snipe_api_logs_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
    except asyncio.CancelledError:
        LOGGER.info("Tasks was cancelled.")
        return

    if MINT:
        ("Found mint:", MINT)
        snipe_api_logs_task.cancel()
        snipe_program_logs_task.cancel()
    else:
        LOGGER.error("Failed to find mint.")
        return

    PAIR = get_pair(MINT)
    print("Pair:", PAIR)
    with open(file_path, "w") as f:
        f.write(
            f"https://photon-sol.tinyastro.io/en/lp/{PAIR}?handle=4070371e951586cba5f04"
        )
    run_script()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("Exiting...")
        exit(0)
