"""Parser for Claude AI responses."""

import re
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
from utils.logger import log


class ActionType(Enum):
    """Types of actions CUDA-chan can take."""
    SPEAK = "speak"
    EMOTION = "emotion"
    ACTION = "action"
    THINK = "think"
    UNKNOWN = "unknown"


@dataclass
class ParsedResponse:
    """Parsed AI response."""
    action_type: ActionType
    content: str
    raw_response: str
    confidence: float = 1.0  # How confident we are in the parsing
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ResponseParser:
    """Parser for Claude's action responses."""

    # Regex patterns for parsing responses
    PATTERNS = {
        ActionType.SPEAK: [
            r'^SPEAK:\s*(.+)$',
            r'^speak:\s*(.+)$',
            r'^\[SPEAK\]\s*(.+)$',
        ],
        ActionType.EMOTION: [
            r'^EMOTION:\s*(\w+)$',
            r'^emotion:\s*(\w+)$',
            r'^\[EMOTION\]\s*(\w+)$',
        ],
        ActionType.ACTION: [
            r'^ACTION:\s*(.+)$',
            r'^action:\s*(.+)$',
            r'^\[ACTION\]\s*(.+)$',
        ],
        ActionType.THINK: [
            r'^THINK:\s*(.+)$',
            r'^think:\s*(.+)$',
            r'^\[THINK\]\s*(.+)$',
        ],
    }

    VALID_EMOTIONS = {
        'happy', 'sad', 'excited', 'focused', 'surprised', 'neutral',
        'thinking', 'confused', 'angry', 'joy', 'fear'
    }

    def __init__(self):
        """Initialize response parser."""
        log.debug("Response parser initialized")

    def parse(self, response: str) -> ParsedResponse:
        """
        Parse Claude's response into an action.

        Args:
            response: Raw response from Claude

        Returns:
            Parsed response object
        """
        if not response or not response.strip():
            log.warning("Empty response received")
            return ParsedResponse(
                action_type=ActionType.UNKNOWN,
                content="",
                raw_response=response,
                confidence=0.0
            )

        response = response.strip()

        # Try to match each action type
        for action_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                match = re.match(pattern, response, re.IGNORECASE | re.MULTILINE)
                if match:
                    content = match.group(1).strip()

                    # Validate emotion if it's an EMOTION action
                    if action_type == ActionType.EMOTION:
                        content = content.lower()
                        if content not in self.VALID_EMOTIONS:
                            log.warning(f"Invalid emotion: {content}, defaulting to neutral")
                            content = "neutral"

                    log.debug(f"Parsed {action_type.value}: {content[:50]}...")

                    return ParsedResponse(
                        action_type=action_type,
                        content=content,
                        raw_response=response,
                        confidence=1.0
                    )

        # If no pattern matched, try to infer the action
        return self._infer_action(response)

    def _infer_action(self, response: str) -> ParsedResponse:
        """
        Try to infer the action type from an unparsed response.

        Args:
            response: Raw response text

        Returns:
            Inferred parsed response
        """
        response_lower = response.lower()

        # If it's a single word emotion
        if response_lower in self.VALID_EMOTIONS:
            log.warning(f"Inferred EMOTION from unparsed response: {response}")
            return ParsedResponse(
                action_type=ActionType.EMOTION,
                content=response_lower,
                raw_response=response,
                confidence=0.7
            )

        # If it looks like speech (natural sentence)
        if any(marker in response_lower for marker in ['!', '?', 'i ', 'you ', 'we ', 'chat']):
            log.warning(f"Inferred SPEAK from unparsed response: {response[:50]}...")
            return ParsedResponse(
                action_type=ActionType.SPEAK,
                content=response,
                raw_response=response,
                confidence=0.6
            )

        # If it contains action words
        action_words = ['press', 'click', 'move', 'type', 'key', 'mouse']
        if any(word in response_lower for word in action_words):
            log.warning(f"Inferred ACTION from unparsed response: {response[:50]}...")
            return ParsedResponse(
                action_type=ActionType.ACTION,
                content=response,
                raw_response=response,
                confidence=0.6
            )

        # Default to SPEAK (safest fallback)
        log.warning(f"Could not parse response, defaulting to SPEAK: {response[:50]}...")
        return ParsedResponse(
            action_type=ActionType.SPEAK,
            content=response,
            raw_response=response,
            confidence=0.3
        )

    def validate_action(self, parsed: ParsedResponse) -> bool:
        """
        Validate that a parsed action is safe and valid.

        Args:
            parsed: Parsed response

        Returns:
            True if valid, False otherwise
        """
        if parsed.action_type == ActionType.UNKNOWN:
            return False

        if parsed.action_type == ActionType.SPEAK:
            # Check for excessively long speech
            if len(parsed.content) > 500:
                log.warning(f"Speech too long ({len(parsed.content)} chars), truncating")
                parsed.content = parsed.content[:500] + "..."

        if parsed.action_type == ActionType.EMOTION:
            # Emotion must be valid
            if parsed.content.lower() not in self.VALID_EMOTIONS:
                log.error(f"Invalid emotion in validated action: {parsed.content}")
                return False

        if parsed.action_type == ActionType.ACTION:
            # Basic validation for game actions (more in action_validator.py)
            dangerous_keywords = ['rm ', 'del ', 'format', 'shutdown', 'alt+f4', 'cmd+q']
            if any(keyword in parsed.content.lower() for keyword in dangerous_keywords):
                log.error(f"Dangerous action blocked: {parsed.content}")
                return False

        return True

    def parse_multiple(self, response: str) -> list[ParsedResponse]:
        """
        Parse response that may contain multiple actions.

        Args:
            response: Raw response text

        Returns:
            List of parsed responses
        """
        # Split by lines and try to parse each
        lines = [line.strip() for line in response.split('\n') if line.strip()]

        parsed_list = []
        for line in lines:
            parsed = self.parse(line)
            if parsed.action_type != ActionType.UNKNOWN:
                parsed_list.append(parsed)

        # If no valid actions found, parse the whole response as one
        if not parsed_list:
            parsed_list.append(self.parse(response))

        return parsed_list


if __name__ == "__main__":
    # Test the parser
    parser = ResponseParser()

    test_responses = [
        "SPEAK: Hello everyone! How are you all doing today?",
        "EMOTION: excited",
        "ACTION: press spacebar",
        "THINK: I should try going left here",
        "emotion: happy",  # Lowercase variant
        "Hello chat!",  # Unparsed - should infer SPEAK
        "excited",  # Single word emotion
        "press W key",  # Unparsed action
    ]

    print("Testing response parser:\n")
    for response in test_responses:
        parsed = parser.parse(response)
        print(f"Input:  {response}")
        print(f"Action: {parsed.action_type.value}")
        print(f"Content: {parsed.content}")
        print(f"Confidence: {parsed.confidence}")
        print(f"Valid: {parser.validate_action(parsed)}")
        print()
