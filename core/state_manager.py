"""State management for CUDA-chan system."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from utils.logger import log


class SystemState(Enum):
    """Overall system state."""
    INITIALIZING = "initializing"
    IDLE = "idle"
    CHATTING = "chatting"
    GAMING = "gaming"
    RESPONDING = "responding"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"


class EmotionalState(Enum):
    """CUDA-chan's emotional state."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    EXCITED = "excited"
    FOCUSED = "focused"
    SAD = "sad"
    SURPRISED = "surprised"
    THINKING = "thinking"


@dataclass
class GameState:
    """State of current game session."""
    game_name: str = "none"
    is_active: bool = False
    start_time: Optional[datetime] = None
    current_goal: str = "Exploring"
    recent_outcomes: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "game_name": self.game_name,
            "is_active": self.is_active,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "current_goal": self.current_goal,
            "recent_outcomes": self.recent_outcomes[-5:],  # Last 5
            "achievements": self.achievements
        }


@dataclass
class ChatContext:
    """Context from chat interactions."""
    recent_messages: List[Dict[str, Any]] = field(default_factory=list)
    mentioned_recently: bool = False
    last_response_time: Optional[datetime] = None
    active_users: set = field(default_factory=set)

    def add_message(self, author: str, text: str, timestamp: Optional[datetime] = None):
        """Add a chat message to context."""
        if timestamp is None:
            timestamp = datetime.now()

        self.recent_messages.append({
            "author": author,
            "text": text,
            "timestamp": timestamp
        })

        # Keep only last 20 messages
        if len(self.recent_messages) > 20:
            self.recent_messages = self.recent_messages[-20:]

        # Track active users
        self.active_users.add(author)

    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages."""
        return self.recent_messages[-limit:]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "recent_messages": self.recent_messages[-10:],
            "mentioned_recently": self.mentioned_recently,
            "last_response_time": self.last_response_time.isoformat() if self.last_response_time else None,
            "active_user_count": len(self.active_users)
        }


@dataclass
class ActionHistory:
    """History of actions taken."""
    actions: List[Dict[str, Any]] = field(default_factory=list)
    max_history: int = 50

    def add_action(self, action_type: str, details: Any, outcome: Optional[str] = None):
        """Add an action to history."""
        self.actions.append({
            "type": action_type,
            "details": details,
            "outcome": outcome,
            "timestamp": datetime.now()
        })

        # Limit history size
        if len(self.actions) > self.max_history:
            self.actions = self.actions[-self.max_history:]

    def get_recent_actions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent actions."""
        return self.actions[-limit:]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "recent_actions": [
                {
                    "type": a["type"],
                    "details": str(a["details"])[:100],  # Truncate long details
                    "outcome": a["outcome"],
                    "timestamp": a["timestamp"].isoformat()
                }
                for a in self.actions[-10:]
            ]
        }


class StateManager:
    """Manages global system state."""

    def __init__(self):
        """Initialize state manager."""
        self.system_state = SystemState.INITIALIZING
        self.emotional_state = EmotionalState.NEUTRAL
        self.game_state = GameState()
        self.chat_context = ChatContext()
        self.action_history = ActionHistory()

        self.start_time = datetime.now()
        self.last_update = datetime.now()

        # Tracking flags
        self.is_speaking = False
        self.is_listening = False
        self.screen_capture_enabled = True

        log.info("State manager initialized")

    def update_system_state(self, new_state: SystemState):
        """Update system state."""
        old_state = self.system_state
        self.system_state = new_state
        self.last_update = datetime.now()
        log.info(f"System state changed: {old_state.value} -> {new_state.value}")

    def update_emotional_state(self, new_emotion: EmotionalState):
        """Update emotional state."""
        old_emotion = self.emotional_state
        self.emotional_state = new_emotion
        self.last_update = datetime.now()
        log.debug(f"Emotional state changed: {old_emotion.value} -> {new_emotion.value}")

    def start_game(self, game_name: str, goal: str = "Exploring"):
        """Start a game session."""
        self.game_state = GameState(
            game_name=game_name,
            is_active=True,
            start_time=datetime.now(),
            current_goal=goal
        )
        self.update_system_state(SystemState.GAMING)
        log.info(f"Started game: {game_name}")

    def end_game(self):
        """End current game session."""
        if self.game_state.is_active:
            game_name = self.game_state.game_name
            self.game_state.is_active = False
            self.update_system_state(SystemState.IDLE)
            log.info(f"Ended game: {game_name}")

    def update_game_goal(self, goal: str):
        """Update current game goal."""
        self.game_state.current_goal = goal
        log.debug(f"Game goal updated: {goal}")

    def add_game_outcome(self, outcome: str):
        """Add game outcome/result."""
        self.game_state.recent_outcomes.append(outcome)
        # Keep only last 10 outcomes
        if len(self.game_state.recent_outcomes) > 10:
            self.game_state.recent_outcomes = self.game_state.recent_outcomes[-10:]
        log.debug(f"Game outcome recorded: {outcome}")

    def add_achievement(self, achievement: str):
        """Add game achievement."""
        self.game_state.achievements.append(achievement)
        log.info(f"Achievement unlocked: {achievement}")

    def get_context_for_ai(self) -> dict:
        """Get current context formatted for AI decision-making."""
        return {
            "system_state": self.system_state.value,
            "emotional_state": self.emotional_state.value,
            "current_game": self.game_state.game_name if self.game_state.is_active else "idle",
            "current_goal": self.game_state.current_goal,
            "recent_chat": self.chat_context.get_recent_messages(limit=10),
            "recent_actions": self.action_history.get_recent_actions(limit=5),
            "is_speaking": self.is_speaking,
            "active_user_count": len(self.chat_context.active_users),
            "uptime_minutes": (datetime.now() - self.start_time).total_seconds() / 60
        }

    def get_full_state(self) -> dict:
        """Get complete state snapshot."""
        return {
            "system_state": self.system_state.value,
            "emotional_state": self.emotional_state.value,
            "game_state": self.game_state.to_dict(),
            "chat_context": self.chat_context.to_dict(),
            "action_history": self.action_history.to_dict(),
            "flags": {
                "is_speaking": self.is_speaking,
                "is_listening": self.is_listening,
                "screen_capture_enabled": self.screen_capture_enabled
            },
            "timing": {
                "start_time": self.start_time.isoformat(),
                "last_update": self.last_update.isoformat(),
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
            }
        }

    def is_busy(self) -> bool:
        """Check if system is busy (can't be interrupted)."""
        return self.system_state in [
            SystemState.INITIALIZING,
            SystemState.SHUTTING_DOWN,
            SystemState.ERROR
        ] or self.is_speaking

    def should_respond_to_chat(self) -> bool:
        """Check if system should respond to chat."""
        return self.system_state in [
            SystemState.IDLE,
            SystemState.CHATTING,
            SystemState.GAMING
        ] and not self.is_speaking

    def reset_to_idle(self):
        """Reset to idle state."""
        self.update_system_state(SystemState.IDLE)
        self.update_emotional_state(EmotionalState.NEUTRAL)
        if self.game_state.is_active:
            self.end_game()
        log.info("State reset to idle")


if __name__ == "__main__":
    # Test the state manager
    manager = StateManager()

    print(f"Initial state: {manager.system_state.value}")

    # Simulate starting a game
    manager.start_game("Test Game", "Complete the level")
    print(f"Game state: {manager.game_state.to_dict()}")

    # Add some chat messages
    manager.chat_context.add_message("User1", "Hello CUDA-chan!")
    manager.chat_context.add_message("User2", "How are you doing?")
    print(f"Chat context: {manager.chat_context.to_dict()}")

    # Get AI context
    context = manager.get_context_for_ai()
    print(f"\nAI Context:")
    for key, value in context.items():
        print(f"  {key}: {value}")
