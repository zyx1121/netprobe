# Joins a LiveKit room with a token and publishes a tone; reports whether
# WebRTC media connects from this network.
import asyncio, math, os, sys
from livekit import rtc

async def main():
    room = rtc.Room()
    states = []
    room.on("connection_state_changed", lambda s: states.append(rtc.ConnectionState.Name(s)))
    try:
        await asyncio.wait_for(room.connect(os.environ["LK_URL"], os.environ["TOKEN"]), 30)
    except Exception as e:
        print("CONNECT FAILED:", type(e).__name__, e)
        print("states:", states)
        sys.exit(1)
    print("signaling+ICE connected, states:", states)
    src = rtc.AudioSource(48000, 1)
    track = rtc.LocalAudioTrack.create_audio_track("tone", src)
    pub = await room.local_participant.publish_track(track, rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE))
    print("published", pub.sid)
    frame = rtc.AudioFrame.create(48000, 1, 480)
    for i in range(1500):  # 15 s of 10 ms frames
        data = frame.data
        for j in range(480):
            data[j] = int(8000 * math.sin(2 * math.pi * 440 * (i * 480 + j) / 48000))
        await src.capture_frame(frame)
    stats = await room.local_participant.get_rtc_stats() if hasattr(room.local_participant, "get_rtc_stats") else None
    print("done, states:", states)
    await room.disconnect()

async def attempt(n):
    room = rtc.Room()
    t = asyncio.get_event_loop().time()
    try:
        await asyncio.wait_for(room.connect(os.environ["LK_URL"], os.environ["TOKEN"]), 90)
        print(f"attempt {n}: connected in {asyncio.get_event_loop().time() - t:.1f}s")
        await asyncio.sleep(3)
        await room.disconnect()
        return True
    except Exception as e:
        print(f"attempt {n}: FAILED after {asyncio.get_event_loop().time() - t:.1f}s {type(e).__name__} {e}")
        return False

async def many():
    ok = [await attempt(i) for i in range(1, 4)]
    print("success", sum(ok), "of", len(ok))

asyncio.run(many())
