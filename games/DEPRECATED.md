# Games Module - DEPRECATED

**Status**: Deprecated as of sidekick mode conversion

## Why Deprecated

CUDA-chan has been converted from an autonomous game-playing VTuber to an AI sidekick/co-host. The sidekick does NOT play games - the human streamer does. Therefore, these game controller modules are no longer used.

## Files in This Module

- `game_controllers/` - Various game-specific controllers for autonomous gameplay

## Current Approach

Instead of controlling games, CUDA-chan now:
- **Watches** the game screen via vision system
- **Reacts** to what's happening in the game
- **Provides commentary** on gameplay
- **Engages with chat** about the game

The vision system (`vision/screen_capture.py`) is still used to see what's happening on screen, but no game inputs are sent.

## Future Use

These modules could be repurposed for:
- Game state detection (understanding what's happening)
- Automated testing of games
- Tutorial/demo mode where CUDA-chan shows specific mechanics

For now, they remain in the codebase but are not imported or used by the main system.
