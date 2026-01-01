#!/usr/bin/env python3
"""Track API costs for CUDA-chan."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import log


class CostTracker:
    """Track and estimate API costs."""

    # Pricing (as of 2025)
    CLAUDE_SONNET_INPUT = 0.003  # per 1K tokens
    CLAUDE_SONNET_OUTPUT = 0.015  # per 1K tokens
    ELEVENLABS_CHAR = 0.00003  # per character (Starter plan)

    def __init__(self):
        """Initialize cost tracker."""
        self.claude_tokens = 0
        self.elevenlabs_chars = 0
        self.total_cost = 0.0

    def add_claude_usage(self, input_tokens: int, output_tokens: int):
        """Add Claude API usage."""
        input_cost = (input_tokens / 1000) * self.CLAUDE_SONNET_INPUT
        output_cost = (output_tokens / 1000) * self.CLAUDE_SONNET_OUTPUT
        cost = input_cost + output_cost

        self.claude_tokens += input_tokens + output_tokens
        self.total_cost += cost

        return cost

    def add_tts_usage(self, characters: int):
        """Add TTS usage."""
        cost = characters * self.ELEVENLABS_CHAR
        self.elevenlabs_chars += characters
        self.total_cost += cost

        return cost

    def estimate_hourly_cost(
        self,
        decisions_per_minute: int = 10,
        words_per_decision: int = 30,
        chars_per_word: int = 5
    ) -> dict:
        """
        Estimate costs for one hour of streaming.

        Args:
            decisions_per_minute: AI decisions per minute
            words_per_decision: Average words spoken per decision
            chars_per_word: Average characters per word

        Returns:
            Cost breakdown dictionary
        """
        # Claude estimation
        # Assume ~1500 tokens per decision (context + response)
        decisions_per_hour = decisions_per_minute * 60
        claude_tokens_per_hour = decisions_per_hour * 1500
        claude_cost = (claude_tokens_per_hour / 1000) * (
            self.CLAUDE_SONNET_INPUT + self.CLAUDE_SONNET_OUTPUT
        ) / 2  # Average

        # ElevenLabs estimation
        chars_per_hour = (
            decisions_per_hour * words_per_decision * chars_per_word
        )
        tts_cost = chars_per_hour * self.ELEVENLABS_CHAR

        # Assume 50% cache hit rate for TTS
        tts_cost_with_cache = tts_cost * 0.5

        total_cost = claude_cost + tts_cost_with_cache

        return {
            "claude_cost": claude_cost,
            "tts_cost": tts_cost,
            "tts_cost_cached": tts_cost_with_cache,
            "total_cost": total_cost,
            "decisions_per_hour": decisions_per_hour,
            "tokens_per_hour": claude_tokens_per_hour,
            "chars_per_hour": chars_per_hour,
        }

    def get_summary(self) -> dict:
        """Get cost summary."""
        return {
            "total_cost": self.total_cost,
            "claude_tokens": self.claude_tokens,
            "elevenlabs_characters": self.elevenlabs_chars,
            "claude_cost": (self.claude_tokens / 1000) * (
                self.CLAUDE_SONNET_INPUT + self.CLAUDE_SONNET_OUTPUT
            ) / 2,
            "tts_cost": self.elevenlabs_chars * self.ELEVENLABS_CHAR,
        }

    def print_report(self):
        """Print formatted cost report."""
        print("\n╔═══════════════════════════════════════════════════════╗")
        print("║              API Cost Report                          ║")
        print("╚═══════════════════════════════════════════════════════╝\n")

        summary = self.get_summary()

        print(f"Claude API:")
        print(f"  Tokens used: {summary['claude_tokens']:,}")
        print(f"  Estimated cost: ${summary['claude_cost']:.3f}")
        print()

        print(f"ElevenLabs TTS:")
        print(f"  Characters generated: {summary['elevenlabs_characters']:,}")
        print(f"  Estimated cost: ${summary['tts_cost']:.3f}")
        print()

        print(f"Total Estimated Cost: ${summary['total_cost']:.3f}")
        print()

    def estimate_and_print(self):
        """Print cost estimates for different scenarios."""
        print("\n╔═══════════════════════════════════════════════════════╗")
        print("║         Hourly Cost Estimates                         ║")
        print("╚═══════════════════════════════════════════════════════╝\n")

        scenarios = [
            ("Conservative (6 decisions/min)", 6),
            ("Moderate (10 decisions/min)", 10),
            ("Active (15 decisions/min)", 15),
        ]

        for name, dpm in scenarios:
            est = self.estimate_hourly_cost(decisions_per_minute=dpm)
            print(f"{name}:")
            print(f"  Claude: ${est['claude_cost']:.2f}/hr")
            print(f"  TTS (cached): ${est['tts_cost_cached']:.2f}/hr")
            print(f"  Total: ${est['total_cost']:.2f}/hr")
            print()


if __name__ == "__main__":
    tracker = CostTracker()

    # Show estimates
    tracker.estimate_and_print()

    # Example usage tracking
    print("=" * 60)
    print("\nExample: Simulating 1 hour of streaming (10 decisions/min)")
    print("=" * 60)

    # Simulate usage
    for _ in range(600):  # 10 decisions/min * 60 min
        # Average API call: 1000 input, 500 output tokens
        tracker.add_claude_usage(1000, 500)
        # Average speech: 30 words * 5 chars = 150 chars
        tracker.add_tts_usage(150)

    tracker.print_report()

    print("\nNote: These are estimates. Actual costs may vary based on:")
    print("  - Conversation complexity (affects token usage)")
    print("  - TTS cache hit rate")
    print("  - Stream activity level")
    print("  - Chat interaction frequency")
