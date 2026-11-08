import React, { useState, useEffect } from 'react';
import { Radio, Sparkles, Volume2, Sliders, RefreshCw, CheckCircle2, AlertCircle, History, Clock, Hash, Play, Activity } from 'lucide-react';
import AudioPlayer from './AudioPlayer';

const PRESET_PROMPTS = [
  { label: '🚗 Reversing Car & Screeching', prompt: 'Car engine reversing fast followed by sudden loud screeching tires skidding on asphalt', duration: 6, engine: 'audioldm2' },
  { label: '🚪 Footsteps & Door Slam', prompt: 'Heavy boots walking quickly on wooden floor followed by a loud heavy wooden door slamming shut', duration: 7, engine: 'audioldm2' },
  { label: '🌩️ Thunder & Rain', prompt: 'Cinematic thunder strike in the distance with gentle rain pouring on asphalt', duration: 12, engine: 'stable_audio' },
  { label: '🎬 Cinematic Impact', prompt: 'Massive cinematic Hollywood trailer impact boom with reverberating brass hit and shattering glass', duration: 8, engine: 'stable_audio_3' },
  { label: '🚀 Sci-Fi Laser Weapon', prompt: 'Futuristic sci-fi laser blast weapon charging up and firing with heavy energy echo', duration: 4, engine: 'audioldm2' },
  { label: '🏎️ V8 Muscle Car', prompt: 'Aggressive V8 muscle car engine revving up and accelerating fast on asphalt', duration: 10, engine: 'stable_audio' },
  { label: '🌌 Deep Space Drone', prompt: 'Dark cinematic atmospheric drone with deep sub bass rumbling in deep space', duration: 20, engine: 'stable_audio' },
  { label: '💥 Trailer Impact Boom', prompt: 'Massive Hollywood movie trailer impact boom with reverberating brass hit', duration: 6, engine: 'audioldm2' },
  { label: '🔥 Campfire Crackle', prompt: 'Cozy fireplace campfire crackling wood embers gently burning in silence', duration: 15, engine: 'stable_audio' },
  { label: '🌊 Ocean Waves', prompt: 'Calm ocean waves crashing gently on a sandy beach during sunset', duration: 16, engine: 'stable_audio' }
];

export default function SoundStudio({ modelsStatus, onOpenModelManager }) {
  const [sfxEngine, setSfxEngine] = useState('audioldm2'); // 'audioldm2' | 'stable_audio' | 'stable_audio_3'
  const [prompt, setPrompt] = useState('Car engine reversing fast followed by sudden loud screeching tires skidding on asphalt');
  const [negativePrompt, setNegativePrompt] = useState('low quality, distortion, harsh, noisy, clipping');
  const [duration, setDuration] = useState(6);
  const [steps, setSteps] = useState(35);
  const [cfgScale, setCfgScale] = useState(4.0);
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
  const [lastEngine, setLastEngine] = useState('audioldm2');
  const [errorMessage, setErrorMessage] = useState('');
  const [history, setHistory] = useState([]);

  const isStableAudioReady = !!modelsStatus?.stable_audio?.installed;
  const isStableAudio3Ready = !!modelsStatus?.stable_audio_3?.installed;
  const isAudioLDMReady = !!modelsStatus?.audioldm2?.installed;
  const isCurrentEngineReady =
    sfxEngine === 'audioldm2'
      ? isAudioLDMReady
      : sfxEngine === 'stable_audio_3'
      ? isStableAudio3Ready
      : isStableAudioReady;

  // Switch default params when engine changes
  const handleSelectEngine = (engine) => {
    setSfxEngine(engine);
    if (engine === 'audioldm2') {
      if (duration > 30) setDuration(15);
      setSteps(35);
      setCfgScale(4.0);
    } else if (engine === 'stable_audio_3') {
      if (duration > 45) setDuration(10);
      setSteps(10);
      setCfgScale(1.2);
    } else {
      setSteps(45);
      setCfgScale(6.0);
    }
  };

  // Progress simulation timer during diffusion
  useEffect(() => {
    let timer = null;
    let stepTimer = null;
    if (isGenerating) {
      setProgressPercent(8);
      setProgressStage(
        sfxEngine === 'audioldm2'
          ? 'Initializing AudioLDM 2 diffusion pipeline on CUDA...'
          : sfxEngine === 'stable_audio_3'
          ? 'Initializing Stable Audio 3 Medium DiT pipeline on CUDA...'
          : 'Initializing Stable Audio Open diffusion pipeline on CUDA...'
      );
      setElapsedSeconds(0);

      timer = setInterval(() => {
        setElapsedSeconds(s => s + 1);
      }, 1000);

      stepTimer = setInterval(() => {
        setProgressPercent(p => {
          if (p < 30) {
            setProgressStage(
              sfxEngine === 'audioldm2'
                ? 'Encoding dual CLAP + T5 narrative text conditioning...'
                : sfxEngine === 'stable_audio_3'
                ? 'Encoding T5 text conditioning with DiT conditioning...'
                : 'Encoding text conditioning with CLAP...'
            );
            return p + 5;
          } else if (p < 85) {
            const currentStep = Math.round((p / 85) * steps);
            setProgressStage(`Denoising audio latents (${currentStep}/${steps} steps)...`);
            return p + 4;
          } else if (p < 95) {
            setProgressStage(
              sfxEngine === 'audioldm2'
                ? `Decoding 16kHz Foley waveform via VAE (${duration}s)...`
                : sfxEngine === 'stable_audio_3'
                ? `Decoding 44.1kHz flagship stereo waveform via DiT Autoencoder (${duration}s)...`
                : `Decoding 44.1kHz stereo waveform via Autoencoder (${duration}s)...`
            );
            return p + 2;
          }
          return p;
        });
      }, 300);
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
  }, [isGenerating, steps, duration, sfxEngine]);

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
    if (preset.engine) {
      handleSelectEngine(preset.engine);
    }
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setErrorMessage('Please enter a description for the sound effect.');
      return;
    }

    if (!isCurrentEngineReady) {
      const engineTitle =
        sfxEngine === 'audioldm2'
          ? 'AudioLDM 2 Studio'
          : sfxEngine === 'stable_audio_3'
          ? 'Stable Audio 3 Medium'
          : 'Stable Audio Open';
      setErrorMessage(`${engineTitle} is not installed. Download it via Model Manager.`);
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
          engine: sfxEngine,
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
      setLastEngine(sfxEngine);

      const newEntry = {
        id: Date.now(),
        title: prompt.length > 40 ? prompt.substring(0, 40) + '...' : prompt,
        url: data.audio_url,
        duration: duration,
        engine: sfxEngine,
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
              Tri-Engine Audio Studio
            </span>
            <span className="text-xs text-slate-500 font-medium">AudioLDM 2, Stable Audio Open &amp; Stable Audio 3 Medium</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Radio className="w-6 h-6 text-purple-600" />
            Sound Studio
          </h2>
        </div>

        {/* Model status pill */}
        <div className="flex items-center gap-2">
          {isCurrentEngineReady ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-semibold">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>
                {sfxEngine === 'audioldm2'
                  ? 'AudioLDM 2 Ready'
                  : sfxEngine === 'stable_audio_3'
                  ? 'Stable Audio 3 Ready'
                  : 'Stable Audio Ready'}
              </span>
            </div>
          ) : (
            <button
              onClick={onOpenModelManager}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-700 text-xs font-semibold hover:bg-amber-100 transition-colors"
            >
              <AlertCircle className="w-4 h-4 text-amber-600" />
              <span>Download in Model Manager</span>
            </button>
          )}
        </div>
      </div>

      {/* Tri-Engine Selector */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Engine 1: AudioLDM 2 */}
        <div
          onClick={() => handleSelectEngine('audioldm2')}
          className={`cursor-pointer rounded-2xl border-2 p-5 transition-all duration-200 select-none ${
            sfxEngine === 'audioldm2'
              ? 'border-indigo-600 bg-indigo-50/70 shadow-md shadow-indigo-100'
              : 'border-slate-200 bg-white hover:border-indigo-300 hover:shadow-xs'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-indigo-100 text-indigo-800 border border-indigo-200">
                AudioLDM 2
              </span>
              <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                Multi-Event Foley
              </span>
            </div>
            {isAudioLDMReady ? (
              <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                Ready
              </span>
            ) : (
              <button
                onClick={(e) => { e.stopPropagation(); onOpenModelManager(); }}
                className="text-[11px] font-bold text-amber-700 bg-amber-50 px-2.5 py-0.5 rounded-full border border-amber-200 hover:bg-amber-100"
              >
                Missing (Download)
              </button>
            )}
          </div>
          <h3 className="text-sm font-bold text-slate-900">Complex Action &amp; Foley Adherence</h3>
          <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
            Dual CLAP + T5 conditioning. Engineered for prompts with multiple actions (e.g. <i>"reversing car screeching tires"</i>). Pristine float32 execution with zero static.
          </p>
          <div className="mt-3 flex items-center gap-4 text-[11px] font-mono text-slate-500">
            <span>• 16kHz Audio</span>
            <span>• Up to 30s</span>
            <span>• Fast Diffusion</span>
          </div>
        </div>

        {/* Engine 2: Stable Audio Open */}
        <div
          onClick={() => handleSelectEngine('stable_audio')}
          className={`cursor-pointer rounded-2xl border-2 p-5 transition-all duration-200 select-none ${
            sfxEngine === 'stable_audio'
              ? 'border-purple-600 bg-purple-50/70 shadow-md shadow-purple-100'
              : 'border-slate-200 bg-white hover:border-purple-300 hover:shadow-xs'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-purple-100 text-purple-800 border border-purple-200">
                Stable Audio Open
              </span>
              <span className="text-[10px] font-bold uppercase tracking-wider text-purple-600 bg-purple-50 px-2 py-0.5 rounded">
                44.1kHz Hi-Fi
              </span>
            </div>
            {isStableAudioReady ? (
              <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                Ready
              </span>
            ) : (
              <button
                onClick={(e) => { e.stopPropagation(); onOpenModelManager(); }}
                className="text-[11px] font-bold text-amber-700 bg-amber-50 px-2.5 py-0.5 rounded-full border border-amber-200 hover:bg-amber-100"
              >
                Missing (Download)
              </button>
            )}
          </div>
          <h3 className="text-sm font-bold text-slate-900">44.1kHz Stereo Ambient Beds</h3>
          <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
            Full bandwidth stereo diffusion by Stability AI. Ideal for long sustained continuous textures (thunderstorm, ocean waves, room tone, space drone) up to 47s.
          </p>
          <div className="mt-3 flex items-center gap-4 text-[11px] font-mono text-slate-500">
            <span>• 44.1kHz Stereo</span>
            <span>• Up to 47s</span>
            <span>• Stability AI</span>
          </div>
        </div>

        {/* Engine 3: Stable Audio 3 Medium */}
        <div
          onClick={() => handleSelectEngine('stable_audio_3')}
          className={`cursor-pointer rounded-2xl border-2 p-5 transition-all duration-200 select-none ${
            sfxEngine === 'stable_audio_3'
              ? 'border-fuchsia-600 bg-fuchsia-50/70 shadow-md shadow-fuchsia-100'
              : 'border-slate-200 bg-white hover:border-fuchsia-300 hover:shadow-xs'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-fuchsia-100 text-fuchsia-800 border border-fuchsia-200">
                Stable Audio 3 Medium
              </span>
              <span className="text-[10px] font-bold uppercase tracking-wider text-fuchsia-600 bg-fuchsia-50 px-2 py-0.5 rounded">
                Flagship DiT
              </span>
            </div>
            {isStableAudio3Ready ? (
              <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                Ready
              </span>
            ) : (
              <button
                onClick={(e) => { e.stopPropagation(); onOpenModelManager(); }}
                className="text-[11px] font-bold text-amber-700 bg-amber-50 px-2.5 py-0.5 rounded-full border border-amber-200 hover:bg-amber-100"
              >
                Missing (Download)
              </button>
            )}
          </div>
          <h3 className="text-sm font-bold text-slate-900">Flagship 2B Studio Sound Design</h3>
          <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
            Stability AI flagship Diffusion Transformer (DiT). Supreme audio fidelity, rich dynamic transients, cinematic impacts, and high-fidelity foley at 44.1kHz.
          </p>
          <div className="mt-3 flex items-center gap-4 text-[11px] font-mono text-slate-500">
            <span>• 44.1kHz Hi-Fi</span>
            <span>• 2B DiT Architecture</span>
            <span>• Gated HF</span>
          </div>
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

          {/* Duration Slider */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className={`w-4 h-4 ${sfxEngine === 'audioldm2' ? 'text-indigo-600' : 'text-purple-600'}`} />
                <span className="text-sm font-bold text-slate-800">Audio Clip Duration</span>
              </div>
              <span className={`font-mono text-lg font-extrabold px-3 py-1 rounded-lg border shadow-2xs ${
                sfxEngine === 'audioldm2'
                  ? 'text-indigo-700 bg-indigo-50 border-indigo-200'
                  : 'text-purple-700 bg-purple-50 border-purple-200'
              }`}>
                {duration}s
              </span>
            </div>
            <input
              type="range"
              min="1"
              max={sfxEngine === 'audioldm2' ? 30 : 47}
              step="1"
              value={duration}
              onChange={(e) => setDuration(parseInt(e.target.value))}
              className={`w-full ${sfxEngine === 'audioldm2' ? 'accent-indigo-600' : 'accent-purple-600'}`}
            />
            <div className="flex justify-between text-[11px] font-mono text-slate-500">
              <span>1s</span>
              <span>{sfxEngine === 'audioldm2' ? '15s' : '24s'}</span>
              <span>{sfxEngine === 'audioldm2' ? '30s (Max)' : '47s (Max)'}</span>
            </div>
          </div>
        </div>

        {/* Right Column: Parameters, Progress Bar, & Visible Output */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-slate-800 flex items-center gap-2">
                <Sliders className={`w-4 h-4 ${sfxEngine === 'audioldm2' ? 'text-indigo-600' : 'text-purple-600'}`} />
                Synthesis Parameters
              </span>
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className={`text-xs font-semibold ${sfxEngine === 'audioldm2' ? 'text-indigo-700 hover:text-indigo-800' : 'text-purple-700 hover:text-purple-800'}`}
              >
                {showAdvanced ? 'Simple' : 'Advanced'}
              </button>
            </div>

            {/* Steps slider */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-slate-700 font-medium">
                <span>Inference Steps</span>
                <span className={`font-mono font-bold ${sfxEngine === 'audioldm2' ? 'text-indigo-700' : 'text-purple-700'}`}>{steps} steps</span>
              </div>
              <input
                type="range"
                min={sfxEngine === 'stable_audio_3' ? "4" : "15"}
                max={sfxEngine === 'stable_audio_3' ? "30" : "100"}
                step={sfxEngine === 'stable_audio_3' ? "1" : "5"}
                value={steps}
                onChange={(e) => setSteps(parseInt(e.target.value))}
                className={`w-full ${sfxEngine === 'audioldm2' ? 'accent-indigo-600' : 'accent-purple-600'}`}
              />
            </div>

            {/* CFG Scale */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-slate-700 font-medium">
                <span>Prompt Guidance (CFG Scale)</span>
                <span className={`font-mono font-bold ${sfxEngine === 'audioldm2' ? 'text-indigo-700' : 'text-purple-700'}`}>{cfgScale.toFixed(1)}</span>
              </div>
              <input
                type="range"
                min="1.0"
                max={sfxEngine === 'stable_audio_3' ? "5.0" : "15.0"}
                step="0.1"
                value={cfgScale}
                onChange={(e) => setCfgScale(parseFloat(e.target.value))}
                className={`w-full ${sfxEngine === 'audioldm2' ? 'accent-indigo-600' : 'accent-purple-600'}`}
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
                      <Hash className={`w-3.5 h-3.5 ${sfxEngine === 'audioldm2' ? 'text-indigo-600' : 'text-purple-600'}`} />
                      Seed (-1 for random)
                    </span>
                    <button
                      onClick={() => setSeed(Math.floor(Math.random() * 999999))}
                      className={`text-[11px] hover:underline ${sfxEngine === 'audioldm2' ? 'text-indigo-600' : 'text-purple-600'}`}
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

            {/* PROGRESS BAR */}
            {isGenerating && (
              <div className={`space-y-2 pt-2 p-4 bg-slate-50 rounded-xl border animate-fadeIn ${
                sfxEngine === 'audioldm2' ? 'border-indigo-100' : 'border-purple-100'
              }`}>
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-800 flex items-center gap-1.5">
                    <Activity className={`w-3.5 h-3.5 animate-pulse ${sfxEngine === 'audioldm2' ? 'text-indigo-600' : 'text-purple-600'}`} />
                    {progressStage}
                  </span>
                  <span className={`font-mono font-bold ${sfxEngine === 'audioldm2' ? 'text-indigo-700' : 'text-purple-700'}`}>
                    {progressPercent}% ({elapsedSeconds}s)
                  </span>
                </div>
                {/* Progress bar track */}
                <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden shadow-inner">
                  <div
                    className={`h-full rounded-full transition-all duration-300 shadow-sm ${
                      sfxEngine === 'audioldm2'
                        ? 'bg-gradient-to-r from-indigo-500 via-blue-500 to-cyan-500'
                        : 'bg-gradient-to-r from-purple-500 via-indigo-500 to-cyan-500'
                    }`}
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>
            )}

            {/* Generate Action Button */}
            <button
              onClick={handleGenerate}
              disabled={isGenerating || !prompt.trim() || !isCurrentEngineReady}
              className={`w-full py-4 px-6 rounded-xl font-bold text-sm flex items-center justify-center gap-2.5 shadow-md transition-all duration-200 ${
                isGenerating
                  ? 'bg-slate-200 text-slate-400 cursor-not-allowed border border-slate-300'
                  : !isCurrentEngineReady
                  ? 'bg-amber-100 text-amber-800 cursor-not-allowed border border-amber-300'
                  : sfxEngine === 'audioldm2'
                  ? 'bg-gradient-to-r from-indigo-600 via-blue-600 to-cyan-600 text-white hover:brightness-105 active:scale-[0.99] shadow-indigo-600/20'
                  : 'bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-600 text-white hover:brightness-105 active:scale-[0.99] shadow-purple-600/20'
              }`}
            >
              {isGenerating ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin text-white" />
                  <span>Synthesizing Sound ({progressPercent}%)...</span>
                </>
              ) : !isCurrentEngineReady ? (
                <>
                  <AlertCircle className="w-5 h-5 text-amber-700" />
                  <span>{sfxEngine === 'audioldm2' ? 'AudioLDM 2' : 'Stable Audio'} Not Installed (Download in Manager)</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  <span>Generate Sound ({sfxEngine === 'audioldm2' ? 'AudioLDM 2 Multi-Event' : 'Stable Audio 44.1kHz'})</span>
                </>
              )}
            </button>
          </div>

          {/* Generated Waveform Player (Visible Results) */}
          {generatedAudioUrl ? (
            <div className="space-y-2">
              <AudioPlayer
                audioUrl={generatedAudioUrl}
                title={lastEngine === 'audioldm2' ? 'AudioLDM 2 Studio (Multi-Event SFX)' : 'Stable Audio Open (44.1kHz Hi-Fi)'}
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
