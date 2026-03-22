import { useState, useCallback } from 'react'
import { cn } from './lib/utils'
import { useLiveKit } from './hooks/use-livekit'
import { useControls } from './hooks/use-controls'
import { useRecorder } from './hooks/use-recorder'
import { useReplay } from './hooks/use-replay'
import { ConnectBar } from './components/connect-bar'
import { VideoDisplay } from './components/video-display'
import { KeyOverlay } from './components/key-overlay'
import { RecordButton } from './components/record-button'
import { ReplayView } from './components/replay-view'
import { StatusBar } from './components/status-bar'

type Tab = 'teleop' | 'replay'

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('teleop')
  const livekit = useLiveKit()
  const controls = useControls(
    livekit.sendControl,
    activeTab === 'teleop' && livekit.connectionState === 'connected'
  )
  const recorder = useRecorder()
  const replay = useReplay()

  const handleConnect = useCallback(
    (url: string, token: string) => livekit.connect(url, token),
    [livekit.connect]
  )

  const handleDisconnect = useCallback(() => {
    controls.releaseAll()
    livekit.disconnect()
  }, [controls.releaseAll, livekit.disconnect])

  return (
    <div className="flex flex-col h-screen bg-black select-none">
      {/* Titlebar with tabs */}
      <div className="h-12 shrink-0 [-webkit-app-region:drag] flex items-center px-20">
        <span className="text-[11px] font-medium text-white/40 tracking-wide uppercase mr-6">
          Remote Operator
        </span>
        <div className="flex gap-1 [-webkit-app-region:no-drag]">
          {(['teleop', 'replay'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                'px-3 py-1 rounded-md text-[11px] font-medium tracking-wide uppercase transition-colors cursor-pointer',
                activeTab === tab
                  ? 'bg-white/10 text-white/70'
                  : 'text-white/25 hover:text-white/40 hover:bg-white/[0.04]'
              )}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Teleop tab */}
      {activeTab === 'teleop' && (
        <>
          <ConnectBar
            connectionState={livekit.connectionState}
            onConnect={handleConnect}
            onDisconnect={handleDisconnect}
            error={livekit.error}
          />

          <main className="flex-1 relative overflow-hidden mx-3 mb-3 rounded-lg border border-white/[0.06] bg-white/[0.02]">
            <VideoDisplay
              videoTrack={livekit.videoTrack}
              connectionState={livekit.connectionState}
              isRecording={recorder.isRecording}
              onFrame={recorder.captureFrame}
            />
            <KeyOverlay held={controls.held} />
            {livekit.connectionState === 'connected' && (
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
      {activeTab === 'replay' && (
        <>
          {/* Spacer to match ConnectBar height */}
          <div className="shrink-0 h-3" />
          <ReplayView replay={replay} />
        </>
      )}

      <StatusBar
        tab={activeTab}
        connectionState={livekit.connectionState}
        isRecording={recorder.isRecording}
        frameCount={activeTab === 'teleop' ? recorder.frameCount : replay.currentIndex}
        isReplayLoaded={replay.isLoaded}
        replayTotalFrames={replay.totalFrames}
        isReplayPlaying={replay.isPlaying}
      />
    </div>
  )
}
