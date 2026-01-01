#!/usr/bin/env python3
"""
CUDA-chan: Autonomous AI VTuber System
Main entry point.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.orchestrator import Orchestrator
from config.settings import settings
from utils.logger import log


def print_banner():
    """Print startup banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║   ██████╗██╗   ██╗██████╗  █████╗       ██████╗██╗  ║
    ║  ██╔════╝██║   ██║██╔══██╗██╔══██╗     ██╔════╝██║  ║
    ║  ██║     ██║   ██║██║  ██║███████║     ██║     ██║  ║
    ║  ██║     ██║   ██║██║  ██║██╔══██║     ██║     ██║  ║
    ║  ╚██████╗╚██████╔╝██████╔╝██║  ██║     ╚██████╗███████╗║
    ║   ╚═════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝      ╚═════╝╚══════╝║
    ║                                                       ║
    ║         Autonomous AI VTuber System v0.1.0           ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """
    print(banner)


def check_configuration():
    """Check if configuration is valid."""
    print("Checking configuration...")

    is_valid, errors = settings.validate()

    if not is_valid:
        print("\n❌ Configuration errors found:")
        for error in errors:
            print(f"   - {error}")
        print("\nPlease check your .env file and ensure all required settings are configured.")
        print("See .env.example for reference.")
        return False

    print("✓ Configuration valid")
    return True


def print_system_info():
    """Print system information."""
    print("\nSystem Information:")
    print(f"  VTuber Name: {settings.personality.name}")
    print(f"  Personality: {', '.join(settings.personality.personality_traits[:3])}")
    print(f"  VTube Studio: ws://{settings.vtube_studio.host}:{settings.vtube_studio.port}")
    print(f"  Tick Rate: {settings.system.tick_rate}s")
    print(f"  Log Level: {settings.system.log_level}")

    if settings.youtube.video_id:
        print(f"  YouTube Video: {settings.youtube.video_id}")
    else:
        print("  YouTube Video: Not configured (chat disabled)")

    print()


async def main():
    """Main entry point."""
    print_banner()

    # Check configuration
    if not check_configuration():
        sys.exit(1)

    print_system_info()

    # Create orchestrator
    log.info("Creating orchestrator...")
    orchestrator = Orchestrator()

    # Initialize all systems
    log.info("Initializing systems...")
    if not await orchestrator.initialize():
        log.error("System initialization failed")
        sys.exit(1)

    log.success("CUDA-chan is ready!")
    print("\n" + "=" * 60)
    print("CUDA-chan is now live!")
    print("Press Ctrl+C to stop")
    print("=" * 60 + "\n")

    # Run main loop
    try:
        await orchestrator.run()
    except KeyboardInterrupt:
        print("\n\nShutdown requested...")
    except Exception as e:
        log.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        log.info("Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete.")
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
