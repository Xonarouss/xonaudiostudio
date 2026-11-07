import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause, Download, Volume2, VolumeX, RotateCcw, Repeat, Sparkles } from 'lucide-react';

export default function AudioPlayer({ audioUrl, title = "Generated Audio", subtitle = "Ready for playback", duration: initialDuration }) {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(initialDuration || 0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [isLooping, setIsLooping] = useState(false);
  const [waveformData, setWaveformData] = useState([]);

  useEffect(() => {
    if (!audioUrl) return;
    const bars = 64;
    const data = [];
    let seed = 42;
    for (let i = 0; i < audioUrl.length; i++) {
      seed = (seed * 31 + audioUrl.charCodeAt(i)) % 1000;
    }
    for (let i = 0; i < bars; i++) {
      const v = Math.sin((i / bars) * Math.PI) * 0.5 + 0.3 + (Math.sin(i * 1.6 + seed) * 0.22);
      data.push(Math.max(0.12, Math.min(1.0, v)));
    }
    setWaveformData(data);
    setIsPlaying(false);
    setCurrentTime(0);
  }, [audioUrl]);

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
    if (!isLooping) {
      setIsPlaying(false);
      setCurrentTime(0);
    }
  };

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play().catch(e => console.warn("Playback error:", e));
      setIsPlaying(true);
    }
  };

  const handleSeek = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const pos = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
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
    <div className="w-full bg-white rounded-2xl p-5 border border-cyan-500/30 shadow-md animate-fadeIn">
      <audio
        ref={audioRef}
        src={audioUrl}
        loop={isLooping}
        onLoadedMetadata={onLoadedMetadata}
        onTimeUpdate={onTimeUpdate}
        onEnded={onEnded}
      />

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-3 h-3 rounded-full bg-cyan-500 animate-pulse"></div>
          <div>
            <h4 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
              {title}
              <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-cyan-50 text-cyan-700 border border-cyan-200">
                WAV 44.1kHz
              </span>
            </h4>
            <p className="text-[11px] text-slate-500">{subtitle}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="font-mono text-xs text-slate-700 bg-slate-100 px-3 py-1 rounded-lg border border-slate-200">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>
          <a
            href={audioUrl}
            download
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-cyan-600 hover:bg-cyan-700 text-white shadow-sm transition-all hover:scale-105 active:scale-95"
            title="Download high-resolution WAV"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download WAV</span>
          </a>
        </div>
      </div>

      {/* Interactive Waveform Visualizer (White Mode with crisp contrast) */}
      <div
        onClick={handleSeek}
        className="group relative h-20 w-full rounded-xl bg-slate-50 border border-slate-200 p-3 flex items-center justify-between gap-1 cursor-pointer overflow-hidden select-none hover:border-cyan-400 transition-colors"
      >
        {/* Glow progress overlay */}
        <div
          className="absolute left-0 top-0 bottom-0 bg-gradient-to-r from-cyan-500/15 via-blue-500/15 to-cyan-500/25 border-r-2 border-cyan-600 pointer-events-none transition-all duration-75"
          style={{ width: `${progress * 100}%` }}
        />

        {waveformData.map((val, idx) => {
          const barProgress = idx / waveformData.length;
          const isPassed = barProgress <= progress;
          return (
            <div
              key={idx}
              className={`flex-1 rounded-full transition-all duration-100 ${
                isPassed
                  ? 'bg-gradient-to-t from-cyan-600 to-cyan-400 shadow-xs'
                  : 'bg-slate-300 group-hover:bg-slate-400'
              }`}
              style={{
                height: `${Math.max(14, val * 100)}%`,
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
            className="flex items-center justify-center w-11 h-11 rounded-full bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-md hover:brightness-105 active:scale-95 transition-all"
            aria-label={isPlaying ? 'Pause' : 'Play'}
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
            className="p-2.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
            title="Restart from beginning"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          <button
            onClick={() => setIsLooping(!isLooping)}
            className={`p-2.5 rounded-lg transition-colors ${
              isLooping ? 'text-cyan-700 bg-cyan-100 border border-cyan-300' : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100'
            }`}
            title="Toggle loop"
          >
            <Repeat className="w-4 h-4" />
          </button>
        </div>

        {/* Volume controls */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={toggleMute}
            className="p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
          >
            {isMuted || volume === 0 ? <VolumeX className="w-4 h-4 text-rose-500" /> : <Volume2 className="w-4 h-4" />}
          </button>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={isMuted ? 0 : volume}
            onChange={handleVolumeChange}
            className="w-20 accent-cyan-600"
          />
        </div>
      </div>
    </div>
  );
}
