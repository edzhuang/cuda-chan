"""Dynamic prompt builder for Claude AI."""

from typing import Dict, Any, Optional, List
from config.prompts import (
    build_system_prompt,
    build_decision_prompt,
    build_idle_prompt,
    build_chat_response_prompt,
    build_game_event_prompt,  # Renamed for sidekick mode
    build_streamer_question_prompt  # New for sidekick mode
)
from utils.logger import log


class PromptBuilder:
    """Builds prompts dynamically based on context."""

    def __init__(self, personality_config: dict):
        """
        Initialize prompt builder.

        Args:
            personality_config: Personality configuration dictionary
        """
        self.personality_config = personality_config
        self.system_prompt = build_system_prompt(personality_config)
        log.info(f"Prompt builder initialized for {personality_config.get('name', 'CUDA-chan')}")

    def build_decision_prompt(self, context: Dict[str, Any]) -> tuple[str, str]:
        """
        Build a decision-making prompt based on current context.

        Args:
            context: Current system context

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        user_prompt = build_decision_prompt(context, self.personality_config)
        return self.system_prompt, user_prompt

    def build_idle_prompt(self, recent_chat: List[Dict], time_silent: float = 0.0) -> tuple[str, str]:
        """
        Build prompt for idle behavior.

        Args:
            recent_chat: Recent chat messages
            time_silent: Time since last speech in seconds

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        user_prompt = build_idle_prompt(self.personality_config, recent_chat, time_silent)
        return self.system_prompt, user_prompt

    def build_chat_response_prompt(
        self,
        message: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[str, str]:
        """
        Build prompt for responding to a specific chat message.

        Args:
            message: Chat message to respond to
            context: Additional context

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        user_prompt = build_chat_response_prompt(message, self.personality_config, context)
        return self.system_prompt, user_prompt

    def build_game_event_prompt(self, event_description: str) -> tuple[str, str]:
        """
        Build prompt for reacting to game events (sidekick mode).

        Args:
            event_description: Description of what happened in the game

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        user_prompt = build_game_event_prompt(event_description, self.personality_config)
        return self.system_prompt, user_prompt

    def build_streamer_question_prompt(self, question: str) -> tuple[str, str]:
        """
        Build prompt for responding to streamer questions (sidekick mode).

        Args:
            question: Question from the streamer

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        user_prompt = build_streamer_question_prompt(question, self.personality_config)
        return self.system_prompt, user_prompt

    def build_compact_context(self, context: Dict[str, Any]) -> str:
        """
        Build a compact summary of context (for token efficiency).

        Args:
            context: Full context

        Returns:
            Compact context string
        """
        # Extract key information
        game = context.get("current_game", "idle")
        goal = context.get("current_goal", "")
        emotion = context.get("emotional_state", "neutral")

        # Summarize chat
        recent_chat = context.get("recent_chat", [])
        if recent_chat:
            chat_summary = f"{len(recent_chat)} recent messages"
            # Include last 3 messages
            last_messages = recent_chat[-3:]
            chat_details = " | ".join([f"{m['author']}: {m['text'][:30]}..." for m in last_messages])
        else:
            chat_summary = "No recent chat"
            chat_details = ""

        # Summarize actions
        recent_actions = context.get("recent_actions", [])
        if recent_actions:
            action_summary = f"Last action: {recent_actions[-1].get('type', 'unknown')}"
        else:
            action_summary = "No recent actions"

        compact = f"""Activity: {game}
Goal: {goal}
Emotion: {emotion}
Chat: {chat_summary}
{chat_details}
{action_summary}"""

        return compact

    def estimate_tokens(self, text: str) -> int:
        """
        Rough estimate of token count.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token
        return len(text) // 4

    def optimize_context(self, context: Dict[str, Any], max_tokens: int = 1500) -> Dict[str, Any]:
        """
        Optimize context to fit within token budget.

        Args:
            context: Full context
            max_tokens: Maximum tokens allowed

        Returns:
            Optimized context
        """
        optimized = context.copy()

        # Estimate current size
        context_str = str(optimized)
        estimated_tokens = self.estimate_tokens(context_str)

        if estimated_tokens <= max_tokens:
            return optimized  # Already within budget

        log.debug(f"Optimizing context: {estimated_tokens} -> {max_tokens} tokens")

        # Reduce chat history
        if "recent_chat" in optimized and len(optimized["recent_chat"]) > 5:
            optimized["recent_chat"] = optimized["recent_chat"][-5:]

        # Reduce action history
        if "recent_actions" in optimized and len(optimized["recent_actions"]) > 3:
            optimized["recent_actions"] = optimized["recent_actions"][-3:]

        # Simplify vision summary
        if "vision_summary" in optimized:
            vision = optimized["vision_summary"]
            if len(vision) > 200:
                optimized["vision_summary"] = vision[:200] + "..."

        return optimized

    def get_system_prompt(self) -> str:
        """Get the cached system prompt."""
        return self.system_prompt

    def rebuild_system_prompt(self):
        """Rebuild system prompt (call if personality changes)."""
        self.system_prompt = build_system_prompt(self.personality_config)
        log.info("System prompt rebuilt")


if __name__ == "__main__":
    # Test the prompt builder
    from config.settings import settings

    personality = {
        "name": "CUDA-chan",
        "description": "A cheerful AI VTuber",
        "personality_traits": ["energetic", "friendly"],
        "speaking_style": ["casual", "enthusiastic"],
        "behavioral_constraints": ["stay in character", "be positive"],
        "backstory": "A tech-loving VTuber who enjoys gaming."
    }

    builder = PromptBuilder(personality)

    # Test decision prompt
    context = {
        "current_game": "Test Game",
        "current_goal": "Complete level",
        "emotional_state": "excited",
        "recent_chat": [
            {"author": "User1", "text": "Go left!"},
            {"author": "User2", "text": "Great job!"}
        ],
        "vision_summary": "Player is at a crossroads",
        "recent_actions": [{"type": "move", "details": "moved forward"}]
    }

    system, user = builder.build_decision_prompt(context)

    print("System Prompt Length:", len(system))
    print("\nUser Prompt:")
    print(user)
    print("\nEstimated tokens:", builder.estimate_tokens(system + user))
