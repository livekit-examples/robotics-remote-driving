import { useEffect, useRef, useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import { Spinner } from "./ui/spinner";
import { KeyOverlay } from "./key-overlay";
import type { ReplayState } from "../hooks/use-replay";

interface ReplayViewProps {
  replay: ReplayState;
}

function DropZone({
  onOpen,
  onDrop,
  isLoading,
}: {
  onOpen: () => void;
  onDrop: (path: string) => void;
  isLoading: boolean;
}) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      const file = e.dataTransfer.files[0] as File & { path: string };
      if (file && file.name.endsWith(".mcap")) {
        onDrop(file.path);
      }
    },
    [onDrop],
  );

  if (isLoading) {
    return (
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <Spinner className="w-8 h-8 mx-auto mb-4" />
          <p className="text-white/30 text-sm">Loading episode...</p>
        </div>
      </div>
    );
  }

  return (
    <div
      className="absolute inset-0 flex items-center justify-center cursor-pointer"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={onOpen}
    >
      <div
        className={cn(
          "absolute inset-5 rounded-[3px] border-2 border-dashed transition-colors",
          isDragging
            ? "border-cyan-500/60 bg-cyan-500/5"
            : "border-white/[0.08]",
        )}
      />
      <div className="text-center relative z-10">
        <div
          className={cn(
            "w-16 h-16 mx-auto mb-5 rounded-[3px] flex items-center justify-center transition-colors",
            isDragging ? "bg-cyan-500/10" : "bg-white/5",
          )}
        >
          <svg
            className={cn(
              "w-8 h-8 transition-colors",
              isDragging ? "text-cyan-500/60" : "text-white/20",
            )}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
            />
          </svg>
        </div>
        <p className="text-white/40 text-sm font-medium">
          {isDragging ? "Drop to load" : "Drop .mcap file or click to open"}
        </p>
        <p className="text-white/20 text-xs mt-1.5">Replay recorded episodes</p>
      </div>
    </div>
  );
}

function PlaybackBar({ replay }: { replay: ReplayState }) {
  const barRef = useRef<HTMLDivElement>(null);

  const handleBarClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const bar = barRef.current;
      if (!bar) return;
      const rect = bar.getBoundingClientRect();
      const ratio = Math.max(
        0,
        Math.min(1, (e.clientX - rect.left) / rect.width),
      );
      replay.seek(Math.round(ratio * (replay.totalFrames - 1)));
    },
    [replay],
  );

  const progress =
    replay.totalFrames > 1
      ? (replay.currentIndex / (replay.totalFrames - 1)) * 100
      : 0;

  return (
    <div className="absolute bottom-0 left-0 right-0 z-20">
      <div className="bg-gradient-to-t from-black/80 to-transparent pt-14 pb-6 px-6">
        <div className="flex items-center gap-2">
          {/* Play/Pause */}
          <button
            onClick={replay.togglePlayback}
            className="w-9 h-9 flex items-center justify-center rounded-[3px] bg-white/10 hover:bg-white/20 transition-colors cursor-pointer"
          >
            {replay.isPlaying ? (
              <svg
                className="w-4 h-4 text-white"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
              </svg>
            ) : (
              <svg
                className="w-4 h-4 text-white ml-0.5"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
          </button>

          {/* Prev/Next */}
          <button
            onClick={replay.prevFrame}
            className="text-white/40 hover:text-white/70 transition-colors cursor-pointer"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15.75 19.5 8.25 12l7.5-7.5"
              />
            </svg>
          </button>
          <button
            onClick={replay.nextFrame}
            className="text-white/40 hover:text-white/70 transition-colors cursor-pointer"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="m8.25 4.5 7.5 7.5-7.5 7.5"
              />
            </svg>
          </button>

          {/* Progress bar */}
          <div
            ref={barRef}
            className="flex-1 h-1.5 bg-white/10 rounded-[2px] cursor-pointer relative group"
            onClick={handleBarClick}
          >
            <div
              className="h-full bg-cyan-500 rounded-[2px] transition-[width] duration-75 relative"
              style={{ width: `${progress}%` }}
            >
              <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 rounded-[2px] bg-white opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
          </div>

          {/* Frame counter */}
          <span className="text-white/40 text-xs font-mono min-w-[5rem] text-right">
            {replay.currentIndex + 1} / {replay.totalFrames}
          </span>
        </div>
      </div>
    </div>
  );
}

export function ReplayView({ replay }: ReplayViewProps) {
  // Keyboard shortcuts for replay
  useEffect(() => {
    if (!replay.isLoaded) return;

    const handleKey = (e: KeyboardEvent) => {
      if (e.key === " ") {
        e.preventDefault();
        replay.togglePlayback();
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        replay.nextFrame();
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        replay.prevFrame();
      } else if (e.key === "Escape") {
        replay.close();
      }
    };

    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [
    replay.isLoaded,
    replay.togglePlayback,
    replay.nextFrame,
    replay.prevFrame,
    replay.close,
  ]);

  if (!replay.isLoaded) {
    return (
      <div className="flex-1 relative overflow-hidden flex-1 rounded-[3px] border border-white/[0.06] bg-white/[0.02]">
        <DropZone
          onOpen={replay.loadFile}
          onDrop={replay.loadFromDrop}
          isLoading={replay.isLoading}
        />
      </div>
    );
  }

  const currentFrame = replay.frames[replay.currentIndex];

  return (
    <div className="flex-1 relative overflow-hidden flex-1 rounded-[3px] border border-white/[0.06] bg-black">
      {/* Close button */}
      <button
        onClick={replay.close}
        className="absolute top-5 left-5 z-30 w-9 h-9 flex items-center justify-center rounded-[3px] bg-black/40 backdrop-blur-md border border-white/[0.08] hover:border-white/20 transition-colors cursor-pointer"
      >
        <svg
          className="w-4 h-4 text-white/50"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M6 18 18 6M6 6l12 12"
          />
        </svg>
      </button>

      {currentFrame && (
        <img
          src={`data:image/jpeg;base64,${currentFrame.jpeg}`}
          alt=""
          className="absolute inset-0 w-full h-full object-contain"
        />
      )}
      <KeyOverlay held={replay.held} className="bottom-20" />
      <PlaybackBar replay={replay} />
    </div>
  );
}
