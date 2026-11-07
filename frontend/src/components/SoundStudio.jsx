import React, { useState } from 'react';
import { Radio, Sparkles, Volume2, Sliders, RefreshCw, CheckCircle2, AlertCircle, History, Clock, Hash } from 'lucide-react';
import AudioPlayer from './AudioPlayer';

const PRESET_PROMPTS = [
  { label: '🌩️ Donder & Regen', prompt: 'Cinematic thunder strike in distance with gentle rain pouring on asphalt', duration: 12 },
  { label: '🚀 Sci-Fi Laser', prompt: 'Futuristic sci-fi laser blast weapon charging up and firing with echo', duration: 4 },
  { label: '👣 Voetstappen Gravel', prompt: 'Heavy boots walking slowly on loose gravel path outdoors', duration: 8 },
  { label: '🏎️ V8 Sportwagen', prompt: 'Aggressive V8 muscle car engine revving and accelerating fast down the highway', duration: 10 },
  { label: '🌌 Diepe Drone', prompt: 'Dark cinematic atmospheric drone with deep sub bass rumbling in deep space', duration: 20 },
  { label: '💥 Filmische Impact', prompt: 'Massive Hollywood movie trailer impact boom with reverberating brass hit', duration: 6 },
  { label: '🔥 Knapperend Vuur', prompt: 'Cozy fireplace campfire crackling wood embers gently burning', duration: 15 },
];

export default function SoundStudio({ modelsStatus, onOpenModelManager }) {
  const [prompt, setPrompt] = useState('Cinematic massive explosion followed by falling debris and reverberation');
  const [negativePrompt, setNegativePrompt] = useState('low quality, distortion, harsh, noisy, speech, human voice');
  const [duration, setDuration] = useState(10);
  const [steps, setSteps] = useState(50);
  const [cfgScale, setCfgScale] = useState(7.0);
  const [seed, setSeed] = useState(-1); // -1 = random
  const [showAdvanced, setShowAdvanced] = useState(false);

  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedAudioUrl, setGeneratedAudioUrl] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [history, setHistory] = useState([]);

  const isModelReady = modelsStatus?.stable_audio?.installed;

  const handleApplyPreset = (preset) => {
    setPrompt(preset.prompt);
    setDuration(preset.duration);
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setErrorMessage('Vul een omschrijving in voor het gewenste geluidseffect.');
      return;
    }

    if (!isModelReady) {
      setErrorMessage('Het Stable Audio Open model is nog niet gedownload. Download het via Model Manager.');
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
        const err = await res.json().catch(() => ({ detail: 'Generatiefout' }));
        throw new Error(err.detail || 'Fout bij genereren van sound effect.');
      }

      const data = await res.json();
      setGeneratedAudioUrl(data.audio_url);

      const newEntry = {
        id: Date.now(),
        title: prompt.length > 35 ? prompt.substring(0, 35) + '...' : prompt,
        url: data.audio_url,
        duration: duration,
        timestamp: new Date().toLocaleTimeString(),
      };
      setHistory(prev => [newEntry, ...prev.slice(0, 7)]);
    } catch (err) {
      setErrorMessage(err.message || 'Er is een fout opgetreden.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 glass-panel rounded-2xl border border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30">
              Stable Audio Open 1.0
            </span>
            <span className="text-xs text-slate-400">High-Resolution 44.1kHz Foley &amp; Sound Effects (Tot 47s)</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Radio className="w-6 h-6 text-purple-400" />
            Sound Studio
          </h2>
        </div>

        {/* Model status pill */}
        <div className="flex items-center gap-2">
          {isModelReady ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-medium">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Model Actief &amp; Geladen</span>
            </div>
          ) : (
            <button
              onClick={onOpenModelManager}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium hover:bg-amber-500/20 transition-colors"
            >
              <AlertCircle className="w-4 h-4 text-amber-400" />
              <span>Model niet geïnstalleerd (Klik om te downloaden)</span>
            </button>
          )}
        </div>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button
            onClick={() => setErrorMessage('')}
            className="text-xs font-semibold text-rose-400 hover:text-rose-200"
          >
            Sluiten
          </button>
        </div>
      )}

      {/* Main Studio Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Prompting & Presets */}
        <div className="lg:col-span-7 space-y-6">
          {/* Preset Buttons */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-2.5">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Snelle Voorbeelden / Presets:</span>
            <div className="flex flex-wrap gap-2">
              {PRESET_PROMPTS.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handleApplyPreset(p)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium bg-studio-900 hover:bg-studio-800 text-slate-300 border border-slate-700/80 hover:border-purple-500/50 hover:text-white transition-all active:scale-95"
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Sound Prompt Input */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-semibold text-slate-200">
                Geluidsbeschrijving (Prompt)
              </label>
              <span className="text-xs font-mono text-slate-400">{prompt.length} tekens</span>
            </div>
            <textarea
              rows={4}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Beschrijf het gewenste geluid zo gedetailleerd mogelijk in het Engels (bijv. Cinematic sub bass impact, rain on a tent, futuristic ui clicks)..."
              className="w-full rounded-xl p-4 text-sm glass-input text-slate-100 placeholder-slate-500 resize-none font-sans leading-relaxed"
            />
            <p className="text-[11px] text-slate-400">
              Tip: Stable Audio Open reageert het krachtigst op beschrijvende Engelse termen inclusief akoestiek (bijv. "reverb", "close-up", "outdoor").
            </p>
          </div>

          {/* Duration Slider (1 to 47 seconds) */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-purple-400" />
                <span className="text-sm font-semibold text-slate-200">Duur van het Geluidseffect</span>
              </div>
              <span className="font-mono text-lg font-bold text-purple-400 bg-studio-950 px-3 py-1 rounded-lg border border-purple-500/30">
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
              className="w-full accent-purple-500"
            />
            <div className="flex justify-between text-[11px] font-mono text-slate-400">
              <span>1 seconde</span>
              <span>24 seconden</span>
              <span>47 seconden (Maximum)</span>
            </div>
          </div>
        </div>

        {/* Right Column: Parameters & Generate */}
        <div className="lg:col-span-5 space-y-6">
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-5">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Sliders className="w-4 h-4 text-purple-400" />
                Synthese Parameters
              </span>
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="text-xs text-purple-400 hover:text-purple-300 font-medium"
              >
                {showAdvanced ? 'Minder opties' : 'Geavanceerd'}
              </button>
            </div>

            {/* Steps slider */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-slate-300 font-medium">
                <span>Inference Steps</span>
                <span className="font-mono text-purple-400">{steps} stappen</span>
              </div>
              <input
                type="range"
                min="25"
                max="100"
                step="5"
                value={steps}
                onChange={(e) => setSteps(parseInt(e.target.value))}
                className="w-full accent-purple-500"
              />
            </div>

            {/* CFG Scale */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-slate-300 font-medium">
                <span>Prompt Kracht (CFG Scale)</span>
                <span className="font-mono text-purple-400">{cfgScale.toFixed(1)}</span>
              </div>
              <input
                type="range"
                min="1.0"
                max="15.0"
                step="0.5"
                value={cfgScale}
                onChange={(e) => setCfgScale(parseFloat(e.target.value))}
                className="w-full accent-purple-500"
              />
            </div>

            {showAdvanced && (
              <div className="space-y-4 pt-3 border-t border-slate-800 animate-fadeIn">
                <div className="space-y-1.5">
                  <label className="text-xs text-slate-300 font-medium">Negatieve Prompt:</label>
                  <input
                    type="text"
                    value={negativePrompt}
                    onChange={(e) => setNegativePrompt(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-lg glass-input text-slate-200"
                  />
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs text-slate-300 font-medium">
                    <span className="flex items-center gap-1">
                      <Hash className="w-3.5 h-3.5 text-purple-400" />
                      Seed (-1 voor willekeurig)
                    </span>
                    <button
                      onClick={() => setSeed(Math.floor(Math.random() * 999999))}
                      className="text-[11px] text-purple-400 hover:underline"
                    >
                      Genereer Seed
                    </button>
                  </div>
                  <input
                    type="number"
                    value={seed}
                    onChange={(e) => setSeed(parseInt(e.target.value) || -1)}
                    className="w-full px-3 py-2 text-xs rounded-lg glass-input text-slate-200 font-mono"
                  />
                </div>
              </div>
            )}

            {/* Generate Action Button */}
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className={`w-full py-4 px-6 rounded-xl font-semibold text-sm flex items-center justify-center gap-2.5 shadow-lg transition-all duration-200 ${
                isGenerating
                  ? 'bg-studio-800 text-slate-400 cursor-not-allowed border border-slate-700'
                  : 'bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-500 text-white shadow-glow-purple hover:brightness-110 active:scale-[0.99]'
              }`}
            >
              {isGenerating ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin text-purple-300" />
                  <span>Synthetiseren op RTX 5080 ({duration}s)...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  <span>Genereer Sound Effect</span>
                </>
              )}
            </button>
          </div>

          {/* Generated Waveform Player */}
          {generatedAudioUrl ? (
            <div className="space-y-2">
              <AudioPlayer audioUrl={generatedAudioUrl} title="Stable Audio Open Effect" />
            </div>
          ) : (
            <div className="glass-panel p-8 rounded-2xl border border-slate-800/80 text-center flex flex-col items-center justify-center gap-3">
              <div className="w-14 h-14 rounded-2xl bg-studio-900/80 border border-slate-800 flex items-center justify-center text-slate-500">
                <Volume2 className="w-7 h-7" />
              </div>
              <p className="text-sm font-medium text-slate-300">Geen geluidseffect gegenereerd</p>
              <p className="text-xs text-slate-500 max-w-xs">
                Kies een preset of typ een prompt en klik op [Genereer Sound Effect].
              </p>
            </div>
          )}

          {/* History List */}
          {history.length > 0 && (
            <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-3">
              <h4 className="text-xs font-semibold text-slate-300 flex items-center gap-2 uppercase tracking-wider">
                <History className="w-3.5 h-3.5 text-purple-400" />
                Recente Foley / Effecten
              </h4>
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {history.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => setGeneratedAudioUrl(item.url)}
                    className="p-2.5 rounded-lg bg-studio-950/70 hover:bg-studio-900 border border-slate-800/80 cursor-pointer flex items-center justify-between gap-2 text-xs transition-colors"
                  >
                    <span className="truncate text-slate-300 font-medium">{item.title}</span>
                    <span className="text-[10px] text-purple-400 font-mono flex-shrink-0">{item.duration}s</span>
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

