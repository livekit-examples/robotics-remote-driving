"""Audio I/O: subscribe to agent audio (speaker) and publish mic to LiveKit room."""

import asyncio
import logging

from livekit import rtc

logger = logging.getLogger("local-bridge")

SAMPLE_RATE = 48000
CHANNELS = 1


class AudioBridge:
    """Manages mic publishing and agent audio playback for a LiveKit room."""

    def __init__(self, room: rtc.Room):
        self._room = room
        self._devices = rtc.MediaDevices(
            input_sample_rate=SAMPLE_RATE,
            output_sample_rate=SAMPLE_RATE,
            num_channels=CHANNELS,
        )
        self._mic = None
        self._mic_track: rtc.LocalAudioTrack | None = None
        self._player = None

    async def start(self):
        """Open mic + speaker, publish mic track, and listen for agent audio."""
        # Open input first so APM is shared with output for AEC
        self._mic = self._devices.open_input(
            enable_aec=True,
            noise_suppression=True,
            high_pass_filter=True,
            auto_gain_control=True,
        )
        self._player = self._devices.open_output()

        @self._room.on("track_subscribed")
        def on_track_subscribed(
            track: rtc.Track,
            publication: rtc.RemoteTrackPublication,
            participant: rtc.RemoteParticipant,
        ):
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                logger.info(f"Subscribed to audio: {participant.identity}:{track.name}")
                asyncio.create_task(self._player.add_track(track))

        @self._room.on("track_unsubscribed")
        def on_track_unsubscribed(
            track: rtc.Track,
            publication: rtc.RemoteTrackPublication,
            participant: rtc.RemoteParticipant,
        ):
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                logger.info(f"Audio unsubscribed: {participant.identity}:{track.name}")
                asyncio.create_task(self._player.remove_track(track))

        # Publish mic track
        self._mic_track = rtc.LocalAudioTrack.create_audio_track(
            "microphone", self._mic.source
        )
        opts = rtc.TrackPublishOptions()
        opts.source = rtc.TrackSource.SOURCE_MICROPHONE
        await self._room.local_participant.publish_track(self._mic_track, opts)
        logger.info("Published mic track")

        await self._player.start()
        logger.info("Audio bridge started (mic + speaker)")

    async def close(self):
        """Clean up audio resources."""
        if self._player:
            await self._player.aclose()
        if self._mic:
            await self._mic.aclose()
        logger.info("Audio bridge closed")
