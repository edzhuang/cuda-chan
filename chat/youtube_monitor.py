"""YouTube Live Chat monitor."""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
import pytchat

from config.settings import settings
from utils.logger import log


class YouTubeChatMonitor:
    """Monitors YouTube live chat for messages."""

    def __init__(self, video_id: Optional[str] = None):
        """
        Initialize YouTube chat monitor.

        Args:
            video_id: YouTube video ID (uses settings if not provided)
        """
        self.video_id = video_id or settings.youtube.video_id
        self.chat: Optional[pytchat.LiveChat] = None
        self.is_monitoring = False

        # Message tracking
        self.total_messages = 0
        self.messages_this_session = 0
        self.active_users = set()

        log.info(f"YouTube chat monitor initialized for video: {self.video_id}")

    async def start(self) -> bool:
        """
        Start monitoring chat.

        Returns:
            True if started successfully
        """
        if not self.video_id:
            log.error("No video ID provided")
            return False

        try:
            log.info(f"Starting chat monitor for video: {self.video_id}")

            # Create pytchat instance
            self.chat = pytchat.create(
                video_id=self.video_id,
                interruptable=True
            )

            self.is_monitoring = True
            log.success("Chat monitor started successfully")
            return True

        except Exception as e:
            log.error(f"Failed to start chat monitor: {e}")
            return False

    async def stop(self):
        """Stop monitoring chat."""
        if self.chat:
            self.chat.terminate()
            self.chat = None

        self.is_monitoring = False
        log.info("Chat monitor stopped")

    async def get_messages(self, timeout: float = 1.0) -> List[Dict[str, Any]]:
        """
        Get new chat messages.

        Args:
            timeout: Maximum time to wait for messages

        Returns:
            List of message dictionaries
        """
        if not self.is_monitoring or not self.chat:
            return []

        messages = []

        try:
            # Get messages from pytchat
            if self.chat.is_alive():
                chat_items = self.chat.get().sync_items()

                for item in chat_items:
                    message = {
                        "author": item.author.name,
                        "author_id": item.author.channelId,
                        "text": item.message,
                        "timestamp": datetime.fromisoformat(item.datetime.replace('Z', '+00:00')),
                        "is_member": item.author.isChatSponsor,
                        "is_moderator": item.author.isChatModerator,
                        "is_owner": item.author.isChatOwner,
                        "superchat_amount": None  # pytchat doesn't provide this easily
                    }

                    messages.append(message)

                    # Track statistics
                    self.total_messages += 1
                    self.messages_this_session += 1
                    self.active_users.add(item.author.name)

                if messages:
                    log.debug(f"Received {len(messages)} new chat messages")

        except Exception as e:
            log.error(f"Error getting chat messages: {e}")

        return messages

    async def monitor_loop(self, message_callback):
        """
        Continuous monitoring loop.

        Args:
            message_callback: Async function to call with new messages
        """
        log.info("Starting chat monitor loop")

        while self.is_monitoring:
            try:
                messages = await self.get_messages()

                for message in messages:
                    await message_callback(message)

                await asyncio.sleep(0.5)  # Poll every 0.5 seconds

            except Exception as e:
                log.error(f"Monitor loop error: {e}")
                await asyncio.sleep(1.0)

        log.info("Chat monitor loop ended")

    def is_alive(self) -> bool:
        """Check if chat stream is still alive."""
        if self.chat:
            return self.chat.is_alive()
        return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get chat monitoring statistics."""
        return {
            "video_id": self.video_id,
            "is_monitoring": self.is_monitoring,
            "is_alive": self.is_alive(),
            "total_messages": self.total_messages,
            "messages_this_session": self.messages_this_session,
            "active_users_count": len(self.active_users),
            "active_users": list(self.active_users)[:10]  # First 10
        }


# Alternative implementation using official YouTube API (more reliable but requires quota)
class YouTubeChatMonitorOfficial:
    """Monitor YouTube chat using official API (requires API key)."""

    def __init__(self, video_id: Optional[str] = None):
        """Initialize official API chat monitor."""
        self.video_id = video_id or settings.youtube.video_id
        self.api_key = settings.api.youtube_api_key

        self.live_chat_id: Optional[str] = None
        self.next_page_token: Optional[str] = None
        self.polling_interval = 5000  # milliseconds

        self.is_monitoring = False
        self.total_messages = 0

        log.info("YouTube official API chat monitor initialized")

    async def start(self) -> bool:
        """Start monitoring with official API."""
        if not self.api_key:
            log.error("YouTube API key not configured")
            return False

        try:
            from googleapiclient.discovery import build

            youtube = build('youtube', 'v3', developerKey=self.api_key)

            # Get live broadcast details
            request = youtube.videos().list(
                part="liveStreamingDetails",
                id=self.video_id
            )
            response = request.execute()

            if response['items']:
                self.live_chat_id = response['items'][0]['liveStreamingDetails']['activeLiveChatId']
                self.is_monitoring = True
                log.success(f"Started official API monitoring (chat ID: {self.live_chat_id})")
                return True
            else:
                log.error("Video not found or not live")
                return False

        except Exception as e:
            log.error(f"Failed to start official API monitor: {e}")
            return False

    async def get_messages(self) -> List[Dict[str, Any]]:
        """Get messages using official API."""
        if not self.is_monitoring:
            return []

        try:
            from googleapiclient.discovery import build

            youtube = build('youtube', 'v3', developerKey=self.api_key)

            request = youtube.liveChatMessages().list(
                liveChatId=self.live_chat_id,
                part='snippet,authorDetails',
                pageToken=self.next_page_token
            )
            response = request.execute()

            messages = []
            for item in response['items']:
                snippet = item['snippet']
                author = item['authorDetails']

                message = {
                    "author": author['displayName'],
                    "author_id": author['channelId'],
                    "text": snippet['displayMessage'],
                    "timestamp": datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00')),
                    "is_member": author.get('isChatSponsor', False),
                    "is_moderator": author.get('isChatModerator', False),
                    "is_owner": author.get('isChatOwner', False),
                    "superchat_amount": None
                }

                messages.append(message)
                self.total_messages += 1

            # Update pagination token
            self.next_page_token = response.get('nextPageToken')
            self.polling_interval = response.get('pollingIntervalMillis', 5000)

            return messages

        except Exception as e:
            log.error(f"Error getting messages from official API: {e}")
            return []

    async def monitor_loop(self, message_callback):
        """Monitor loop for official API."""
        while self.is_monitoring:
            try:
                messages = await self.get_messages()

                for message in messages:
                    await message_callback(message)

                # Wait for polling interval
                await asyncio.sleep(self.polling_interval / 1000)

            except Exception as e:
                log.error(f"Official API monitor loop error: {e}")
                await asyncio.sleep(5.0)


if __name__ == "__main__":
    # Test YouTube chat monitor
    async def test_monitor():
        # Create monitor (use your video ID)
        monitor = YouTubeChatMonitor(video_id="test_video_id")

        # Message callback
        async def on_message(message):
            print(f"{message['author']}: {message['text']}")

        # Start monitoring
        if await monitor.start():
            # Run for 30 seconds
            try:
                await asyncio.wait_for(
                    monitor.monitor_loop(on_message),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                pass

            await monitor.stop()

            print(f"\nStatistics: {monitor.get_statistics()}")
        else:
            print("Failed to start monitor")

    # Uncomment to test (requires live video ID)
    # asyncio.run(test_monitor())
    print("YouTube chat monitor module loaded. Requires live video ID to test.")
