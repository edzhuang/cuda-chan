"""Claude AI decision-making brain for CUDA-chan."""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import deque
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from ai.prompt_builder import PromptBuilder
from ai.response_parser import ResponseParser, ParsedResponse, ActionType
from utils.logger import log


class RateLimiter:
    """Rate limiter for API calls."""

    def __init__(self, max_requests_per_minute: int):
        """
        Initialize rate limiter.

        Args:
            max_requests_per_minute: Maximum requests per minute
        """
        self.max_rpm = max_requests_per_minute
        self.requests = deque()
        log.debug(f"Rate limiter initialized: {max_requests_per_minute} RPM")

    async def acquire(self):
        """Wait until a request slot is available."""
        now = datetime.now()

        # Remove requests older than 1 minute
        while self.requests and self.requests[0] < now - timedelta(minutes=1):
            self.requests.popleft()

        # If at limit, wait
        if len(self.requests) >= self.max_rpm:
            wait_time = 60 - (now - self.requests[0]).total_seconds()
            if wait_time > 0:
                log.warning(f"Rate limit reached, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                await self.acquire()  # Retry after waiting
                return

        # Record this request
        self.requests.append(now)

    def get_remaining(self) -> int:
        """Get remaining requests in current minute."""
        now = datetime.now()
        # Remove old requests
        while self.requests and self.requests[0] < now - timedelta(minutes=1):
            self.requests.popleft()
        return self.max_rpm - len(self.requests)


class ClaudeBrain:
    """Main AI decision-making engine using Claude."""

    def __init__(self):
        """Initialize Claude brain."""
        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=settings.api.anthropic_api_key)

        # Initialize components
        personality_dict = settings.personality.dict()
        self.prompt_builder = PromptBuilder(personality_dict)
        self.response_parser = ResponseParser()

        # Rate limiting
        self.rate_limiter = RateLimiter(settings.rate_limits.claude_max_rpm)

        # Statistics
        self.total_requests = 0
        self.total_tokens = 0
        self.failed_requests = 0

        log.info("Claude brain initialized")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _call_claude(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000,
        temperature: float = 1.0
    ) -> str:
        """
        Call Claude API with retry logic.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Claude's response text
        """
        # Wait for rate limit
        await self.rate_limiter.acquire()

        try:
            # Call Claude API (synchronous call in async context)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt,
                    messages=[{
                        "role": "user",
                        "content": user_prompt
                    }]
                )
            )

            # Extract response text
            response_text = response.content[0].text

            # Update statistics
            self.total_requests += 1
            self.total_tokens += response.usage.input_tokens + response.usage.output_tokens

            log.debug(f"Claude API call successful. Tokens: {response.usage.input_tokens + response.usage.output_tokens}")

            return response_text

        except anthropic.APIError as e:
            self.failed_requests += 1
            log.error(f"Claude API error: {e}")
            raise

    async def decide(self, context: Dict[str, Any]) -> Optional[ParsedResponse]:
        """
        Make a decision based on current context.

        Args:
            context: Current system context

        Returns:
            Parsed action or None if failed
        """
        try:
            # Build prompt
            system_prompt, user_prompt = self.prompt_builder.build_decision_prompt(context)

            # Optimize context if needed
            estimated_tokens = self.prompt_builder.estimate_tokens(system_prompt + user_prompt)
            if estimated_tokens > settings.rate_limits.claude_max_tokens:
                log.warning(f"Context too large ({estimated_tokens} tokens), optimizing")
                optimized_context = self.prompt_builder.optimize_context(
                    context,
                    max_tokens=settings.rate_limits.claude_max_tokens // 2
                )
                system_prompt, user_prompt = self.prompt_builder.build_decision_prompt(optimized_context)

            # Call Claude
            response_text = await self._call_claude(
                system_prompt,
                user_prompt,
                max_tokens=500,  # Decisions should be concise
                temperature=1.0
            )

            # Parse response
            parsed = self.response_parser.parse(response_text)

            # Validate
            if not self.response_parser.validate_action(parsed):
                log.error("Action validation failed")
                return None

            log.info(f"Decision: {parsed.action_type.value} - {parsed.content[:50]}...")
            return parsed

        except Exception as e:
            log.error(f"Decision making failed: {e}")
            return None

    async def respond_to_chat(
        self,
        message: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[ParsedResponse]:
        """
        Respond to a specific chat message.

        Args:
            message: Chat message to respond to
            context: Additional context

        Returns:
            Parsed response or None
        """
        try:
            system_prompt, user_prompt = self.prompt_builder.build_chat_response_prompt(
                message,
                context
            )

            response_text = await self._call_claude(
                system_prompt,
                user_prompt,
                max_tokens=300,
                temperature=1.0
            )

            parsed = self.response_parser.parse(response_text)

            if self.response_parser.validate_action(parsed):
                log.info(f"Chat response: {parsed.content[:50]}...")
                return parsed

            return None

        except Exception as e:
            log.error(f"Chat response failed: {e}")
            return None

    async def decide_game_action(self, game_state: Dict[str, Any]) -> Optional[ParsedResponse]:
        """
        Decide on a game action.

        Args:
            game_state: Current game state

        Returns:
            Parsed action or None
        """
        try:
            system_prompt, user_prompt = self.prompt_builder.build_game_action_prompt(game_state)

            response_text = await self._call_claude(
                system_prompt,
                user_prompt,
                max_tokens=200,  # Game actions should be brief
                temperature=0.8  # Slightly more focused for gameplay
            )

            parsed = self.response_parser.parse(response_text)

            if parsed.action_type in [ActionType.ACTION, ActionType.SPEAK, ActionType.EMOTION]:
                if self.response_parser.validate_action(parsed):
                    return parsed

            return None

        except Exception as e:
            log.error(f"Game action decision failed: {e}")
            return None

    async def idle_behavior(self, recent_chat: list) -> Optional[ParsedResponse]:
        """
        Decide what to do when idle.

        Args:
            recent_chat: Recent chat messages

        Returns:
            Parsed action or None
        """
        try:
            system_prompt, user_prompt = self.prompt_builder.build_idle_prompt(recent_chat)

            response_text = await self._call_claude(
                system_prompt,
                user_prompt,
                max_tokens=300,
                temperature=1.0
            )

            parsed = self.response_parser.parse(response_text)

            if self.response_parser.validate_action(parsed):
                return parsed

            return None

        except Exception as e:
            log.error(f"Idle behavior decision failed: {e}")
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get API usage statistics."""
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "failed_requests": self.failed_requests,
            "average_tokens_per_request": self.total_tokens / max(self.total_requests, 1),
            "rate_limit_remaining": self.rate_limiter.get_remaining()
        }


if __name__ == "__main__":
    # Test the Claude brain
    async def test_brain():
        brain = ClaudeBrain()

        # Test decision making
        context = {
            "current_game": "idle",
            "current_goal": "Chat with viewers",
            "emotional_state": "happy",
            "recent_chat": [
                {"author": "TestUser", "text": "Hello CUDA-chan!"}
            ],
            "vision_summary": "No game active",
            "recent_actions": []
        }

        print("Testing decision making...")
        decision = await brain.decide(context)

        if decision:
            print(f"Action: {decision.action_type.value}")
            print(f"Content: {decision.content}")
            print(f"Confidence: {decision.confidence}")
        else:
            print("Decision failed")

        print(f"\nStatistics: {brain.get_statistics()}")

    # Uncomment to test (requires valid API key)
    # asyncio.run(test_brain())
    print("Claude brain module loaded. Run test_brain() with valid API key to test.")
