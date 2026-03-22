import { useState, useCallback, useMemo } from "react";
import { cn } from "./lib/utils";
import { useLiveKit } from "./hooks/use-livekit";
import { useControls, heldToControls } from "./hooks/use-controls";
import { useRecorder } from "./hooks/use-recorder";
import { useReplay } from "./hooks/use-replay";
import { ConnectBar } from "./components/connect-bar";
import { VideoDisplay } from "./components/video-display";
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
  const controlState = useMemo(() => heldToControls(controls.held), [controls.held]);

  const handleConnect = useCallback(
    (url: string, token: string) => livekit.connect(url, token),
    [livekit.connect],
  );

  const handleDisconnect = useCallback(() => {
    controls.releaseAll();
    livekit.disconnect();
  }, [controls.releaseAll, livekit.disconnect]);

  return (
    <div className="flex flex-col h-screen bg-black select-none pt-12 px-4 gap-2">
      {/* Titlebar / drag region — breaks out of px-8 so drag area spans full window width */}
      <div className="shrink-0 [-webkit-app-region:drag] flex items-center justify-start relative -mx-8 px-8">
        <div className="flex [-webkit-app-region:no-drag] bg-white/[0.04] rounded-[3px] p-0.5">
          {(["teleop", "replay"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                "px-5 py-1.5 rounded-[2px] text-[11px] font-medium tracking-wide uppercase transition-colors cursor-pointer",
                activeTab === tab
                  ? "bg-white/10 text-white/80"
                  : "text-white/30 hover:text-white/50",
              )}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Teleop tab */}
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

      {/* Status bar — breaks out of px-8 so border spans full window width */}
      <div className="shrink-0 -mx-8 px-8 border-t border-white/[0.04]">
        <StatusBar
          tab={activeTab}
          connectionState={livekit.connectionState}
          isRecording={recorder.isRecording}
          frameCount={
            activeTab === "teleop" ? recorder.frameCount : replay.currentIndex
          }
          rtt={livekit.rtt}
          isReplayLoaded={replay.isLoaded}
          replayTotalFrames={replay.totalFrames}
          isReplayPlaying={replay.isPlaying}
        />
      </div>
    </div>
  );
}
