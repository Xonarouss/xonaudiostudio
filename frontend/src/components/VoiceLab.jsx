import React, { useState, useRef, useEffect } from 'react';
import { Mic, Upload, Sparkles, Volume2, Music, CheckCircle2, AlertCircle, RefreshCw, Sliders, History, Play, Activity } from 'lucide-react';
import AudioPlayer from './AudioPlayer';

export default function VoiceLab({ modelsStatus, onOpenModelManager }) {
  const [text, setText] = useState('Welcome to XonAudio Studio. This voice is generated locally with the F5-TTS architecture on your GPU.');
  const [refAudioFile, setRefAudioFile] = useState(null);
  const [refAudioName, setRefAudioName] = useState('');
  const [refText, setRefText] = useState('');
  const [speed, setSpeed] = useState(1.0);
  const [nfeSteps, setNfeSteps] = useState(32);
  const [removeSilence, setRemoveSilence] = useState(true);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Generation & Progress states
  const [isGenerating, setIsGenerating] = useState(false);
  const [progressPercent, setProgressPercent] = useState(0);
  const [progressStage, setProgressStage] = useState('');
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [generatedAudioUrl, setGeneratedAudioUrl] = useState(null);
  const [lastGenText, setLastGenText] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [history, setHistory] = useState([]);

  const fileInputRef = useRef(null);
  const isF5Ready = modelsStatus?.f5_tts?.installed;

  // Progress simulation timer during generation
  useEffect(() => {
    let timer = null;
    let stepTimer = null;
    if (isGenerating) {
      setProgressPercent(10);
      setProgressStage('Preparing reference voice & loading F5-TTS weights...');
      setElapsedSeconds(0);

      timer = setInterval(() => {
        setElapsedSeconds(s => s + 1);
      }, 1000);

      stepTimer = setInterval(() => {
        setProgressPercent(p => {
          if (p < 35) {
            setProgressStage('Computing flow-matching voice conditioning...');
            return p + 6;
          } else if (p < 75) {
            setProgressStage(`Running ODE neural diffusion steps (${nfeSteps} steps)...`);
            return p + 4;
          } else if (p < 92) {
            setProgressStage('Vocoder synthesis & silence trimming...');
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
  }, [isGenerating, nfeSteps]);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith('audio/')) {
        setErrorMessage('Please select a valid audio file (.wav, .mp3, .flac, etc.)');
        return;
      }
      setRefAudioFile(file);
      setRefAudioName(file.name);
      setErrorMessage('');
    }
  };

  const handleGenerate = async () => {
    if (!text.trim()) {
      setErrorMessage('Please enter the text you want the voice to speak.');
      return;
    }

    if (!isF5Ready) {
      setErrorMessage('F5-TTS model checkpoint is missing. Please download it via the Model Manager.');
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
        const err = await res.json().catch(() => ({ detail: 'Generation error' }));
        throw new Error(err.detail || 'Voice generation failed');
      }

      const data = await res.json();
      setProgressPercent(100);
      setProgressStage('Voice rendered successfully!');
      setGeneratedAudioUrl(data.audio_url);
      setLastGenText(text);

      // Add to session history
      const newEntry = {
        id: Date.now(),
        title: text.length > 45 ? text.substring(0, 45) + '...' : text,
        url: data.audio_url,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        speed: speed,
      };
      setHistory(prev => [newEntry, ...prev.slice(0, 9)]);
    } catch (err) {
      setErrorMessage(err.message || 'An error occurred during voice synthesis.');
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
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-cyan-100 text-cyan-800 border border-cyan-200">
              F5-TTS v1
            </span>
            <span className="text-xs text-slate-500 font-medium">Zero-Shot Voice Cloning &amp; High-Fidelity Neural Speech</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Mic className="w-6 h-6 text-cyan-600" />
            Voice Lab
          </h2>
        </div>

        {/* Model status pill */}
        <div className="flex items-center gap-2">
          {isF5Ready ? (
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
        {/* Left Column: Script and Reference Voice */}
        <div className="lg:col-span-7 space-y-6">
          {/* Target Text Input */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-bold text-slate-800">
                Text to Speak
              </label>
              <span className="text-xs font-mono text-slate-500">{text.length} characters</span>
            </div>
            <textarea
              rows={5}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Enter speech script here (multilingual support)..."
              className="w-full rounded-xl p-4 text-sm glass-input text-slate-900 placeholder-slate-400 resize-none font-sans leading-relaxed shadow-xs"
            />
          </div>

          {/* Reference Voice Cloning Section */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                  <Upload className="w-4 h-4 text-purple-600" />
                  Reference Voice (Zero-Shot Cloning)
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Upload a 5–10 second clean audio clip of the target speaker's voice.
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
                  className="text-xs text-slate-500 hover:text-rose-600 underline font-medium"
                >
                  Remove
                </button>
              )}
            </div>

            {/* Upload Area */}
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
                  ? 'border-purple-400 bg-purple-50/60'
                  : 'border-slate-300 hover:border-cyan-500 hover:bg-slate-50'
              }`}
            >
              <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-cyan-600 border border-slate-200 shadow-xs">
                {refAudioFile ? <CheckCircle2 className="w-6 h-6 text-purple-600" /> : <Upload className="w-6 h-6" />}
              </div>
              <p className="text-sm font-semibold text-slate-800 text-center">
                {refAudioName ? refAudioName : 'Click to select reference audio or drag & drop'}
              </p>
              <span className="text-xs text-slate-500 font-mono">
                {refAudioFile ? `${(refAudioFile.size / 1024 / 1024).toFixed(2)} MB` : 'WAV, MP3, FLAC, M4A (5–10 sec recommended)'}
              </span>
            </div>

            {/* Reference Audio Transcript */}
            {refAudioFile && (
              <div className="space-y-1.5 pt-2 animate-fadeIn">
                <label className="text-xs font-semibold text-slate-700">
                  Reference Transcript (What does the voice say in the recording?):
                </label>
                <input
                  type="text"
                  value={refText}
                  onChange={(e) => setRefText(e.target.value)}
                  placeholder="e.g. 'Hello, this is a sample recording for voice cloning.'"
                  className="w-full px-3.5 py-2.5 text-xs rounded-lg glass-input text-slate-900 placeholder-slate-400 shadow-xs"
                />
                <p className="text-[11px] text-slate-500">
                  Tip: A matching reference transcript ensures the highest clone fidelity and zero pronunciation artifacts.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Parameters, Progress Bar, & Visible Output */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-slate-800 flex items-center gap-2">
                <Sliders className="w-4 h-4 text-cyan-600" />
                Parameters
              </span>
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="text-xs text-cyan-700 hover:text-cyan-800 font-semibold"
              >
                {showAdvanced ? 'Simple' : 'Advanced'}
              </button>
            </div>

            {/* Speed slider */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-slate-700 font-medium">
                <span>Speaking Rate</span>
                <span className="font-mono text-cyan-700 font-bold">{speed.toFixed(2)}x</span>
              </div>
              <input
                type="range"
                min="0.6"
                max="1.6"
                step="0.05"
                value={speed}
                onChange={(e) => setSpeed(parseFloat(e.target.value))}
                className="w-full accent-cyan-600"
              />
            </div>

            {showAdvanced && (
              <div className="space-y-4 pt-3 border-t border-slate-100 animate-fadeIn">
                <div className="space-y-2">
                  <div className="flex justify-between text-xs text-slate-700 font-medium">
                    <span>NFE Steps (Sampling Quality)</span>
                    <span className="font-mono text-cyan-700 font-bold">{nfeSteps} steps</span>
                  </div>
                  <input
                    type="range"
                    min="16"
                    max="64"
                    step="4"
                    value={nfeSteps}
                    onChange={(e) => setNfeSteps(parseInt(e.target.value))}
                    className="w-full accent-cyan-600"
                  />
                  <p className="text-[11px] text-slate-500">
                    32 steps is optimal for high speed and natural flow.
                  </p>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-700 font-medium">Auto-trim silence</span>
                  <input
                    type="checkbox"
                    checked={removeSilence}
                    onChange={(e) => setRemoveSilence(e.target.checked)}
                    className="w-4 h-4 rounded text-cyan-600 focus:ring-cyan-500 border-slate-300"
                  />
                </div>
              </div>
            )}

            {/* BEAUTIFUL VISIBLE PROGRESS BAR */}
            {isGenerating && (
              <div className="space-y-2 pt-2 p-4 bg-slate-50 rounded-xl border border-cyan-100 animate-fadeIn">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-800 flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-cyan-600 animate-pulse" />
                    {progressStage}
                  </span>
                  <span className="font-mono font-bold text-cyan-700">{progressPercent}% ({elapsedSeconds}s)</span>
                </div>
                {/* Progress bar track */}
                <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden shadow-inner">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500 transition-all duration-300 shadow-sm"
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
                  : 'bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 text-white hover:brightness-105 active:scale-[0.99] shadow-cyan-600/20'
              }`}
            >
              {isGenerating ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin text-cyan-600" />
                  <span>Synthesizing Voice ({progressPercent}%)...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  <span>Generate Voice (F5-TTS)</span>
                </>
              )}
            </button>
          </div>

          {/* Generated Waveform Player (Visible Results) */}
          {generatedAudioUrl ? (
            <div className="space-y-2">
              <AudioPlayer
                audioUrl={generatedAudioUrl}
                title="F5-TTS Voice Synthesis"
                subtitle={lastGenText.length > 50 ? lastGenText.substring(0, 50) + '...' : lastGenText}
              />
            </div>
          ) : (
            <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center flex flex-col items-center justify-center gap-3 shadow-xs">
              <div className="w-14 h-14 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-400">
                <Volume2 className="w-7 h-7" />
              </div>
              <p className="text-sm font-bold text-slate-800">No voice generated yet</p>
              <p className="text-xs text-slate-500 max-w-xs">
                Click [Generate Voice] to synthesize speech. The result waveform and direct WAV download will appear here immediately.
              </p>
            </div>
          )}

          {/* History Gallery */}
          {history.length > 0 && (
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
              <h4 className="text-xs font-bold text-slate-800 flex items-center gap-2 uppercase tracking-wider">
                <History className="w-3.5 h-3.5 text-cyan-600" />
                Recent Voice Clips ({history.length})
              </h4>
              <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
                {history.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => {
                      setGeneratedAudioUrl(item.url);
                      setLastGenText(item.title);
                    }}
                    className={`p-2.5 rounded-lg border cursor-pointer flex items-center justify-between gap-2 text-xs transition-colors ${
                      generatedAudioUrl === item.url
                        ? 'bg-cyan-50 border-cyan-300 text-cyan-900 font-semibold'
                        : 'bg-slate-50 hover:bg-slate-100 border-slate-200 text-slate-700'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <Play className="w-3 h-3 text-cyan-600 flex-shrink-0" />
                      <span className="truncate">{item.title}</span>
                    </div>
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
