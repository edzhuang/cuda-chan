"""Action validator for safety checks."""

import re
from typing import Optional, List, Set
from dataclasses import dataclass

from utils.logger import log


@dataclass
class ValidationResult:
    """Result of action validation."""
    is_valid: bool
    reason: Optional[str] = None
    sanitized_action: Optional[str] = None


class ActionValidator:
    """Validates actions before execution for safety."""

    # Dangerous actions that should never be allowed
    FORBIDDEN_ACTIONS = {
        'alt+f4', 'cmd+q', 'ctrl+alt+delete',
        'shutdown', 'restart', 'poweroff',
        'rm -rf', 'del /f', 'format',
        'taskkill', 'pkill', 'kill -9'
    }

    # Safe keyboard keys
    SAFE_KEYS = {
        # Letters
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
        # Numbers
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
        # Special keys
        'space', 'spacebar', 'enter', 'return', 'escape', 'esc',
        'backspace', 'tab', 'shift', 'ctrl', 'control', 'alt',
        # Arrow keys
        'up', 'down', 'left', 'right',
        # Function keys
        'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
        # Other
        'home', 'end', 'pageup', 'pagedown', 'insert', 'delete'
    }

    # Mouse actions
    SAFE_MOUSE_ACTIONS = {'click', 'left_click', 'right_click', 'double_click', 'move'}

    def __init__(self, max_actions_per_second: int = 10):
        """
        Initialize action validator.

        Args:
            max_actions_per_second: Maximum actions allowed per second
        """
        self.max_actions_per_second = max_actions_per_second
        self.action_count = 0
        self.last_reset_time = 0

        log.info(f"Action validator initialized (max {max_actions_per_second} actions/sec)")

    def validate_keyboard_action(self, action: str) -> ValidationResult:
        """
        Validate a keyboard action.

        Args:
            action: Action string (e.g., "press w", "hold shift")

        Returns:
            ValidationResult
        """
        action_lower = action.lower().strip()

        # Check for forbidden actions
        for forbidden in self.FORBIDDEN_ACTIONS:
            if forbidden in action_lower:
                log.warning(f"Blocked forbidden action: {action}")
                return ValidationResult(
                    is_valid=False,
                    reason=f"Forbidden action detected: {forbidden}"
                )

        # Parse action
        action_type, key = self._parse_keyboard_action(action_lower)

        if not action_type or not key:
            return ValidationResult(
                is_valid=False,
                reason="Could not parse action"
            )

        # Validate key
        if key not in self.SAFE_KEYS:
            log.warning(f"Unsafe key: {key}")
            return ValidationResult(
                is_valid=False,
                reason=f"Key not in safe list: {key}"
            )

        # Sanitize and return
        sanitized = f"{action_type} {key}"
        return ValidationResult(
            is_valid=True,
            sanitized_action=sanitized
        )

    def validate_mouse_action(self, action: str) -> ValidationResult:
        """
        Validate a mouse action.

        Args:
            action: Action string (e.g., "click", "move to center")

        Returns:
            ValidationResult
        """
        action_lower = action.lower().strip()

        # Parse action
        action_type = self._parse_mouse_action(action_lower)

        if not action_type:
            return ValidationResult(
                is_valid=False,
                reason="Could not parse mouse action"
            )

        if action_type not in self.SAFE_MOUSE_ACTIONS:
            return ValidationResult(
                is_valid=False,
                reason=f"Unsafe mouse action: {action_type}"
            )

        # Extract coordinates if present
        coords = self._extract_coordinates(action_lower)

        if action_type == 'move' and coords:
            # Validate coordinates are reasonable
            x, y = coords
            if not (0 <= x <= 10000 and 0 <= y <= 10000):
                return ValidationResult(
                    is_valid=False,
                    reason="Coordinates out of reasonable range"
                )

        return ValidationResult(
            is_valid=True,
            sanitized_action=action_lower
        )

    def validate_action(self, action: str) -> ValidationResult:
        """
        Validate any action (keyboard or mouse).

        Args:
            action: Action string

        Returns:
            ValidationResult
        """
        action_lower = action.lower().strip()

        # Check if it's a keyboard action
        if any(keyword in action_lower for keyword in ['press', 'hold', 'release', 'type', 'key']):
            return self.validate_keyboard_action(action)

        # Check if it's a mouse action
        if any(keyword in action_lower for keyword in ['click', 'move', 'mouse']):
            return self.validate_mouse_action(action)

        # Unknown action type
        return ValidationResult(
            is_valid=False,
            reason="Unknown action type (must be keyboard or mouse)"
        )

    def _parse_keyboard_action(self, action: str) -> tuple[Optional[str], Optional[str]]:
        """
        Parse keyboard action into type and key.

        Returns:
            Tuple of (action_type, key)
        """
        # Pattern: "press W", "hold shift", "release space"
        patterns = [
            r'(press|hold|release|type)\s+(.+)',
            r'(.+)\s+key',
        ]

        for pattern in patterns:
            match = re.match(pattern, action)
            if match:
                if len(match.groups()) == 2:
                    return match.group(1), match.group(2).strip()
                elif len(match.groups()) == 1:
                    return 'press', match.group(1).strip()

        # Single word might be a key
        words = action.split()
        if len(words) == 1 and words[0] in self.SAFE_KEYS:
            return 'press', words[0]

        return None, None

    def _parse_mouse_action(self, action: str) -> Optional[str]:
        """Parse mouse action type."""
        if 'double' in action and 'click' in action:
            return 'double_click'
        elif 'right' in action and 'click' in action:
            return 'right_click'
        elif 'left' in action and 'click' in action:
            return 'left_click'
        elif 'click' in action:
            return 'click'
        elif 'move' in action:
            return 'move'

        return None

    def _extract_coordinates(self, action: str) -> Optional[tuple[int, int]]:
        """Extract coordinates from action string."""
        # Pattern: "move to 100, 200" or "move (100, 200)"
        coord_pattern = r'(\d+)\s*,?\s*(\d+)'
        match = re.search(coord_pattern, action)

        if match:
            x = int(match.group(1))
            y = int(match.group(2))
            return x, y

        # Special positions
        if 'center' in action:
            return 960, 540  # Rough center of 1920x1080
        elif 'top' in action and 'left' in action:
            return 100, 100
        elif 'top' in action and 'right' in action:
            return 1820, 100
        elif 'bottom' in action and 'left' in action:
            return 100, 980
        elif 'bottom' in action and 'right' in action:
            return 1820, 980

        return None

    def is_rate_limited(self) -> bool:
        """Check if rate limit is exceeded."""
        import time
        current_time = time.time()

        # Reset counter every second
        if current_time - self.last_reset_time >= 1.0:
            self.action_count = 0
            self.last_reset_time = current_time

        return self.action_count >= self.max_actions_per_second

    def record_action(self):
        """Record that an action was executed."""
        self.action_count += 1


if __name__ == "__main__":
    # Test action validator
    validator = ActionValidator()

    test_actions = [
        "press W",
        "hold shift",
        "press spacebar",
        "click",
        "move to center",
        "alt+f4",  # Should be blocked
        "rm -rf /",  # Should be blocked
        "press unknown_key",  # Should be blocked
        "double click",
        "move to 500, 300",
    ]

    print("Testing action validator:\n")
    for action in test_actions:
        result = validator.validate_action(action)
        print(f"Action: {action}")
        print(f"Valid: {result.is_valid}")
        if not result.is_valid:
            print(f"Reason: {result.reason}")
        else:
            print(f"Sanitized: {result.sanitized_action}")
        print()
