"""Input controller for keyboard and mouse automation."""

import asyncio
from typing import Optional, Tuple
import pyautogui

from config.settings import settings
from control.action_validator import ActionValidator, ValidationResult
from utils.logger import log


class InputController:
    """Controls keyboard and mouse inputs with safety mechanisms."""

    def __init__(self):
        """Initialize input controller."""
        # Initialize pyautogui with safety settings
        pyautogui.FAILSAFE = settings.safety.pyautogui_failsafe
        pyautogui.PAUSE = 0.1  # Small delay between actions

        self.validator = ActionValidator(
            max_actions_per_second=settings.safety.max_actions_per_second
        )

        self.is_enabled = True
        self.actions_executed = 0

        log.info("Input controller initialized (failsafe enabled)")

    async def execute_action(self, action: str) -> bool:
        """
        Execute a validated action.

        Args:
            action: Action string to execute

        Returns:
            True if executed successfully
        """
        if not self.is_enabled:
            log.warning("Input controller is disabled")
            return False

        # Rate limiting check
        if self.validator.is_rate_limited():
            log.warning("Rate limit exceeded, action blocked")
            return False

        # Validate action
        validation = self.validator.validate_action(action)

        if not validation.is_valid:
            log.error(f"Action validation failed: {validation.reason}")
            return False

        # Execute based on type
        try:
            action_lower = validation.sanitized_action.lower()

            if any(keyword in action_lower for keyword in ['press', 'hold', 'release', 'type', 'key']):
                success = await self._execute_keyboard(action_lower)
            elif any(keyword in action_lower for keyword in ['click', 'move', 'mouse']):
                success = await self._execute_mouse(action_lower)
            else:
                log.error(f"Unknown action type: {action}")
                return False

            if success:
                self.validator.record_action()
                self.actions_executed += 1
                log.info(f"Executed action: {action}")

            return success

        except pyautogui.FailSafeException:
            log.error("PyAutoGUI failsafe triggered! Mouse moved to corner.")
            self.disable()
            return False
        except Exception as e:
            log.error(f"Action execution failed: {e}")
            return False

    async def _execute_keyboard(self, action: str) -> bool:
        """Execute keyboard action."""
        # Parse action type and key
        if 'press' in action:
            key = action.replace('press', '').strip()
            await self._press_key(key)
        elif 'hold' in action:
            key = action.replace('hold', '').strip()
            await self._hold_key(key)
        elif 'release' in action:
            key = action.replace('release', '').strip()
            await self._release_key(key)
        elif 'type' in action:
            text = action.replace('type', '').strip()
            await self._type_text(text)
        else:
            # Assume single key press
            await self._press_key(action)

        return True

    async def _execute_mouse(self, action: str) -> bool:
        """Execute mouse action."""
        if 'move' in action:
            coords = self._extract_coordinates_from_action(action)
            if coords:
                await self._move_mouse(coords[0], coords[1])
        elif 'double' in action and 'click' in action:
            await self._double_click()
        elif 'right' in action and 'click' in action:
            await self._right_click()
        elif 'click' in action:
            await self._click()
        else:
            return False

        return True

    async def _press_key(self, key: str):
        """Press a key."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, pyautogui.press, self._normalize_key(key))
        log.debug(f"Pressed key: {key}")

    async def _hold_key(self, key: str):
        """Hold a key down."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, pyautogui.keyDown, self._normalize_key(key))
        log.debug(f"Holding key: {key}")

    async def _release_key(self, key: str):
        """Release a key."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, pyautogui.keyUp, self._normalize_key(key))
        log.debug(f"Released key: {key}")

    async def _type_text(self, text: str):
        """Type text."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, pyautogui.write, text)
        log.debug(f"Typed text: {text[:20]}...")

    async def _click(self):
        """Left mouse click."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, pyautogui.click)
        log.debug("Mouse clicked")

    async def _right_click(self):
        """Right mouse click."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, pyautogui.rightClick)
        log.debug("Mouse right-clicked")

    async def _double_click(self):
        """Double mouse click."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, pyautogui.doubleClick)
        log.debug("Mouse double-clicked")

    async def _move_mouse(self, x: int, y: int, duration: float = 0.2):
        """Move mouse to position."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: pyautogui.moveTo(x, y, duration=duration))
        log.debug(f"Mouse moved to ({x}, {y})")

    def _normalize_key(self, key: str) -> str:
        """Normalize key name for pyautogui."""
        key = key.lower().strip()

        # Map common names to pyautogui names
        key_mapping = {
            'spacebar': 'space',
            'esc': 'escape',
            'return': 'enter',
            'control': 'ctrl'
        }

        return key_mapping.get(key, key)

    def _extract_coordinates_from_action(self, action: str) -> Optional[Tuple[int, int]]:
        """Extract coordinates from mouse action."""
        import re

        # Try to find numbers
        numbers = re.findall(r'\d+', action)
        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])

        # Check for special positions
        if 'center' in action:
            screen_width, screen_height = pyautogui.size()
            return screen_width // 2, screen_height // 2

        return None

    async def emergency_stop(self):
        """Emergency stop - release all keys."""
        log.warning("Emergency stop triggered!")

        # Release common keys
        common_keys = ['w', 'a', 's', 'd', 'shift', 'ctrl', 'space']
        for key in common_keys:
            try:
                pyautogui.keyUp(key)
            except:
                pass

        self.disable()

    def enable(self):
        """Enable input controller."""
        self.is_enabled = True
        log.info("Input controller enabled")

    def disable(self):
        """Disable input controller."""
        self.is_enabled = False
        log.warning("Input controller disabled")

    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position."""
        return pyautogui.position()

    def get_screen_size(self) -> Tuple[int, int]:
        """Get screen size."""
        return pyautogui.size()

    def get_statistics(self) -> dict:
        """Get controller statistics."""
        return {
            "is_enabled": self.is_enabled,
            "actions_executed": self.actions_executed,
            "mouse_position": self.get_mouse_position(),
            "screen_size": self.get_screen_size(),
            "failsafe_enabled": pyautogui.FAILSAFE
        }


if __name__ == "__main__":
    # Test input controller
    async def test_controller():
        controller = InputController()

        print("Input Controller Test")
        print("=" * 50)
        print(f"Screen size: {controller.get_screen_size()}")
        print(f"Mouse position: {controller.get_mouse_position()}")
        print()

        # Test validation only (don't actually execute)
        test_actions = [
            "press W",
            "hold shift",
            "click",
            "move to center",
        ]

        print("Testing action validation:\n")
        for action in test_actions:
            validation = controller.validator.validate_action(action)
            print(f"Action: {action}")
            print(f"Valid: {validation.is_valid}")
            print(f"Sanitized: {validation.sanitized_action}")
            print()

        print(f"Statistics: {controller.get_statistics()}")

    asyncio.run(test_controller())
