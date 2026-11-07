import React, { useState, useEffect } from 'react';
import { Radio, Sparkles, Volume2, Sliders, RefreshCw, CheckCircle2, AlertCircle, History, Clock, Hash, Play, Activity } from 'lucide-react';
import AudioPlayer from './AudioPlayer';

const PRESET_PROMPTS = [
  { label: '🌩️ Thunder & Rain', prompt: 'Cinematic thunder strike in the distance with gentle rain pouring on asphalt', duration: 12 },
  { label: '🚀 Sci-Fi Laser', prompt: 'Futuristic sci-fi laser blast weapon charging up and firing with heavy energy echo', duration: 4 },
  { label: '👣 Gravel Footsteps', prompt: 'Heavy boots walking steadily on loose gravel path outdoors', duration: 8 },
  { label: '🏎️ V8 Muscle Car', prompt: 'Aggressive V8 muscle car engine revving up and accelerating fast on asphalt', duration: 10 },
  { label: '🌌 Deep Space Drone', prompt: 'Dark cinematic atmospheric drone with deep sub bass rumbling in deep space', duration: 20 },
  { label: '💥 Trailer Impact', prompt: 'Massive Hollywood movie trailer impact boom with reverberating brass hit', duration: 6 },
  { label: '🔥 Campfire Crackle', prompt: 'Cozy fireplace campfire crackling wood embers gently burning in silence', duration: 15 },
  { label: '🌊 Ocean Waves', prompt: 'Calm ocean waves crashing gently on a sandy beach during sunset', duration: 16 }
];

export default function SoundStudio({ modelsStatus, onOpenModelManager }) {
  const [prompt, setPrompt] = useState('Cinematic massive explosion followed by falling debris and reverberation');
  const [negativePrompt, setNegativePrompt] = useState('low quality, distortion, harsh, noisy, speech, human voice');
  const [duration, setDuration] = useState(10);
  const [steps, setSteps] = useState(50);
  const [cfgScale, setCfgScale] = useState(7.0);
  const [seed, setSeed] = useState(-1);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isEnhancing, setIsEnhancing] = useState(false);

  // Generation & Progress states
  const [isGenerating, setIsGenerating] = useState(false);
  const [progressPercent, setProgressPercent] = useState(0);
  const [progressStage, setProgressStage] = useState('');
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [generatedAudioUrl, setGeneratedAudioUrl] = useState(null);
  const [lastPrompt, setLastPrompt] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [history, setHistory] = useState([]);

  const isModelReady = modelsStatus?.stable_audio?.installed;

  // Progress simulation timer during diffusion
  useEffect(() => {
    let timer = null;
    let stepTimer = null;
    if (isGenerating) {
      setProgressPercent(8);
      setProgressStage('Initializing Stable Audio Open diffusion pipeline...');
      setElapsedSeconds(0);

      timer = setInterval(() => {
        setElapsedSeconds(s => s + 1);
      }, 1000);

      stepTimer = setInterval(() => {
        setProgressPercent(p => {
          if (p < 30) {
            setProgressStage('Encoding text conditioning with T5 / CLAP...');
            return p + 5;
          } else if (p < 85) {
            const currentStep = Math.round((p / 85) * steps);
            setProgressStage(`Denoising stereo audio latent (${currentStep}/${steps} steps)...`);
            return p + 3;
          } else if (p < 95) {
            setProgressStage(`Decoding 44.1kHz stereo waveform via Autoencoder (${duration}s)...`);
            return p + 2;
          }
          return p;
        });
      }, 350);
    } else {
      if (progressPercent > 0 && progressPercent < 100) {
        setProgressPercent(100);
        setProgressStage('Complete!');
      }
    }
    return () => {
      clearInterval(timer);
      clearInterval(stepTimer);
    };
  }, [isGenerating, steps, duration]);

  const handleEnhanceWithLlama = async () => {
    if (!prompt.trim() || isEnhancing) return;
    setIsEnhancing(true);
    try {
      const res = await fetch('/api/llama/enhance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt, mode: 'sfx' })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.enhanced) {
          setPrompt(data.enhanced);
        }
      }
    } catch (e) {
      console.warn("Llama enhance error:", e);
    } finally {
      setIsEnhancing(false);
    }
  };

  const handleApplyPreset = (preset) => {
    setPrompt(preset.prompt);
    setDuration(preset.duration);
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setErrorMessage('Please enter a description for the sound effect.');
      return;
    }

    if (!isModelReady) {
      setErrorMessage('Stable Audio Open model is not installed. Download it via Model Manager.');
      return;
    }

    setIsGenerating(true);
    setErrorMessage('');

    try {
      const res = await fetch('/api/sfx/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          negative_prompt: negativePrompt,
          duration: Number(duration),
          steps: Number(steps),
          cfg_scale: Number(cfgScale),
          seed: Number(seed),
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Generation error' }));
        throw new Error(err.detail || 'Failed to generate sound effect.');
      }

      const data = await res.json();
      setProgressPercent(100);
      setProgressStage('Audio generated successfully!');
      setGeneratedAudioUrl(data.audio_url);
      setLastPrompt(prompt);

      const newEntry = {
        id: Date.now(),
        title: prompt.length > 40 ? prompt.substring(0, 40) + '...' : prompt,
        url: data.audio_url,
        duration: duration,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      };
      setHistory(prev => [newEntry, ...prev.slice(0, 9)]);
    } catch (err) {
      setErrorMessage(err.message || 'An error occurred during audio synthesis.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 bg-white rounded-2xl border border-slate-200/90 shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-purple-100 text-purple-800 border border-purple-200">
              Stable Audio Open 1.0
            </span>
            <span className="text-xs text-slate-500 font-medium">High-Resolution 44.1kHz Foley &amp; Sound FX Diffusion (Up to 47s)</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Radio className="w-6 h-6 text-purple-600" />
            Sound Studio
          </h2>
        </div>

        {/* Model status pill */}
        <div className="flex items-center gap-2">
          {isModelReady ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-semibold">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Model Ready</span>
            </div>
          ) : (
            <button
              onClick={onOpenModelManager}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-700 text-xs font-semibold hover:bg-amber-100 transition-colors"
            >
              <AlertCircle className="w-4 h-4 text-amber-600" />
              <span>Model Missing (Download in Manager)</span>
            </button>
          )}
        </div>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center justify-between shadow-xs animate-fadeIn">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-600" />
            <span className="font-medium">{errorMessage}</span>
          </div>
          <button
            onClick={() => setErrorMessage('')}
            className="text-xs font-semibold text-rose-600 hover:text-rose-800"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Main Studio Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Prompting & Presets */}
        <div className="lg:col-span-7 space-y-6">
          {/* Preset Buttons */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2.5">
            <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">Quick Inspiration Presets:</span>
            <div className="flex flex-wrap gap-2">
              {PRESET_PROMPTS.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handleApplyPreset(p)}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 hover:border-purple-300 transition-all active:scale-95 shadow-2xs"
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Sound Prompt Input */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-bold text-slate-800">
                Sound Description (Prompt)
              </label>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleEnhanceWithLlama}
                  disabled={isEnhancing || !prompt.trim()}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 transition-all active:scale-95 disabled:opacity-50"
                  title="Enhance with Hollywood-grade acoustics using local Llama AI"
                >
                  <Sparkles className={`w-3.5 h-3.5 text-purple-600 ${isEnhancing ? 'animate-spin' : ''}`} />
                  <span>{isEnhancing ? 'Enhancing...' : 'Enhance with Llama 🪄'}</span>
                </button>
                <span className="text-xs font-mono text-slate-500">{prompt.length} chars</span>
              </div>
            </div>
            <textarea
              rows={4}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe the desired sound effect in detail (e.g. Cinematic sub bass impact, rain on a tent, futuristic sci-fi UI clicks)..."
              className="w-full rounded-xl p-4 text-sm glass-input text-slate-900 placeholder-slate-400 resize-none font-sans leading-relaxed shadow-xs"
            />
            <p className="text-[11px] text-slate-500">
              Tip: Include acoustics and environment terms (e.g., "reverberant hall", "close-up foley", "outdoor ambience") for pristine results.
            </p>
          </div>

          {/* Duration Slider (1 to 47 seconds) */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-purple-600" />
                <span className="text-sm font-bold text-slate-800">Audio Clip Duration</span>
              </div>
              <span className="font-mono text-lg font-extrabold text-purple-700 bg-purple-50 px-3 py-1 rounded-lg border border-purple-200 shadow-2xs">
                {duration}s
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="47"
              step="1"
              value={duration}
              onChange={(e) => setDuration(parseInt(e.target.value))}
              className="w-full accent-purple-600"
            />
            <div className="flex justify-between text-[11px] font-mono text-slate-500">
              <span>1 second</span>
              <span>24 seconds</span>
              <span>47 seconds (Max)</span>
            </div>
          </div>
        </div>

        {/* Right Column: Parameters, Progress Bar, & Visible Output */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-slate-800 flex items-center gap-2">
                <Sliders className="w-4 h-4 text-purple-600" />
                Synthesis Parameters
              </span>
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="text-xs text-purple-700 hover:text-purple-800 font-semibold"
              >
                {showAdvanced ? 'Simple' : 'Advanced'}
              </button>
            </div>

            {/* Steps slider */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-slate-700 font-medium">
                <span>Inference Steps</span>
                <span className="font-mono text-purple-700 font-bold">{steps} steps</span>
              </div>
              <input
                type="range"
                min="25"
                max="100"
                step="5"
                value={steps}
                onChange={(e) => setSteps(parseInt(e.target.value))}
                className="w-full accent-purple-600"
              />
            </div>

            {/* CFG Scale */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-slate-700 font-medium">
                <span>Prompt Guidance (CFG Scale)</span>
                <span className="font-mono text-purple-700 font-bold">{cfgScale.toFixed(1)}</span>
              </div>
              <input
                type="range"
                min="1.0"
                max="15.0"
                step="0.5"
                value={cfgScale}
                onChange={(e) => setCfgScale(parseFloat(e.target.value))}
                className="w-full accent-purple-600"
              />
            </div>

            {showAdvanced && (
              <div className="space-y-4 pt-3 border-t border-slate-100 animate-fadeIn">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-700">Negative Prompt:</label>
                  <input
                    type="text"
                    value={negativePrompt}
                    onChange={(e) => setNegativePrompt(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-lg glass-input text-slate-900 shadow-xs"
                  />
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs text-slate-700 font-semibold">
                    <span className="flex items-center gap-1">
                      <Hash className="w-3.5 h-3.5 text-purple-600" />
                      Seed (-1 for random)
                    </span>
                    <button
                      onClick={() => setSeed(Math.floor(Math.random() * 999999))}
                      className="text-[11px] text-purple-600 hover:underline"
                    >
                      Randomize
                    </button>
                  </div>
                  <input
                    type="number"
                    value={seed}
                    onChange={(e) => setSeed(parseInt(e.target.value) || -1)}
                    className="w-full px-3 py-2 text-xs rounded-lg glass-input text-slate-900 font-mono shadow-xs"
                  />
                </div>
              </div>
            )}

            {/* BEAUTIFUL VISIBLE PROGRESS BAR */}
            {isGenerating && (
              <div className="space-y-2 pt-2 p-4 bg-slate-50 rounded-xl border border-purple-100 animate-fadeIn">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-800 flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-purple-600 animate-pulse" />
                    {progressStage}
                  </span>
                  <span className="font-mono font-bold text-purple-700">{progressPercent}% ({elapsedSeconds}s)</span>
                </div>
                {/* Progress bar track */}
                <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden shadow-inner">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-purple-500 via-indigo-500 to-cyan-500 transition-all duration-300 shadow-sm"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>
            )}

            {/* Generate Action Button */}
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className={`w-full py-4 px-6 rounded-xl font-bold text-sm flex items-center justify-center gap-2.5 shadow-md transition-all duration-200 ${
                isGenerating
                  ? 'bg-slate-200 text-slate-400 cursor-not-allowed border border-slate-300'
                  : 'bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-600 text-white hover:brightness-105 active:scale-[0.99] shadow-purple-600/20'
              }`}
            >
              {isGenerating ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin text-purple-600" />
                  <span>Synthesizing Sound ({progressPercent}%)...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  <span>Generate Sound Effect</span>
                </>
              )}
            </button>
          </div>

          {/* Generated Waveform Player (Visible Results) */}
          {generatedAudioUrl ? (
            <div className="space-y-2">
              <AudioPlayer
                audioUrl={generatedAudioUrl}
                title="Stable Audio Open Effect"
                subtitle={lastPrompt.length > 50 ? lastPrompt.substring(0, 50) + '...' : lastPrompt}
                duration={duration}
              />
            </div>
          ) : (
            <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center flex flex-col items-center justify-center gap-3 shadow-xs">
              <div className="w-14 h-14 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-400">
                <Volume2 className="w-7 h-7" />
              </div>
              <p className="text-sm font-bold text-slate-800">No sound effect generated yet</p>
              <p className="text-xs text-slate-500 max-w-xs">
                Pick an inspiration preset or enter a prompt, then click [Generate Sound Effect]. The result will display here immediately.
              </p>
            </div>
          )}

          {/* History Gallery */}
          {history.length > 0 && (
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
              <h4 className="text-xs font-bold text-slate-800 flex items-center gap-2 uppercase tracking-wider">
                <History className="w-3.5 h-3.5 text-purple-600" />
                Recent Foley Clips ({history.length})
              </h4>
              <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
                {history.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => {
                      setGeneratedAudioUrl(item.url);
                      setLastPrompt(item.title);
                    }}
                    className={`p-2.5 rounded-lg border cursor-pointer flex items-center justify-between gap-2 text-xs transition-colors ${
                      generatedAudioUrl === item.url
                        ? 'bg-purple-50 border-purple-300 text-purple-900 font-semibold'
                        : 'bg-slate-50 hover:bg-slate-100 border-slate-200 text-slate-700'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <Play className="w-3 h-3 text-purple-600 flex-shrink-0" />
                      <span className="truncate">{item.title}</span>
                    </div>
                    <span className="text-[10px] text-purple-700 font-mono flex-shrink-0">{item.duration}s</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
