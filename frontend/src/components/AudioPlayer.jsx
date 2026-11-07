import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause, Download, Volume2, VolumeX, RotateCcw, Sparkles } from 'lucide-react';

export default function AudioPlayer({ audioUrl, title = "Gegenereerde Audio", duration: initialDuration }) {
  const audioRef = useRef(null);
  const canvasRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(initialDuration || 0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [waveformData, setWaveformData] = useState([]);
  const animationFrameRef = useRef(null);

  // Generate pseudo-waveform bars based on url hash for visual consistency
  useEffect(() => {
    if (!audioUrl) return;
    const bars = 60;
    const data = [];
    let seed = 42;
    for (let i = 0; i < audioUrl.length; i++) {
      seed = (seed * 31 + audioUrl.charCodeAt(i)) % 1000;
    }
    for (let i = 0; i < bars; i++) {
      const v = Math.sin((i / bars) * Math.PI) * 0.5 + 0.3 + (Math.sin(i * 1.5 + seed) * 0.2);
      data.push(Math.max(0.15, Math.min(1.0, v)));
    }
    setWaveformData(data);
    setIsPlaying(false);
    setCurrentTime(0);
  }, [audioUrl]);

  // Audio event listeners
  const onLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };

  const onTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const onEnded = () => {
    setIsPlaying(false);
    setCurrentTime(0);
  };

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleSeek = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const pos = (e.clientX - rect.left) / rect.width;
    const newTime = pos * duration;
    if (audioRef.current) {
      audioRef.current.currentTime = newTime;
      setCurrentTime(newTime);
    }
  };

  const handleVolumeChange = (e) => {
    const val = parseFloat(e.target.value);
    setVolume(val);
    if (audioRef.current) {
      audioRef.current.volume = val;
      setIsMuted(val === 0);
    }
  };

  const toggleMute = () => {
    if (!audioRef.current) return;
    if (isMuted) {
      audioRef.current.volume = volume || 0.8;
      setIsMuted(false);
    } else {
      audioRef.current.volume = 0;
      setIsMuted(true);
    }
  };

  const formatTime = (seconds) => {
    if (isNaN(seconds) || seconds === 0) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  if (!audioUrl) return null;

  const progress = duration > 0 ? (currentTime / duration) : 0;

  return (
    <div className="w-full glass-panel-glow rounded-2xl p-5 border border-cyan-500/20 bg-studio-900/90 shadow-glass transition-all">
      <audio
        ref={audioRef}
        src={audioUrl}
        onLoadedMetadata={onLoadedMetadata}
        onTimeUpdate={onTimeUpdate}
        onEnded={onEnded}
      />

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse"></div>
          <span className="text-sm font-semibold text-slate-200 tracking-wide">{title}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="font-mono text-xs text-cyan-300/80 bg-studio-950/80 px-2.5 py-1 rounded-md border border-slate-800">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>
          <a
            href={audioUrl}
            download
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/30 transition-all hover:scale-105 active:scale-95"
            title="Download WAV bestand"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download WAV</span>
          </a>
        </div>
      </div>

      {/* Interactive Waveform Visualizer */}
      <div
        onClick={handleSeek}
        className="group relative h-20 w-full rounded-xl bg-studio-950/90 border border-slate-800/80 p-3 flex items-center justify-between gap-1 cursor-pointer overflow-hidden select-none hover:border-cyan-500/40 transition-colors"
      >
        {/* Glow progress bar */}
        <div
          className="absolute left-0 top-0 bottom-0 bg-gradient-to-r from-cyan-500/10 via-purple-500/10 to-cyan-500/20 border-r-2 border-cyan-400 pointer-events-none transition-all duration-75"
          style={{ width: `${progress * 100}%` }}
        />

        {waveformData.map((val, idx) => {
          const barProgress = idx / waveformData.length;
          const isPassed = barProgress <= progress;
          return (
            <div
              key={idx}
              className={`flex-1 rounded-full transition-all duration-150 ${
                isPassed
                  ? 'bg-gradient-to-t from-cyan-500 to-cyan-300 shadow-[0_0_8px_rgba(6,182,212,0.6)]'
                  : 'bg-slate-700/60 group-hover:bg-slate-600/70'
              }`}
              style={{
                height: `${Math.max(12, val * 100)}%`,
                transform: isPlaying && isPassed ? `scaleY(${0.85 + Math.random() * 0.3})` : 'scaleY(1)',
              }}
            />
          );
        })}
      </div>

      {/* Playback Controls Bar */}
      <div className="flex items-center justify-between mt-4 gap-4">
        <div className="flex items-center gap-2">
          <button
            onClick={togglePlay}
            className="flex items-center justify-center w-11 h-11 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-glow-cyan hover:brightness-110 active:scale-95 transition-all"
            aria-label={isPlaying ? 'Pauzeren' : 'Afspelen'}
          >
            {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current ml-0.5" />}
          </button>

          <button
            onClick={() => {
              if (audioRef.current) {
                audioRef.current.currentTime = 0;
                setCurrentTime(0);
              }
            }}
            className="p-2.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-studio-800 transition-colors"
            title="Herstarten"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>

        {/* Volume controls */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={toggleMute}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-studio-800 transition-colors"
          >
            {isMuted || volume === 0 ? <VolumeX className="w-4 h-4 text-rose-400" /> : <Volume2 className="w-4 h-4" />}
          </button>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={isMuted ? 0 : volume}
            onChange={handleVolumeChange}
            className="w-20 accent-cyan-400"
          />
        </div>
      </div>
    </div>
  );
}

