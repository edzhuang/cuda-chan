# Control Module - DEPRECATED

**Status**: Deprecated as of sidekick mode conversion

## Why Deprecated

CUDA-chan has been converted from an autonomous game-playing VTuber to an AI sidekick/co-host. The sidekick does NOT control the game - the human streamer does. Therefore, these input control modules are no longer used.

## Files in This Module

- `input_controller.py` - PyAutoGUI keyboard/mouse automation
- `action_validator.py` - Safety validation for game inputs

## Future Use

These modules may be useful if you want to add limited automation features in the future, such as:
- Emergency failsafe controls
- Automated scene switching in OBS
- Simple macro execution

For now, they remain in the codebase but are not imported or used by the main system.
