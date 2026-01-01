"""VTube Studio WebSocket controller."""

import asyncio
import json
from typing import Optional, Dict, Any
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from config.settings import settings
from output.expression_mapper import ExpressionMapper
from utils.logger import log


class VTubeStudioController:
    """Controls VTube Studio avatar via WebSocket API."""

    def __init__(self):
        """Initialize VTube Studio controller."""
        self.host = settings.vtube_studio.host
        self.port = settings.vtube_studio.port
        self.token = settings.vtube_studio.token

        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        self.authenticated = False

        self.expression_mapper = ExpressionMapper()
        self.current_emotion = "neutral"

        self._message_id = 0
        self._ws_lock = asyncio.Lock()  # Prevent concurrent WebSocket operations

        log.info(f"VTube Studio controller initialized (ws://{self.host}:{self.port})")

    def _get_next_message_id(self) -> str:
        """Get next message ID for API calls."""
        self._message_id += 1
        return str(self._message_id)

    async def connect(self, max_retries: int = 3) -> bool:
        """
        Connect to VTube Studio WebSocket API.

        Args:
            max_retries: Maximum connection attempts

        Returns:
            True if connected successfully
        """
        for attempt in range(max_retries):
            try:
                uri = f"ws://{self.host}:{self.port}"
                log.info(f"Connecting to VTube Studio at {uri} (attempt {attempt + 1}/{max_retries})")

                self.ws = await websockets.connect(uri)
                self.is_connected = True

                # Authenticate if we have a token
                if self.token:
                    self.authenticated = await self._authenticate()
                else:
                    # Request authentication token
                    self.authenticated = await self._request_authentication()

                if self.authenticated:
                    log.success("Connected and authenticated with VTube Studio")
                    return True
                else:
                    log.error("Authentication failed")

            except Exception as e:
                log.error(f"Connection attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        log.error("Failed to connect to VTube Studio after all retries")
        return False

    async def disconnect(self):
        """Disconnect from VTube Studio."""
        if self.ws:
            await self.ws.close()
            self.is_connected = False
            self.authenticated = False
            log.info("Disconnected from VTube Studio")

    async def _send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send a request to VTube Studio API.

        Args:
            request: API request dictionary

        Returns:
            Response dictionary or None if failed
        """
        if not self.is_connected or not self.ws:
            log.error("Not connected to VTube Studio")
            return None

        async with self._ws_lock:  # Serialize WebSocket operations
            try:
                # Add authentication token to request
                if self.token:
                    request["data"]["authenticationToken"] = self.token

                # Send request
                await self.ws.send(json.dumps(request))

                # Receive response
                response_text = await self.ws.recv()
                response = json.loads(response_text)

                if response.get("messageType") == "APIError":
                    log.error(f"VTube Studio API error: {response.get('data', {}).get('message', 'Unknown error')}")
                    return None

                return response

            except (ConnectionClosed, WebSocketException) as e:
                log.error(f"WebSocket error: {e}")
                self.is_connected = False
                self.authenticated = False
                return None
            except Exception as e:
                log.error(f"Request failed: {e}")
                return None

    async def _authenticate(self) -> bool:
        """Authenticate with existing token."""
        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": self._get_next_message_id(),
            "messageType": "AuthenticationRequest",
            "data": {
                "pluginName": "CUDA-chan",
                "pluginDeveloper": "AI VTuber Project",
                "authenticationToken": self.token
            }
        }

        response = await self._send_request(request)
        if response and response.get("data", {}).get("authenticated"):
            log.success("Authenticated with VTube Studio")
            return True

        return False

    async def _request_authentication(self) -> bool:
        """Request new authentication token."""
        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": self._get_next_message_id(),
            "messageType": "AuthenticationTokenRequest",
            "data": {
                "pluginName": "CUDA-chan",
                "pluginDeveloper": "AI VTuber Project",
                "pluginIcon": None
            }
        }

        if not self.ws:
            return False

        async with self._ws_lock:  # Serialize WebSocket operations
            try:
                await self.ws.send(json.dumps(request))
                response_text = await self.ws.recv()
                response = json.loads(response_text)

                if response.get("data", {}).get("authenticationToken"):
                    new_token = response["data"]["authenticationToken"]
                    log.success(f"Received authentication token: {new_token[:20]}...")
                    print(f"\n{'='*60}")
                    print(f"VTUBE STUDIO AUTHENTICATION TOKEN:")
                    print(f"{new_token}")
                    print(f"{'='*60}\n")
                    log.info("Add this token to your .env file as VTUBE_STUDIO_TOKEN")
                    self.token = new_token
                    return True

            except Exception as e:
                log.error(f"Token request failed: {e}")

        return False

    async def trigger_hotkey(self, hotkey_name: str) -> bool:
        """
        Trigger a VTube Studio hotkey.

        Args:
            hotkey_name: Name of the hotkey to trigger

        Returns:
            True if successful
        """
        if not self.authenticated:
            log.error("Not authenticated with VTube Studio")
            return False

        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": self._get_next_message_id(),
            "messageType": "HotkeyTriggerRequest",
            "data": {
                "hotkeyID": hotkey_name,
                "authenticationToken": self.token
            }
        }

        response = await self._send_request(request)
        if response:
            log.debug(f"Triggered hotkey: {hotkey_name}")
            return True

        return False

    async def set_parameter(self, parameter_name: str, value: float) -> bool:
        """
        Set a Live2D model parameter directly.

        Args:
            parameter_name: Parameter name
            value: Parameter value (-1.0 to 1.0)

        Returns:
            True if successful
        """
        if not self.authenticated:
            log.error("Not authenticated with VTube Studio")
            return False

        # Clamp value to valid range
        value = max(-1.0, min(1.0, value))

        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": self._get_next_message_id(),
            "messageType": "InjectParameterDataRequest",
            "data": {
                "parameterValues": [
                    {
                        "id": parameter_name,
                        "value": value
                    }
                ],
                "authenticationToken": self.token
            }
        }

        response = await self._send_request(request)
        if response:
            log.debug(f"Set parameter {parameter_name} = {value}")
            return True

        return False

    async def set_emotion(self, emotion: str, use_hotkeys: bool = True) -> bool:
        """
        Set CUDA-chan's emotion/expression.

        Args:
            emotion: Emotion name
            use_hotkeys: If True, use hotkeys; if False, use parameters directly

        Returns:
            True if successful
        """
        expression = self.expression_mapper.get_expression(emotion)
        if not expression:
            log.warning(f"Unknown emotion: {emotion}")
            return False

        success = True

        if use_hotkeys:
            # Trigger hotkey for this expression
            success = await self.trigger_hotkey(expression.hotkey_name)
        else:
            # Set parameters directly
            for param_name, value in expression.parameter_changes.items():
                param_success = await self.set_parameter(param_name, value * expression.intensity)
                success = success and param_success

        if success:
            self.current_emotion = emotion
            log.info(f"Emotion changed to: {emotion}")

        return success

    async def animate_speaking(self, duration: float, intensity: float = 0.5):
        """
        Animate mouth for speaking.

        Args:
            duration: How long to animate (seconds)
            intensity: Animation intensity (0.0 - 1.0)
        """
        if not self.authenticated:
            return

        params = self.expression_mapper.get_speaking_animation_params(intensity)

        # Start speaking animation
        for param_name, value in params.items():
            await self.set_parameter(param_name, value)

        # Wait for duration
        await asyncio.sleep(duration)

        # Reset mouth
        for param_name in params.keys():
            await self.set_parameter(param_name, 0.0)

        log.debug(f"Speaking animation completed ({duration:.1f}s)")

    async def get_available_hotkeys(self) -> Optional[list]:
        """
        Get list of available hotkeys from VTube Studio.

        Returns:
            List of hotkey dictionaries or None
        """
        if not self.authenticated:
            return None

        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": self._get_next_message_id(),
            "messageType": "HotkeysInCurrentModelRequest",
            "data": {
                "authenticationToken": self.token
            }
        }

        response = await self._send_request(request)
        if response and "data" in response:
            hotkeys = response["data"].get("availableHotkeys", [])
            log.info(f"Found {len(hotkeys)} available hotkeys")
            return hotkeys

        return None

    async def health_check(self) -> bool:
        """
        Check if connection to VTube Studio is healthy.

        Returns:
            True if healthy
        """
        if not self.is_connected:
            return False

        # Try a simple API call
        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": self._get_next_message_id(),
            "messageType": "APIStateRequest",
            "data": {}
        }

        response = await self._send_request(request)
        return response is not None


if __name__ == "__main__":
    # Test VTube Studio controller
    async def test_controller():
        controller = VTubeStudioController()

        print("Connecting to VTube Studio...")
        if await controller.connect():
            print("Connected successfully!")

            # Test emotion change
            print("\nTesting emotions...")
            for emotion in ["happy", "excited", "sad", "neutral"]:
                print(f"Setting emotion: {emotion}")
                await controller.set_emotion(emotion)
                await asyncio.sleep(2)

            # Test speaking animation
            print("\nTesting speaking animation...")
            await controller.animate_speaking(duration=3.0, intensity=0.7)

            await controller.disconnect()
        else:
            print("Failed to connect")

    # Uncomment to test (requires VTube Studio running)
    # asyncio.run(test_controller())
    print("VTube Studio controller module loaded. Requires VTube Studio running to test.")
