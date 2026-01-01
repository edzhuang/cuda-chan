#!/usr/bin/env python3
"""Test VTube Studio connection."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import websockets
from config.settings import settings


async def test_connection(host: str, port: int):
    """Test connection to VTube Studio."""
    uri = f"ws://{host}:{port}"

    print(f"\n{'='*60}")
    print(f"Testing connection to VTube Studio")
    print(f"{'='*60}\n")
    print(f"URI: {uri}")

    try:
        print(f"\nAttempting to connect...")

        # Try to connect with timeout
        async with asyncio.timeout(5):
            ws = await websockets.connect(uri)
            print(f"✅ Connection successful!")

            # Try to send a simple API state request
            request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "TestRequest",
                "messageType": "APIStateRequest",
                "data": {}
            }

            print(f"\nSending test request...")
            await ws.send(str(request))

            response = await ws.recv()
            print(f"✅ Received response!")
            print(f"Response preview: {response[:100]}...")

            await ws.close()

            print(f"\n{'='*60}")
            print(f"✅ VTube Studio connection test PASSED")
            print(f"{'='*60}\n")
            return True

    except asyncio.TimeoutError:
        print(f"\n❌ Connection timeout after 5 seconds")
        print(f"\nPossible issues:")
        print(f"  - VTube Studio is not running")
        print(f"  - Plugin API is not enabled")
        print(f"  - Firewall is blocking the connection")
        return False

    except ConnectionRefusedError:
        print(f"\n❌ Connection refused")
        print(f"\nPossible issues:")
        print(f"  - VTube Studio plugin API is not enabled")
        print(f"  - Wrong port number")
        print(f"  - VTube Studio is not listening on this address")
        return False

    except Exception as e:
        print(f"\n❌ Connection failed: {type(e).__name__}: {e}")
        return False


async def test_multiple_hosts():
    """Test multiple possible host configurations."""
    hosts_to_try = [
        ("localhost", 8001),
        ("127.0.0.1", 8001),
        ("0.0.0.0", 8001),
    ]

    results = {}

    for host, port in hosts_to_try:
        print(f"\n\nTrying {host}:{port}...")
        success = await test_connection(host, port)
        results[f"{host}:{port}"] = success

        if success:
            print(f"\n✅ SOLUTION FOUND!")
            print(f"\nAdd this to your .env file:")
            print(f"VTUBE_STUDIO_HOST={host}")
            print(f"VTUBE_STUDIO_PORT={port}")
            break

    print(f"\n\n{'='*60}")
    print(f"Summary of Connection Tests")
    print(f"{'='*60}\n")

    for uri, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status:15} {uri}")

    print(f"\n{'='*60}\n")


async def main():
    """Main test function."""
    print("\n╔═══════════════════════════════════════════════════════╗")
    print("║        VTube Studio Connection Diagnostic             ║")
    print("╚═══════════════════════════════════════════════════════╝\n")

    # First try the configured host
    print(f"Testing configured host: {settings.vtube_studio.host}:{settings.vtube_studio.port}")

    success = await test_connection(
        settings.vtube_studio.host,
        settings.vtube_studio.port
    )

    if not success:
        print(f"\nConfigured host failed. Testing alternatives...\n")
        await test_multiple_hosts()
    else:
        print(f"\nYour current configuration works! ✅")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\nTest cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
