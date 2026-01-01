"""Priority-based event queue for CUDA-chan."""

import asyncio
from enum import IntEnum
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
from utils.logger import log


class Priority(IntEnum):
    """Event priority levels (lower number = higher priority)."""
    CRITICAL = 0  # System errors, emergency stops
    HIGH = 1      # Chat messages with mentions, direct interactions
    MEDIUM = 2    # Game state changes, regular chat
    LOW = 3       # Idle behaviors, autonomous actions
    BACKGROUND = 4  # Logging, cleanup tasks


@dataclass(order=True)
class Event:
    """Event with priority and data."""
    priority: Priority = field(compare=True)
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp(), compare=True)
    event_type: str = field(default="", compare=False)
    data: Any = field(default=None, compare=False)
    source: str = field(default="unknown", compare=False)
    id: str = field(default_factory=lambda: f"evt_{datetime.now().timestamp()}", compare=False)

    def __post_init__(self):
        """Ensure timestamp is set if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now().timestamp()


class EventQueue:
    """Async priority queue for event management."""

    def __init__(self, max_size: int = 1000):
        """
        Initialize event queue.

        Args:
            max_size: Maximum queue size (0 = unlimited)
        """
        self.max_size = max_size
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_size)
        self._processed_count = 0
        self._dropped_count = 0
        log.info(f"Event queue initialized with max_size={max_size}")

    async def put(
        self,
        event_type: str,
        data: Any,
        priority: Priority = Priority.MEDIUM,
        source: str = "unknown"
    ) -> bool:
        """
        Add event to queue.

        Args:
            event_type: Type of event (e.g., "chat_message", "game_action")
            data: Event data
            priority: Event priority level
            source: Source of the event

        Returns:
            True if event was added, False if queue is full
        """
        event = Event(
            priority=priority,
            event_type=event_type,
            data=data,
            source=source
        )

        try:
            await self._queue.put(event)
            log.debug(f"Event queued: {event_type} (priority={priority.name}, source={source})")
            return True
        except asyncio.QueueFull:
            self._dropped_count += 1
            log.warning(f"Event queue full! Dropped event: {event_type} from {source}")
            return False

    async def get(self, timeout: Optional[float] = None) -> Optional[Event]:
        """
        Get next event from queue (highest priority first).

        Args:
            timeout: Maximum time to wait for event (None = wait forever)

        Returns:
            Next event or None if timeout reached
        """
        try:
            if timeout:
                event = await asyncio.wait_for(self._queue.get(), timeout=timeout)
            else:
                event = await self._queue.get()

            self._processed_count += 1
            log.debug(f"Event retrieved: {event.event_type} (priority={event.priority.name})")
            return event

        except asyncio.TimeoutError:
            return None

    def put_nowait(
        self,
        event_type: str,
        data: Any,
        priority: Priority = Priority.MEDIUM,
        source: str = "unknown"
    ) -> bool:
        """
        Add event to queue without waiting.

        Args:
            event_type: Type of event
            data: Event data
            priority: Event priority level
            source: Source of the event

        Returns:
            True if event was added, False if queue is full
        """
        event = Event(
            priority=priority,
            event_type=event_type,
            data=data,
            source=source
        )

        try:
            self._queue.put_nowait(event)
            log.debug(f"Event queued (nowait): {event_type} (priority={priority.name})")
            return True
        except asyncio.QueueFull:
            self._dropped_count += 1
            log.warning(f"Event queue full! Dropped event: {event_type}")
            return False

    def get_nowait(self) -> Optional[Event]:
        """
        Get next event without waiting.

        Returns:
            Next event or None if queue is empty
        """
        try:
            event = self._queue.get_nowait()
            self._processed_count += 1
            log.debug(f"Event retrieved (nowait): {event.event_type}")
            return event
        except asyncio.QueueEmpty:
            return None

    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()

    def qsize(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    def get_stats(self) -> dict:
        """Get queue statistics."""
        return {
            "current_size": self.qsize(),
            "max_size": self.max_size,
            "processed_count": self._processed_count,
            "dropped_count": self._dropped_count,
            "is_empty": self.empty()
        }

    async def clear(self):
        """Clear all events from queue."""
        count = 0
        while not self.empty():
            try:
                self._queue.get_nowait()
                count += 1
            except asyncio.QueueEmpty:
                break
        log.info(f"Event queue cleared ({count} events removed)")

    async def wait_for_event(self, event_type: str, timeout: Optional[float] = None) -> Optional[Event]:
        """
        Wait for a specific event type.

        Args:
            event_type: Event type to wait for
            timeout: Maximum time to wait

        Returns:
            Event if found, None if timeout
        """
        start_time = datetime.now().timestamp()

        while True:
            if timeout and (datetime.now().timestamp() - start_time) > timeout:
                log.warning(f"Timeout waiting for event: {event_type}")
                return None

            event = await self.get(timeout=1.0)  # Check every second

            if event and event.event_type == event_type:
                return event
            elif event:
                # Re-queue event if it's not the one we're looking for
                await self._queue.put(event)


# Event type constants for consistency
class EventType:
    """Standard event types."""
    # Chat events
    CHAT_MESSAGE = "chat_message"
    CHAT_COMMAND = "chat_command"

    # Game events
    GAME_STATE_CHANGE = "game_state_change"
    GAME_ACTION_COMPLETE = "game_action_complete"
    GAME_START = "game_start"
    GAME_END = "game_end"

    # System events
    SYSTEM_ERROR = "system_error"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_STARTUP = "system_startup"

    # Output events
    TTS_COMPLETE = "tts_complete"
    EXPRESSION_CHANGE = "expression_change"

    # Autonomous behavior
    IDLE_ACTION = "idle_action"
    AUTONOMOUS_DECISION = "autonomous_decision"


if __name__ == "__main__":
    # Test the event queue
    async def test_queue():
        queue = EventQueue(max_size=10)

        # Add events with different priorities
        await queue.put("low_priority_task", {"data": "test"}, Priority.LOW)
        await queue.put("high_priority_task", {"data": "urgent"}, Priority.HIGH)
        await queue.put("medium_priority_task", {"data": "normal"}, Priority.MEDIUM)
        await queue.put("critical_task", {"data": "emergency"}, Priority.CRITICAL)

        print(f"Queue size: {queue.qsize()}")

        # Events should come out in priority order
        while not queue.empty():
            event = await queue.get()
            print(f"Processing: {event.event_type} (priority={event.priority.name})")

        print(f"Stats: {queue.get_stats()}")

    asyncio.run(test_queue())
