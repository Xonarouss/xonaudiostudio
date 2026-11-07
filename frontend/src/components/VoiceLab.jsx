import React, { useState, useRef } from 'react';
import { Mic, Upload, Sparkles, Volume2, Music, CheckCircle2, AlertCircle, RefreshCw, Sliders, History } from 'lucide-react';
import AudioPlayer from './AudioPlayer';

export default function VoiceLab({ modelsStatus, onOpenModelManager }) {
  const [text, setText] = useState('Welkom bij de nieuwe AI Audio Studio. Deze stem is gegenereerd met de F5-TTS architectuur op een Nvidia RTX 5080.');
  const [refAudioFile, setRefAudioFile] = useState(null);
  const [refAudioName, setRefAudioName] = useState('');
  const [refText, setRefText] = useState('');
  const [speed, setSpeed] = useState(1.0);
  const [nfeSteps, setNfeSteps] = useState(32);
  const [removeSilence, setRemoveSilence] = useState(true);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedAudioUrl, setGeneratedAudioUrl] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [history, setHistory] = useState([]);

  const fileInputRef = useRef(null);

  const isF5Ready = modelsStatus?.f5_tts?.installed;

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith('audio/')) {
        setErrorMessage('Selecteer een geldig audiobestand (.wav, .mp3, etc.)');
        return;
      }
      setRefAudioFile(file);
      setRefAudioName(file.name);
      setErrorMessage('');
    }
  };

  const handleGenerate = async () => {
    if (!text.trim()) {
      setErrorMessage('Vul een tekst in om uit te spreken.');
      return;
    }

    if (!isF5Ready) {
      setErrorMessage('Het F5-TTS model is nog niet gedownload. Download het via Model Manager.');
      return;
    }

    setIsGenerating(true);
    setErrorMessage('');

    try {
      const formData = new FormData();
      formData.append('gen_text', text);
      if (refAudioFile) {
        formData.append('ref_audio', refAudioFile);
      }
      formData.append('ref_text', refText);
      formData.append('speed', speed.toString());
      formData.append('nfe_steps', nfeSteps.toString());
      formData.append('remove_silence', removeSilence.toString());

      const res = await fetch('/api/tts/generate', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Generatiefout' }));
        throw new Error(err.detail || 'Fout bij stemgeneratie');
      }

      const data = await res.json();
      const fullUrl = data.audio_url;
      setGeneratedAudioUrl(fullUrl);

      // Add to history
      const newEntry = {
        id: Date.now(),
        title: text.length > 40 ? text.substring(0, 40) + '...' : text,
        url: fullUrl,
        timestamp: new Date().toLocaleTimeString(),
        speed: speed,
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
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
              F5-TTS v1
            </span>
            <span className="text-xs text-slate-400">Zero-Shot Voice Cloning & High-Fidelity Speech</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Mic className="w-6 h-6 text-cyan-400" />
            Voice Lab
          </h2>
        </div>

        {/* Model status pill */}
        <div className="flex items-center gap-2">
          {isF5Ready ? (
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
        {/* Left Column: Prompt and Reference Voice */}
        <div className="lg:col-span-7 space-y-6">
          {/* Target Text Input */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <span>Tekst om te genereren</span>
              </label>
              <span className="text-xs font-mono text-slate-400">{text.length} karakters</span>
            </div>
            <textarea
              rows={5}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Voer de gewenste tekst in (Nederlands, Engels, meertalig)..."
              className="w-full rounded-xl p-4 text-sm glass-input text-slate-100 placeholder-slate-500 resize-none font-sans leading-relaxed"
            />
          </div>

          {/* Reference Voice Cloning Section */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <Upload className="w-4 h-4 text-purple-400" />
                  Referentiestem (Voice Cloning)
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Upload een heldere audio-opname van 5-10 seconden voor zero-shot stemkloons.
                </p>
              </div>
              {refAudioFile && (
                <button
                  onClick={() => {
                    setRefAudioFile(null);
                    setRefAudioName('');
                    setRefText('');
                    if (fileInputRef.current) fileInputRef.current.value = '';
                  }}
                  className="text-xs text-slate-400 hover:text-rose-400 underline"
                >
                  Verwijderen
                </button>
              )}
            </div>

            {/* Upload Drag & Drop Area */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept="audio/*"
              className="hidden"
            />

            <div
              onClick={() => fileInputRef.current?.click()}
              className={`p-6 rounded-xl border-2 border-dashed cursor-pointer transition-all flex flex-col items-center justify-center gap-2 ${
                refAudioFile
                  ? 'border-purple-500/50 bg-purple-500/10'
                  : 'border-slate-700 hover:border-cyan-500/50 hover:bg-studio-900/60'
              }`}
            >
              <div className="w-12 h-12 rounded-full bg-studio-900 flex items-center justify-center text-cyan-400 border border-slate-700 shadow-inner">
                {refAudioFile ? <CheckCircle2 className="w-6 h-6 text-purple-400" /> : <Upload className="w-6 h-6" />}
              </div>
              <p className="text-sm font-medium text-slate-200 text-center">
                {refAudioName ? refAudioName : 'Klik om referentie-audio te kiezen of sleep hierheen'}
              </p>
              <span className="text-xs text-slate-400 font-mono">
                {refAudioFile ? `${(refAudioFile.size / 1024 / 1024).toFixed(2)} MB` : 'WAV, MP3, FLAC, M4A (5-10 sec ideaal)'}
              </span>
            </div>

            {/* Reference Audio Transcript (Crucial for F5-TTS) */}
            {refAudioFile && (
              <div className="space-y-1.5 pt-2">
                <label className="text-xs font-medium text-slate-300">
                  Referentietekst (Wat zegt de stem in het audiofragment?):
                </label>
                <input
                  type="text"
                  value={refText}
                  onChange={(e) => setRefText(e.target.value)}
                  placeholder="Bijv. 'Hallo, dit is een voorbeeldopname voor stemkloonen.'"
                  className="w-full px-3.5 py-2.5 text-xs rounded-lg glass-input text-slate-100 placeholder-slate-500"
                />
                <p className="text-[11px] text-slate-400">
                  Tip: Een nauwkeurige referentietekst zorgt voor de hoogste kloongelijkenis en minste artefacten.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Audio Output & Controls */}
        <div className="lg:col-span-5 space-y-6">
          {/* Controls & Generate Button */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-5">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Sliders className="w-4 h-4 text-cyan-400" />
                Parameters
              </span>
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="text-xs text-cyan-400 hover:text-cyan-300 font-medium"
              >
                {showAdvanced ? 'Minder opties' : 'Geavanceerd'}
              </button>
            </div>

            {/* Speed slider */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-slate-300 font-medium">
                <span>Spreeksnelheid</span>
                <span className="font-mono text-cyan-400">{speed.toFixed(2)}x</span>
              </div>
              <input
                type="range"
                min="0.6"
                max="1.6"
                step="0.05"
                value={speed}
                onChange={(e) => setSpeed(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>

            {showAdvanced && (
              <div className="space-y-4 pt-3 border-t border-slate-800 animate-fadeIn">
                <div className="space-y-2">
                  <div className="flex justify-between text-xs text-slate-300 font-medium">
                    <span>NFE Steps (Sampling Kwaliteit)</span>
                    <span className="font-mono text-cyan-400">{nfeSteps} steps</span>
                  </div>
                  <input
                    type="range"
                    min="16"
                    max="64"
                    step="4"
                    value={nfeSteps}
                    onChange={(e) => setNfeSteps(parseInt(e.target.value))}
                    className="w-full"
                  />
                  <p className="text-[11px] text-slate-400">
                    32 steps is optimaal voor RTX 5080 (bliksemsnel &amp; kraakhelder).
                  </p>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-300 font-medium">Stilte automatisch trimmen</span>
                  <input
                    type="checkbox"
                    checked={removeSilence}
                    onChange={(e) => setRemoveSilence(e.target.checked)}
                    className="w-4 h-4 rounded text-cyan-500 focus:ring-cyan-400 bg-studio-900 border-slate-700"
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
                  : 'bg-gradient-to-r from-cyan-500 via-blue-600 to-purple-600 text-white shadow-glow-cyan hover:brightness-110 active:scale-[0.99]'
              }`}
            >
              {isGenerating ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin text-cyan-400" />
                  <span>Genereren op RTX 5080...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  <span>Genereer Stem (F5-TTS)</span>
                </>
              )}
            </button>
          </div>

          {/* Generated Waveform Player */}
          {generatedAudioUrl ? (
            <div className="space-y-2">
              <AudioPlayer audioUrl={generatedAudioUrl} title="F5-TTS Gegenereerde Stem" />
            </div>
          ) : (
            <div className="glass-panel p-8 rounded-2xl border border-slate-800/80 text-center flex flex-col items-center justify-center gap-3">
              <div className="w-14 h-14 rounded-2xl bg-studio-900/80 border border-slate-800 flex items-center justify-center text-slate-500">
                <Volume2 className="w-7 h-7" />
              </div>
              <p className="text-sm font-medium text-slate-300">Geen audio gegenereerd</p>
              <p className="text-xs text-slate-500 max-w-xs">
                Klik hierboven op [Genereer Stem] om de audio via F5-TTS te synthetiseren.
              </p>
            </div>
          )}

          {/* History List */}
          {history.length > 0 && (
            <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-3">
              <h4 className="text-xs font-semibold text-slate-300 flex items-center gap-2 uppercase tracking-wider">
                <History className="w-3.5 h-3.5 text-cyan-400" />
                Recente Generaties
              </h4>
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {history.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => setGeneratedAudioUrl(item.url)}
                    className="p-2.5 rounded-lg bg-studio-950/70 hover:bg-studio-900 border border-slate-800/80 cursor-pointer flex items-center justify-between gap-2 text-xs transition-colors"
                  >
                    <span className="truncate text-slate-300 font-medium">{item.title}</span>
                    <span className="text-[10px] text-slate-400 font-mono flex-shrink-0">{item.timestamp}</span>
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

