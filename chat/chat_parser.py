"""Chat message parser and processor."""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict

from config.settings import settings
from core.event_queue import Priority
from utils.logger import log


class ChatParser:
    """Parses and categorizes chat messages."""

    def __init__(self):
        """Initialize chat parser."""
        self.bot_name = settings.personality.name.lower()

        # Spam detection
        self.user_message_history = defaultdict(list)
        self.spam_threshold = 3  # messages
        self.spam_window = 5.0  # seconds

        # Command prefix
        self.command_prefix = "!"

        log.info(f"Chat parser initialized (bot name: {self.bot_name})")

    def parse_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and enrich a chat message.

        Args:
            message: Raw message dictionary

        Returns:
            Enriched message with parsed information
        """
        text = message.get("text", "").strip()
        author = message.get("author", "Unknown")

        # Create enriched message
        parsed = message.copy()
        parsed["original_text"] = text
        parsed["text_lower"] = text.lower()

        # Check if bot is mentioned
        parsed["mentions_bot"] = self._check_mention(text)

        # Check if it's a command
        parsed["is_command"] = text.startswith(self.command_prefix)
        if parsed["is_command"]:
            parsed["command"], parsed["command_args"] = self._parse_command(text)
        else:
            parsed["command"] = None
            parsed["command_args"] = []

        # Detect message intent
        parsed["intent"] = self._detect_intent(text)

        # Calculate priority
        parsed["priority"] = self._calculate_priority(parsed)

        # Check for spam
        parsed["is_spam"] = self._is_spam(author, text)

        # Extract emojis and special characters
        parsed["has_emojis"] = self._has_emojis(text)

        # Check for questions
        parsed["is_question"] = "?" in text

        log.debug(f"Parsed message from {author}: priority={parsed['priority'].name}, mentions={parsed['mentions_bot']}")

        return parsed

    def _check_mention(self, text: str) -> bool:
        """Check if message mentions the bot."""
        text_lower = text.lower()

        # Direct name mention
        if self.bot_name in text_lower:
            return True

        # Common mention patterns
        mention_patterns = [
            r'\b(hey|hi|hello)\s+(cuda|bot)\b',
            r'@\s*cuda',
        ]

        for pattern in mention_patterns:
            if re.search(pattern, text_lower):
                return True

        return False

    def _parse_command(self, text: str) -> tuple[Optional[str], List[str]]:
        """
        Parse command from message.

        Args:
            text: Message text

        Returns:
            Tuple of (command, arguments)
        """
        if not text.startswith(self.command_prefix):
            return None, []

        parts = text[1:].split()  # Remove prefix and split
        if not parts:
            return None, []

        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        return command, args

    def _detect_intent(self, text: str) -> str:
        """
        Detect the intent of the message.

        Args:
            text: Message text

        Returns:
            Intent category
        """
        text_lower = text.lower()

        # Greeting
        if any(word in text_lower for word in ['hello', 'hi', 'hey', 'greetings', 'sup']):
            return "greeting"

        # Question
        if "?" in text or any(word in text_lower for word in ['what', 'how', 'why', 'when', 'where', 'who']):
            return "question"

        # Suggestion/advice
        if any(word in text_lower for word in ['try', 'should', 'could', 'maybe', 'suggest']):
            return "suggestion"

        # Encouragement
        if any(word in text_lower for word in ['good job', 'nice', 'great', 'awesome', 'amazing', 'poggers']):
            return "encouragement"

        # Game-specific
        if any(word in text_lower for word in ['play', 'game', 'level', 'move', 'jump', 'attack']):
            return "game_related"

        return "general"

    def _calculate_priority(self, parsed_message: Dict[str, Any]) -> Priority:
        """
        Calculate message priority.

        Args:
            parsed_message: Parsed message dictionary

        Returns:
            Priority level
        """
        # Commands are high priority
        if parsed_message.get("is_command"):
            return Priority.HIGH

        # Direct mentions are high priority
        if parsed_message.get("mentions_bot"):
            return Priority.HIGH

        # Questions are medium-high priority
        if parsed_message.get("is_question"):
            return Priority.MEDIUM

        # Moderators/members get slightly higher priority
        if parsed_message.get("is_moderator") or parsed_message.get("is_member"):
            return Priority.MEDIUM

        # Owner messages are critical
        if parsed_message.get("is_owner"):
            return Priority.CRITICAL

        # Everything else is medium
        return Priority.MEDIUM

    def _is_spam(self, author: str, text: str) -> bool:
        """
        Check if message is spam.

        Args:
            author: Message author
            text: Message text

        Returns:
            True if spam
        """
        now = datetime.now()

        # Add to history
        self.user_message_history[author].append({
            "text": text,
            "timestamp": now
        })

        # Remove old messages from history
        cutoff_time = now - timedelta(seconds=self.spam_window)
        self.user_message_history[author] = [
            msg for msg in self.user_message_history[author]
            if msg["timestamp"] > cutoff_time
        ]

        # Check for spam
        recent_count = len(self.user_message_history[author])

        if recent_count > self.spam_threshold:
            log.warning(f"Spam detected from {author}: {recent_count} messages in {self.spam_window}s")
            return True

        # Check for repeated messages
        if recent_count >= 2:
            recent_texts = [msg["text"] for msg in self.user_message_history[author][-2:]]
            if recent_texts[0] == recent_texts[1]:
                log.warning(f"Repeated message spam from {author}")
                return True

        return False

    def _has_emojis(self, text: str) -> bool:
        """Check if text contains emojis."""
        # Simple emoji detection (Unicode ranges)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        return bool(emoji_pattern.search(text))

    def should_respond(self, parsed_message: Dict[str, Any]) -> bool:
        """
        Determine if bot should respond to this message.

        Args:
            parsed_message: Parsed message

        Returns:
            True if should respond
        """
        # Don't respond to spam
        if parsed_message.get("is_spam"):
            return False

        # Always respond to mentions and commands
        if parsed_message.get("mentions_bot") or parsed_message.get("is_command"):
            return True

        # Respond to questions sometimes (to avoid overwhelming chat)
        if parsed_message.get("is_question"):
            # Could add random chance here
            return True

        # Don't respond to every general message
        return False

    def extract_game_suggestions(self, text: str) -> Optional[str]:
        """
        Extract game suggestions from text.

        Args:
            text: Message text

        Returns:
            Game name if found
        """
        text_lower = text.lower()

        # Common game mentions
        game_keywords = {
            'minecraft': 'minecraft',
            'osu': 'osu',
            '2048': '2048',
            'tetris': 'tetris',
            'chess': 'chess',
        }

        for keyword, game_name in game_keywords.items():
            if keyword in text_lower:
                return game_name

        # Generic "play [game]" pattern
        play_match = re.search(r'play\s+(\w+)', text_lower)
        if play_match:
            return play_match.group(1)

        return None

    def get_sentiment(self, text: str) -> str:
        """
        Simple sentiment analysis.

        Args:
            text: Message text

        Returns:
            Sentiment: positive, negative, or neutral
        """
        text_lower = text.lower()

        positive_words = ['good', 'great', 'awesome', 'love', 'nice', 'poggers', 'amazing', 'cool']
        negative_words = ['bad', 'terrible', 'hate', 'awful', 'boring', 'sad', 'fail']

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"


if __name__ == "__main__":
    # Test chat parser
    parser = ChatParser()

    test_messages = [
        {"author": "User1", "text": "Hey CUDA-chan, how are you?"},
        {"author": "User2", "text": "!help"},
        {"author": "User3", "text": "You should try playing Minecraft!"},
        {"author": "User1", "text": "spam"},
        {"author": "User1", "text": "spam"},
        {"author": "User1", "text": "spam"},  # This should be detected as spam
        {"author": "User4", "text": "Great job! Keep it up!"},
    ]

    print("Testing chat parser:\n")
    for msg in test_messages:
        parsed = parser.parse_message(msg)
        print(f"Author: {parsed['author']}")
        print(f"Text: {parsed['text']}")
        print(f"Mentions bot: {parsed['mentions_bot']}")
        print(f"Is command: {parsed['is_command']}")
        print(f"Priority: {parsed['priority'].name}")
        print(f"Intent: {parsed['intent']}")
        print(f"Is spam: {parsed['is_spam']}")
        print(f"Should respond: {parser.should_respond(parsed)}")
        print()
