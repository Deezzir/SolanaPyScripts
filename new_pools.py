import aiohttp
import asyncio
from typing import List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger("NewPoolsProcessor")


class RecentLaunchesProcessor:
    def __init__(self, api_url: str, interval: int = 1):
        self.api_url = api_url
        self.interval = interval
        self.most_recent_timestamp: Optional[datetime] = None
        self.session = aiohttp.ClientSession()

    async def fetch_recent_launches(self) -> List[dict]:
        """
        Fetches recent launches from the API asynchronously.
        Returns a list of launch items.
        """
        async with self.session.get(self.api_url) as response:
            response.raise_for_status()
            return await response.json()

    async def process_launches(self, launches: List[dict]) -> None:
        """
        Processes the new launches.
        """
        for launch in launches:
            LOGGER.info(f"Processing launch: {launch}")

    async def clean_up(self):
        """
        Closes the aiohttp session.
        """
        await self.session.close()

    async def run(self):
        while True:
            try:
                launches = await self.fetch_recent_launches()

                if self.most_recent_timestamp:
                    new_launches = [
                        launch
                        for launch in launches
                        if datetime.strptime(
                            launch["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ"
                        )
                        > self.most_recent_timestamp
                    ]
                else:
                    new_launches = launches

                if new_launches:
                    await self.process_launches(new_launches)

                    self.most_recent_timestamp = max(
                        datetime.strptime(launch["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ")
                        for launch in new_launches
                    )

                await asyncio.sleep(self.interval)
            except Exception as e:
                LOGGER.error(f"Error occurred: {e}")
                await asyncio.sleep(5)


# Example usage
if __name__ == "__main__":
    pass
