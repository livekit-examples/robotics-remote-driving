import { useState, useCallback, useMemo } from "react";
import { cn } from "./lib/utils";
import { useLiveKit } from "./hooks/use-livekit";
import { useControls, heldToControls } from "./hooks/use-controls";
import { useRecorder } from "./hooks/use-recorder";
import { useReplay } from "./hooks/use-replay";
import { ConnectBar } from "./components/connect-bar";
import { VideoDisplay, type VideoMeta } from "./components/video-display";
import { KeyOverlay } from "./components/key-overlay";
import { RecordButton } from "./components/record-button";
import { ReplayView } from "./components/replay-view";
import { StatusBar } from "./components/status-bar";

type Tab = "teleop" | "replay";

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("teleop");
  const livekit = useLiveKit();
  const controls = useControls(
    livekit.sendControl,
    activeTab === "teleop" && livekit.connectionState === "connected",
  );
  const recorder = useRecorder();
  const replay = useReplay();
  const [videoMeta, setVideoMeta] = useState<VideoMeta | null>(null);
  const controlState = useMemo(
    () => heldToControls(controls.held),
    [controls.held],
  );

  const handleConnect = useCallback(
    (url: string, token: string) => livekit.connect(url, token),
    [livekit.connect],
  );

  const handleDisconnect = useCallback(() => {
    controls.releaseAll();
    livekit.disconnect();
  }, [controls.releaseAll, livekit.disconnect]);

  return (
    <div className="flex flex-col h-screen bg-black select-none">
      {/* Title bar */}
      <div className="shrink-0 h-12 [-webkit-app-region:drag] flex items-center justify-center bg-white/[0.02] border-b border-white/[0.06]">
        <div className="flex [-webkit-app-region:no-drag] bg-white/[0.04] rounded-[3px] p-0.5 gap-0.5">
          {[
            {
              id: "teleop" as const,
              label: "Teleop",
              icon: (
                <svg
                  className="w-3.5 h-3.5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z"
                  />
                </svg>
              ),
            },
            {
              id: "replay" as const,
              label: "Replay",
              icon: (
                <svg
                  className="w-3.5 h-3.5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z"
                  />
                </svg>
              ),
            },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "flex items-center gap-1.5 px-4 py-1.5 rounded-[2px] text-[11px] font-medium tracking-wide uppercase transition-colors cursor-pointer",
                activeTab === tab.id
                  ? "bg-white/10 text-white/80"
                  : "text-white/30 hover:text-white/50",
              )}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col min-h-0 px-4 pt-2 gap-2">
        {activeTab === "teleop" && (
          <>
            <ConnectBar
              connectionState={livekit.connectionState}
              onConnect={handleConnect}
              onDisconnect={handleDisconnect}
              error={livekit.error}
            />

            <main className="flex-1 relative overflow-hidden rounded-[3px] border border-white/[0.06] bg-white/[0.02]">
              <VideoDisplay
                videoTrack={livekit.videoTrack}
                connectionState={livekit.connectionState}
                isRecording={recorder.isRecording}
                controls={controlState}
                onFrame={recorder.captureFrame}
                onMeta={setVideoMeta}
              />
              {livekit.connectionState === "connected" && (
                <KeyOverlay held={controls.held} />
              )}
              {livekit.connectionState === "connected" && (
                <RecordButton
                  isRecording={recorder.isRecording}
                  frameCount={recorder.frameCount}
                  elapsed={recorder.elapsed}
                  onStart={recorder.startRecording}
                  onStop={recorder.stopRecording}
                />
              )}
            </main>
          </>
        )}

        {/* Replay tab */}
        {activeTab === "replay" && <ReplayView replay={replay} />}

        {/* Status bar */}
        <div className="shrink-0 border-t border-white/[0.04] px-4">
          <StatusBar
            tab={activeTab}
            connectionState={livekit.connectionState}
            isRecording={recorder.isRecording}
            frameCount={
              activeTab === "teleop" ? recorder.frameCount : replay.currentIndex
            }
            rtt={livekit.rtt}
            videoMeta={videoMeta}
            isReplayLoaded={replay.isLoaded}
            replayTotalFrames={replay.totalFrames}
            isReplayPlaying={replay.isPlaying}
          />
        </div>
      </div>
    </div>
  );
}
