"""Main orchestrator - coordinates all CUDA-chan systems."""

import asyncio
from typing import Optional
from datetime import datetime

from config.settings import settings
from core.event_queue import EventQueue, Priority, EventType
from core.state_manager import StateManager, SystemState, EmotionalState
from ai.claude_brain import ClaudeBrain
from ai.response_parser import ActionType
from output.vtube_controller import VTubeStudioController
from output.tts_manager import TTSManager
from chat.youtube_monitor import YouTubeChatMonitor
from chat.chat_parser import ChatParser
from vision.screen_capture import ScreenCapture
from control.input_controller import InputController
from input.audio_monitor import AudioMonitor
from input.speech_to_text import StreamerVoiceInput
from utils.logger import log


class Orchestrator:
    """Main system orchestrator."""

    def __init__(self):
        """Initialize orchestrator and all subsystems."""
        log.info("Initializing CUDA-chan orchestrator...")

        # Core systems
        self.event_queue = EventQueue(max_size=1000)
        self.state_manager = StateManager()

        # AI system
        self.brain = ClaudeBrain()

        # Output systems
        self.vtube = VTubeStudioController()
        self.tts = TTSManager()

        # Input systems
        self.chat_monitor: Optional[YouTubeChatMonitor] = None
        self.chat_parser = ChatParser()
        self.screen_capture = ScreenCapture()
        # Very low threshold for iPhone Continuity Mic and other low-gain devices
        self.audio_monitor = AudioMonitor(threshold=0.003)
        self.voice_input = StreamerVoiceInput()

        # Control system
        self.input_controller = InputController()

        # Control flags
        self.running = False
        self.tick_rate = settings.system.tick_rate

        # Background tasks
        self.tasks = []

        log.success("Orchestrator initialized")

    async def initialize(self) -> bool:
        """
        Initialize all subsystems.

        Returns:
            True if initialization successful
        """
        log.info("Starting subsystem initialization...")

        try:
            # Connect to VTube Studio
            log.info("Connecting to VTube Studio...")
            if not await self.vtube.connect():
                log.error("Failed to connect to VTube Studio")
                return False

            # Start TTS playback worker
            log.info("Starting TTS system...")
            tts_task = asyncio.create_task(self.tts.playback_worker())
            self.tasks.append(tts_task)

            # Initialize chat monitor if video ID is provided
            if settings.youtube.video_id:
                log.info("Initializing YouTube chat monitor...")
                self.chat_monitor = YouTubeChatMonitor(settings.youtube.video_id)
                if await self.chat_monitor.start():
                    # Start chat monitoring loop
                    chat_task = asyncio.create_task(
                        self.chat_monitor.monitor_loop(self._handle_chat_message)
                    )
                    self.tasks.append(chat_task)
                else:
                    log.warning("Chat monitor failed to start, continuing without it")
            else:
                log.warning("No YouTube video ID configured, skipping chat monitor")

            # Initialize microphone input (CRITICAL for sidekick mode)
            log.info("Initializing streamer voice input...")
            try:
                await self.voice_input.initialize()
                self.audio_monitor.set_speech_callback(self._on_streamer_speech)
                await self.audio_monitor.start()
                log.success("Microphone input active - CUDA-chan can now hear you!")
            except Exception as e:
                log.error(f"Failed to initialize microphone: {e}")
                log.warning("Continuing without microphone input")

            # Set initial state
            self.state_manager.update_system_state(SystemState.IDLE)

            log.success("All subsystems initialized successfully")
            return True

        except Exception as e:
            log.error(f"Initialization failed: {e}")
            return False

    async def run(self):
        """Main orchestration loop."""
        log.info("Starting main orchestration loop...")
        self.running = True
        self.state_manager.update_system_state(SystemState.IDLE)

        # Send startup greeting
        await self._startup_greeting()

        try:
            while self.running:
                await self._main_loop_iteration()
                await asyncio.sleep(self.tick_rate)

        except KeyboardInterrupt:
            log.info("Shutdown requested by user")
        except Exception as e:
            log.error(f"Main loop error: {e}")
        finally:
            await self.shutdown()

    async def _main_loop_iteration(self):
        """Single iteration of main loop."""
        try:
            # Phase 1: Process events from queue
            event = self.event_queue.get_nowait()

            if event:
                await self._process_event(event)
            else:
                # No events - idle behavior
                if self.state_manager.system_state == SystemState.IDLE:
                    await self._idle_behavior()

            # Phase 2: Periodic tasks
            await self._periodic_tasks()

        except Exception as e:
            log.error(f"Loop iteration error: {e}")

    async def _process_event(self, event):
        """Process an event from the queue."""
        log.debug(f"Processing event: {event.event_type}")

        try:
            if event.event_type == EventType.STREAMER_SPEECH:
                await self._handle_streamer_speech(event.data)

            elif event.event_type == EventType.CHAT_MESSAGE:
                await self._handle_chat_event(event.data)

            elif event.event_type == EventType.GAME_STATE_CHANGE:
                await self._handle_game_state_change(event.data)

            elif event.event_type == EventType.AUTONOMOUS_DECISION:
                await self._make_autonomous_decision()

            elif event.event_type == EventType.SYSTEM_SHUTDOWN:
                self.running = False

        except Exception as e:
            log.error(f"Event processing error: {e}")

    async def _handle_chat_message(self, message: dict):
        """
        Handle incoming chat message.

        Args:
            message: Chat message dictionary
        """
        # Parse message
        parsed = self.chat_parser.parse_message(message)

        # Add to state manager context
        self.state_manager.chat_context.add_message(
            parsed["author"],
            parsed["text"]
        )

        # Queue event with appropriate priority
        await self.event_queue.put(
            EventType.CHAT_MESSAGE,
            parsed,
            priority=parsed["priority"],
            source="youtube_chat"
        )

    async def _on_streamer_speech(self, audio_data):
        """
        Callback when streamer speech is detected.

        Args:
            audio_data: Audio data from microphone
        """
        try:
            log.debug(f"Processing streamer speech: {len(audio_data)} samples")

            # Transcribe audio (no need to set streamer_is_speaking flag)
            text = await self.voice_input.stt.transcribe(audio_data)

            if text and text.strip():
                log.info(f"Streamer said: {text}")

                # Queue streamer speech event with CRITICAL priority
                await self.event_queue.put(
                    EventType.STREAMER_SPEECH,
                    {"text": text, "audio_length": len(audio_data)},
                    Priority.CRITICAL,
                    "streamer_microphone"
                )
            else:
                log.debug("No text transcribed from audio")

        except Exception as e:
            log.error(f"Error processing streamer speech: {e}")

    async def _handle_streamer_speech(self, speech_data: dict):
        """
        Handle streamer speech event (HIGHEST PRIORITY).

        Args:
            speech_data: Dictionary with 'text' and other metadata
        """
        text = speech_data.get("text", "")

        if not text or not text.strip():
            return

        log.info(f"Responding to streamer: {text[:50]}...")

        # Get AI response using streamer question prompt
        response = await self.brain.respond_to_streamer(text)

        if response:
            await self._execute_ai_action(response)

    async def _handle_chat_event(self, parsed_message: dict):
        """Handle chat message event."""
        # Skip spam
        if parsed_message.get("is_spam"):
            return

        # Check if we should respond
        if not self.chat_parser.should_respond(parsed_message):
            return

        log.info(f"Responding to chat from {parsed_message['author']}: {parsed_message['text'][:50]}...")

        # Get AI response
        context = self.state_manager.get_context_for_ai()
        response = await self.brain.respond_to_chat(parsed_message, context)

        if response:
            await self._execute_ai_action(response)

    async def _make_autonomous_decision(self):
        """Make an autonomous decision based on current state."""
        context = self.state_manager.get_context_for_ai()
        decision = await self.brain.decide(context)

        if decision:
            await self._execute_ai_action(decision)

    async def _execute_ai_action(self, action):
        """Execute an action decided by AI."""
        try:
            if action.action_type == ActionType.SPEAK:
                await self._execute_speak(action.content)

            elif action.action_type == ActionType.EMOTION:
                await self._execute_emotion(action.content)

            elif action.action_type == ActionType.ACTION:
                await self._execute_game_action(action.content)

            elif action.action_type == ActionType.THINK:
                self._execute_think(action.content)

        except Exception as e:
            log.error(f"Action execution failed: {e}")

    async def _execute_speak(self, text: str):
        """Execute speech action."""
        log.info(f"Speaking: {text[:50]}...")

        # Update state
        self.state_manager.is_speaking = True

        # Estimate duration
        duration = self.tts.estimate_duration(text)

        # Queue speech and avatar animation
        await self.tts.speak(text)

        # Animate avatar
        if self.vtube.authenticated:
            asyncio.create_task(self.vtube.animate_speaking(duration, intensity=0.6))

        # Wait for speech to finish
        # Note: We don't stop if streamer starts speaking - natural overlapping conversation
        while self.tts.is_speaking:
            await asyncio.sleep(0.1)

        self.state_manager.is_speaking = False

    async def _execute_emotion(self, emotion: str):
        """Execute emotion change."""
        log.info(f"Changing emotion to: {emotion}")

        # Update state manager
        try:
            emotion_state = EmotionalState(emotion.lower())
            self.state_manager.update_emotional_state(emotion_state)
        except ValueError:
            log.warning(f"Unknown emotional state: {emotion}")

        # Update avatar
        if self.vtube.authenticated:
            await self.vtube.set_emotion(emotion)

    async def _execute_game_action(self, action: str):
        """Execute game input action."""
        log.info(f"Game action: {action}")

        # Record in state
        self.state_manager.action_history.add_action("game_input", action)

        # Execute via input controller
        success = await self.input_controller.execute_action(action)

        if not success:
            log.warning(f"Game action failed: {action}")

    def _execute_think(self, thought: str):
        """Execute internal thought (no external action)."""
        log.debug(f"Internal thought: {thought[:100]}...")
        # Could store thoughts for context/memory

    async def _idle_behavior(self):
        """Behavior when idle (no events)."""
        # Occasionally make an autonomous decision for commentary
        # In sidekick mode, should comment on game, chat, etc.
        import random
        if random.random() < 0.15:  # 15% chance per tick for more engagement
            log.debug("Idle behavior triggered")
            recent_chat = self.state_manager.chat_context.get_recent_messages(5)
            decision = await self.brain.idle_behavior(recent_chat)
            if decision:
                await self._execute_ai_action(decision)

    async def _periodic_tasks(self):
        """Periodic maintenance tasks."""
        # Could add: health checks, statistics logging, etc.
        pass

    async def _handle_game_state_change(self, game_state: dict):
        """Handle game state changes."""
        pass  # To be implemented for specific games

    async def _startup_greeting(self):
        """Send startup greeting."""
        greeting = settings.personality.catchphrases.get("greeting", ["Hello everyone!"])[0]
        await self._execute_speak(f"{greeting} CUDA-chan is online and ready to play!")
        await self._execute_emotion("happy")

    async def shutdown(self):
        """Graceful shutdown of all subsystems."""
        log.info("Shutting down CUDA-chan...")

        self.state_manager.update_system_state(SystemState.SHUTTING_DOWN)

        # Send farewell
        farewell = settings.personality.catchphrases.get("farewell", ["Goodbye!"])[0]
        await self._execute_speak(f"{farewell} See you next time!")

        # Stop audio monitor
        if self.audio_monitor.is_monitoring:
            await self.audio_monitor.stop()

        # Stop chat monitor
        if self.chat_monitor:
            await self.chat_monitor.stop()

        # Disconnect VTube Studio
        await self.vtube.disconnect()

        # Cleanup TTS
        await self.tts.cleanup()

        # Cancel background tasks
        for task in self.tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        log.success("CUDA-chan shutdown complete")


if __name__ == "__main__":
    # Test orchestrator initialization
    async def test_orchestrator():
        orchestrator = Orchestrator()

        print("Testing orchestrator initialization...")
        success = await orchestrator.initialize()

        if success:
            print("Initialization successful!")
            print(f"State: {orchestrator.state_manager.system_state.value}")
            print(f"Stats: {orchestrator.brain.get_statistics()}")
        else:
            print("Initialization failed")

        await orchestrator.shutdown()

    # Uncomment to test (requires valid API keys and VTube Studio)
    # asyncio.run(test_orchestrator())
    print("Orchestrator module loaded. Requires full setup to test.")
