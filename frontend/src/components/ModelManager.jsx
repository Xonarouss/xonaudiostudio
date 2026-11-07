import React, { useState } from 'react';
import {
  HardDrive,
  Trash2,
  Download,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Cpu,
  Layers,
  Database,
  ArrowDownCircle,
  ShieldAlert,
  Server,
  Key,
  ExternalLink
} from 'lucide-react';

export default function ModelManager({
  modelsStatus,
  systemInfo,
  onRefresh,
  isLoading
}) {
  const [downloadingModel, setDownloadingModel] = useState(null);
  const [deletingModel, setDeletingModel] = useState(null);
  const [message, setMessage] = useState({ text: '', type: '' });
  const [hfToken, setHfToken] = useState('');
  const [savingToken, setSavingToken] = useState(false);

  const handleSaveHFToken = async () => {
    if (!hfToken.trim()) return;
    setSavingToken(true);
    try {
      const res = await fetch('/api/settings/hf_token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: hfToken.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to save token');
      setMessage({ text: data.message, type: 'success' });
      setHfToken('');
    } catch (err) {
      setMessage({ text: err.message, type: 'error' });
    } finally {
      setSavingToken(false);
    }
  };

  const handleDownload = async (modelKey) => {
    setDownloadingModel(modelKey);
    setMessage({ text: `Downloading ${modelKey}... This might take a few moments depending on your network connection.`, type: 'info' });

    try {
      const res = await fetch(`/api/models/download/${modelKey}`, {
        method: 'POST',
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Download error');
      }
      setMessage({ text: `${data.message || 'Model downloaded successfully!'}`, type: 'success' });
      await onRefresh();
    } catch (err) {
      setMessage({ text: err.message || 'Download failed.', type: 'error' });
    } finally {
      setDownloadingModel(null);
    }
  };

  const handleDelete = async (modelKey) => {
    const confirmText = modelKey === 'all'
      ? 'Are you sure you want to delete ALL models to free up storage space?'
      : `Are you sure you want to delete the ${modelKey} checkpoint from your drive?`;

    if (!window.confirm(confirmText)) return;

    setDeletingModel(modelKey);
    setMessage({ text: 'Removing model files from disk...', type: 'info' });

    try {
      const res = await fetch('/api/models/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_key: modelKey }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to delete model files');
      }
      setMessage({ text: data.message || 'Files deleted successfully.', type: 'success' });
      await onRefresh();
    } catch (err) {
      setMessage({ text: err.message || 'Deletion failed.', type: 'error' });
    } finally {
      setDeletingModel(null);
    }
  };

  const handleUnloadVRAM = async () => {
    try {
      const res = await fetch('/api/models/unload', { method: 'POST' });
      const data = await res.json();
      setMessage({ text: data.message || 'GPU VRAM cleared successfully!', type: 'success' });
      await onRefresh();
    } catch (err) {
      setMessage({ text: 'Could not free VRAM.', type: 'error' });
    }
  };

  const f5 = modelsStatus?.f5_tts || {};
  const stable = modelsStatus?.stable_audio || {};
  const llama = modelsStatus?.llama || {};
  const xtts = modelsStatus?.xtts || {};
  const fish = modelsStatus?.fish_speech || {};
  const audioldm = modelsStatus?.audioldm2 || {};
  const whisper = modelsStatus?.whisper || {};

  const totalSize = (
    parseFloat(f5.size_gb || 0) + parseFloat(stable.size_gb || 0) + parseFloat(llama.size_gb || 0) +
    parseFloat(xtts.size_gb || 0) + parseFloat(fish.size_gb || 0) + parseFloat(audioldm.size_gb || 0) +
    parseFloat(whisper.size_gb || 0)
  ).toFixed(2);

  const gpuName = systemInfo?.gpu_name || 'GPU';
  const vramUsed = systemInfo?.gpu_vram_used_gb || '0.0';
  const vramTotal = systemInfo?.gpu_vram_total_gb || '0.0';
  const vramPct = systemInfo?.gpu_vram_percent || 0;
  const ramUsed = systemInfo?.ram_used_gb || '0.0';
  const ramTotal = systemInfo?.ram_total_gb || '0.0';
  const ramPct = systemInfo?.ram_percent || 0;
  const diskFree = systemInfo?.disk_free_gb || '0.0';

  return (
    <div className="space-y-8 animate-fadeIn max-w-6xl mx-auto">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 bg-white rounded-2xl border border-slate-200/90 shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
              Storage &amp; Hardware Management
            </span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <HardDrive className="w-6 h-6 text-cyan-600" />
            Model Manager &amp; Settings
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Manage neural weights, check for updates, monitor live GPU VRAM, and clean storage on demand.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-all active:scale-95 shadow-2xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-cyan-600' : ''}`} />
            <span>Refresh Status</span>
          </button>

          <button
            onClick={() => handleDelete('all')}
            disabled={deletingModel === 'all' || totalSize === '0.00'}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed shadow-2xs"
          >
            <Trash2 className="w-3.5 h-3.5 text-rose-600" />
            <span>Purge All ({totalSize} GB)</span>
          </button>
        </div>
      </div>

      {/* Alert / Feedback message */}
      {message.text && (
        <div
          className={`p-4 rounded-xl border text-sm flex items-center justify-between animate-fadeIn shadow-xs ${
            message.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : message.type === 'error'
              ? 'bg-rose-50 border-rose-200 text-rose-800'
              : 'bg-cyan-50 border-cyan-200 text-cyan-800'
          }`}
        >
          <div className="flex items-center gap-2">
            {message.type === 'success' ? (
              <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-600" />
            ) : message.type === 'error' ? (
              <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-600" />
            ) : (
              <RefreshCw className="w-5 h-5 flex-shrink-0 animate-spin text-cyan-600" />
            )}
            <span className="font-medium">{message.text}</span>
          </div>
          <button
            onClick={() => setMessage({ text: '', type: '' })}
            className="text-xs font-semibold hover:underline"
          >
            Close
          </button>
        </div>
      )}

      {/* Hardware Monitor Overview (White Mode) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* GPU VRAM Card */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-500 font-semibold">
            <span className="flex items-center gap-1.5 text-slate-800">
              <Cpu className="w-4 h-4 text-cyan-600" />
              {gpuName}
            </span>
            <span className="font-mono text-cyan-700 font-bold">
              {vramUsed} / {vramTotal} GB
            </span>
          </div>
          <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden shadow-inner">
            <div
              className="bg-gradient-to-r from-cyan-600 to-blue-600 h-full rounded-full transition-all duration-300"
              style={{ width: `${Math.min(100, Math.max(2, vramPct))}%` }}
            />
          </div>
          <div className="flex items-center justify-between pt-1">
            <span className="text-[11px] text-slate-500 font-mono">Dedicated Video Memory</span>
            <button
              onClick={handleUnloadVRAM}
              className="text-[11px] text-cyan-700 hover:text-cyan-800 font-bold hover:underline"
            >
              Clear VRAM Cache
            </button>
          </div>
        </div>

        {/* Disk Space Card */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-500 font-semibold">
            <span className="flex items-center gap-1.5 text-slate-800">
              <Database className="w-4 h-4 text-purple-600" />
              Storage Drive
            </span>
            <span className="font-mono text-purple-700 font-bold">
              {diskFree} GB Free
            </span>
          </div>
          <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden shadow-inner">
            <div
              className="bg-gradient-to-r from-purple-500 to-indigo-600 h-full rounded-full"
              style={{ width: '45%' }}
            />
          </div>
          <div className="flex items-center justify-between pt-1 text-[11px] text-slate-500 font-mono">
            <span>Model dir: /models</span>
            <span className="text-slate-700 font-semibold">{totalSize} GB in use</span>
          </div>
        </div>

        {/* System RAM Card */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-500 font-semibold">
            <span className="flex items-center gap-1.5 text-slate-800">
              <Layers className="w-4 h-4 text-emerald-600" />
              System RAM
            </span>
            <span className="font-mono text-emerald-700 font-bold">
              {ramUsed} / {ramTotal} GB
            </span>
          </div>
          <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden shadow-inner">
            <div
              className="bg-gradient-to-r from-emerald-500 to-teal-600 h-full rounded-full"
              style={{ width: `${Math.min(100, Math.max(2, ramPct))}%` }}
            />
          </div>
          <div className="flex items-center justify-between pt-1 text-[11px] text-slate-500 font-mono">
            <span>Dynamic System Memory</span>
            <span className="text-emerald-700 font-bold">{ramPct}% Utilized</span>
          </div>
        </div>
      </div>

      {/* Model Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {/* Model 1: F5-TTS */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between space-y-5">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-cyan-100 text-cyan-800 border border-cyan-200">
                  F5-TTS
                </span>
                <span className="text-xs text-slate-500 font-medium">Voice Synthesis &amp; Cloning</span>
              </div>
              {f5.installed ? (
                <span className="flex items-center gap-1 text-xs text-emerald-700 font-bold">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Installed ({f5.size_gb} GB)
                </span>
              ) : (
                <span className="flex items-center gap-1 text-xs text-amber-700 font-bold">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                  Not Installed (~2.3 GB)
                </span>
              )}
            </div>

            <h3 className="text-lg font-bold text-slate-900">F5-TTS Base Model</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              State-of-the-art non-autoregressive flow-matching architecture for natural speech generation and zero-shot voice cloning with just 5-10s of reference audio.
            </p>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-[11px] font-mono text-slate-600 space-y-1">
              <div className="flex justify-between">
                <span>Source:</span>
                <span className="text-slate-800 font-semibold">Hugging Face (SWivid/F5-TTS)</span>
              </div>
              <div className="flex justify-between">
                <span>Local Directory:</span>
                <span className="text-slate-800 truncate max-w-[200px]">/models/f5-tts</span>
              </div>
              <div className="flex justify-between">
                <span>VRAM Footprint:</span>
                <span className="text-cyan-700 font-bold">~2.2 GB VRAM</span>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-3 pt-2">
            {f5.installed ? (
              <button
                onClick={() => handleDelete('f5_tts')}
                disabled={deletingModel === 'f5_tts'}
                className="flex-1 py-2.5 px-4 rounded-xl text-xs font-bold bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 flex items-center justify-center gap-2 transition-all active:scale-95 shadow-2xs"
              >
                <Trash2 className="w-4 h-4 text-rose-600" />
                <span>Delete ({f5.size_gb} GB)</span>
              </button>
            ) : (
              <button
                onClick={() => handleDownload('f5_tts')}
                disabled={downloadingModel === 'f5_tts'}
                className="flex-1 py-2.5 px-4 rounded-xl text-xs font-bold bg-cyan-600 hover:bg-cyan-700 text-white flex items-center justify-center gap-2 transition-all active:scale-95 shadow-md shadow-cyan-600/20"
              >
                {downloadingModel === 'f5_tts' ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Downloading (~2.3 GB)...</span>
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    <span>Download F5-TTS (~2.3 GB)</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Model 2: Stable Audio Open */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between space-y-5">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-purple-100 text-purple-800 border border-purple-200">
                  Stable Audio Open
                </span>
                <span className="text-xs text-slate-500 font-medium">SFX &amp; Foley Diffusion</span>
              </div>
              {stable.installed ? (
                <span className="flex items-center gap-1 text-xs text-emerald-700 font-bold">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Installed ({stable.size_gb} GB)
                </span>
              ) : (
                <span className="flex items-center gap-1 text-xs text-amber-700 font-bold">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                  Not Installed (~4.8 GB)
                </span>
              )}
            </div>

            <h3 className="text-lg font-bold text-slate-900">Stable Audio Open 1.0</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Generative diffusion audio model by Stability AI for sound effects, foley, background atmospheres, and instrumental samples in 44.1kHz stereo up to 47 seconds.
            </p>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-[11px] font-mono text-slate-600 space-y-1">
              <div className="flex justify-between">
                <span>Source:</span>
                <span className="text-slate-800 font-semibold">stabilityai/stable-audio-open-1.0</span>
              </div>
              <div className="flex justify-between">
                <span>Local Directory:</span>
                <span className="text-slate-800 truncate max-w-[200px]">/models/stable-audio-open</span>
              </div>
              <div className="flex justify-between">
                <span>VRAM Footprint:</span>
                <span className="text-purple-700 font-bold">~4.5 GB VRAM (Float16)</span>
              </div>
            </div>
          </div>

          {/* HF Token required notice + input */}
          {!stable.installed && (
            <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 space-y-2.5">
              <p className="text-[11px] text-amber-800 font-semibold">
                🔑 Requires Hugging Face Token (gated model)
              </p>
              <p className="text-[11px] text-amber-700 leading-relaxed">
                1. Create a free account at <a href="https://huggingface.co" target="_blank" rel="noreferrer" className="underline font-semibold">huggingface.co</a>.<br/>
                2. Accept the license at <a href="https://huggingface.co/stabilityai/stable-audio-open-1.0" target="_blank" rel="noreferrer" className="underline font-semibold">stable-audio-open-1.0</a>.<br/>
                3. Generate a token at <a href="https://huggingface.co/settings/tokens" target="_blank" rel="noreferrer" className="underline font-semibold">settings/tokens</a> and paste below.
              </p>
              <div className="flex gap-2">
                <input
                  type="password"
                  value={hfToken}
                  onChange={e => setHfToken(e.target.value)}
                  placeholder="hf_your_token_here"
                  className="flex-1 px-3 py-2 text-xs rounded-lg border border-amber-300 bg-white focus:outline-none focus:border-amber-500 text-slate-800 placeholder-slate-400"
                />
                <button
                  onClick={handleSaveHFToken}
                  disabled={savingToken || !hfToken.trim()}
                  className="px-3 py-2 rounded-lg text-xs font-bold bg-amber-600 hover:bg-amber-700 text-white disabled:opacity-50 transition-all"
                >
                  {savingToken ? 'Saving...' : 'Save Token'}
                </button>
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex items-center gap-3 pt-2">
            {stable.installed ? (
              <button
                onClick={() => handleDelete('stable_audio')}
                disabled={deletingModel === 'stable_audio'}
                className="flex-1 py-2.5 px-4 rounded-xl text-xs font-bold bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 flex items-center justify-center gap-2 transition-all active:scale-95 shadow-2xs"
              >
                <Trash2 className="w-4 h-4 text-rose-600" />
                <span>Delete ({stable.size_gb} GB)</span>
              </button>
            ) : (
              <button
                onClick={() => handleDownload('stable_audio')}
                disabled={downloadingModel === 'stable_audio'}
                className="flex-1 py-2.5 px-4 rounded-xl text-xs font-bold bg-purple-600 hover:bg-purple-700 text-white flex items-center justify-center gap-2 transition-all active:scale-95 shadow-md shadow-purple-600/20"
              >
                {downloadingModel === 'stable_audio' ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Downloading (~4.8 GB)...</span>
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    <span>Download Stable Audio (~4.8 GB)</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Model 3: AudioLDM 2 Studio (Multi-Event SFX) */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between space-y-5">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-indigo-100 text-indigo-800 border border-indigo-200">
                  AudioLDM 2
                </span>
                <span className="text-xs text-slate-500 font-medium">Multi-Event Foley Studio</span>
              </div>
              {audioldm.installed ? (
                <span className="flex items-center gap-1 text-xs text-emerald-700 font-bold">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Installed ({audioldm.size_gb} GB)
                </span>
              ) : (
                <span className="flex items-center gap-1 text-xs text-amber-700 font-bold">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                  Not Installed (~1.8 GB)
                </span>
              )}
            </div>

            <h3 className="text-lg font-bold text-slate-900">AudioLDM 2 Studio</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Dual CLAP + T5 conditioning designed for composite soundscapes &amp; Foley actions where multiple prompt elements (e.g. reversing car screeching tires) must all be heard with strict adherence.
            </p>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-[11px] font-mono text-slate-600 space-y-1">
              <div className="flex justify-between">
                <span>Source:</span>
                <span className="text-slate-800 font-semibold">Hugging Face (cvssp/audioldm2)</span>
              </div>
              <div className="flex justify-between">
                <span>Local Directory:</span>
                <span className="text-slate-800 truncate max-w-[200px]">/models/audioldm2</span>
              </div>
              <div className="flex justify-between">
                <span>VRAM Footprint:</span>
                <span className="text-indigo-700 font-bold">~2.5 GB VRAM</span>
              </div>
              <div className="flex justify-between">
                <span>Conditioning:</span>
                <span className="text-indigo-700 font-bold">Dual CLAP + T5 Text</span>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-3 pt-2">
            {audioldm.installed ? (
              <button
                onClick={() => handleDelete('audioldm2')}
                disabled={deletingModel === 'audioldm2'}
                className="flex-1 py-2.5 px-4 rounded-xl text-xs font-bold bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 flex items-center justify-center gap-2 transition-all active:scale-95 shadow-2xs"
              >
                <Trash2 className="w-4 h-4 text-rose-600" />
                <span>Delete ({audioldm.size_gb} GB)</span>
              </button>
            ) : (
              <button
                onClick={() => handleDownload('audioldm2')}
                disabled={downloadingModel === 'audioldm2'}
                className="flex-1 py-2.5 px-4 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white flex items-center justify-center gap-2 transition-all active:scale-95 shadow-md shadow-indigo-600/20"
              >
                {downloadingModel === 'audioldm2' ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Downloading (~1.8 GB)...</span>
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    <span>Download AudioLDM 2 (~1.8 GB)</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Model 4: Llama 3 Local AI */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between space-y-5">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                  Llama 3
                </span>
                <span className="text-xs text-slate-500 font-medium">Assistant &amp; Prompt Enhancer</span>
              </div>
              {llama.installed ? (
                <span className="flex items-center gap-1 text-xs text-emerald-700 font-bold">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Installed ({llama.size_gb} GB)
                </span>
              ) : (
                <span className="flex items-center gap-1 text-xs text-amber-700 font-bold">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                  Not Installed (~2.8 GB)
                </span>
              )}
            </div>

            <h3 className="text-lg font-bold text-slate-900">Llama 3 Studio AI</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Meta Llama 3 local LLM running on your GPU for cinematic audio prompt expansion (Magic Wand), creative foley suggestions, and voice acting scriptwriting.
            </p>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-[11px] font-mono text-slate-600 space-y-1">
              <div className="flex justify-between">
                <span>Source:</span>
                <span className="text-slate-800 font-semibold">Hugging Face (unsloth/Llama-3.2)</span>
              </div>
              <div className="flex justify-between">
                <span>Local Directory:</span>
                <span className="text-slate-800 truncate max-w-[200px]">/models/llama</span>
              </div>
              <div className="flex justify-between">
                <span>VRAM Footprint:</span>
                <span className="text-emerald-700 font-bold">~2.8 GB VRAM (Float16)</span>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-3 pt-2">
            {llama.installed ? (
              <button
                onClick={() => handleDelete('llama')}
                disabled={deletingModel === 'llama'}
                className="flex-1 py-2.5 px-4 rounded-xl text-xs font-bold bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 flex items-center justify-center gap-2 transition-all active:scale-95 shadow-2xs"
              >
                <Trash2 className="w-4 h-4 text-rose-600" />
                <span>Delete ({llama.size_gb} GB)</span>
              </button>
            ) : (
              <button
                onClick={() => handleDownload('llama')}
                disabled={downloadingModel === 'llama'}
                className="flex-1 py-2.5 px-4 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white flex items-center justify-center gap-2 transition-all active:scale-95 shadow-md shadow-emerald-600/20"
              >
                {downloadingModel === 'llama' ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Downloading (~2.8 GB)...</span>
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    <span>Download Llama 3 (~2.8 GB)</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Model 4: XTTS-v2 Multilingual TTS */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between space-y-5">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-orange-100 text-orange-800 border border-orange-200">
                  XTTS-v2
                </span>
                <span className="text-xs text-slate-500 font-medium">Multilingual Voice Cloning</span>
              </div>
              {xtts.installed ? (
                <span className="flex items-center gap-1 text-xs text-emerald-700 font-bold">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Installed ({xtts.size_gb} GB)
                </span>
              ) : (
                <span className="flex items-center gap-1 text-xs text-amber-700 font-bold">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                  Not Installed (~2.0 GB)
                </span>
              )}
            </div>

            <h3 className="text-lg font-bold text-slate-900">XTTS-v2 Multilingual TTS</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Coqui XTTS-v2: state-of-the-art multilingual voice cloning supporting 17 languages including 🇳🇱 Dutch, German, French, Spanish and more. Zero-shot cloning from 6+ seconds of reference audio.
            </p>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-[11px] font-mono text-slate-600 space-y-1">
              <div className="flex justify-between">
                <span>Source:</span>
                <span className="text-slate-800 font-semibold">coqui/XTTS-v2</span>
              </div>
              <div className="flex justify-between">
                <span>Local Directory:</span>
                <span className="text-slate-800 truncate max-w-[200px]">/models/xtts-v2</span>
              </div>
              <div className="flex justify-between">
                <span>VRAM Footprint:</span>
                <span className="text-orange-700 font-bold">~3.5 GB VRAM</span>
              </div>
              <div className="flex justify-between">
                <span>Languages:</span>
                <span className="text-orange-700 font-bold">17 Languages incl. Dutch</span>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-3 pt-2">
            {xtts.installed ? (
              <button
                onClick={() => handleDelete('xtts')}
                disabled={deletingModel === 'xtts'}
                className="flex-1 py-2.5 px-4 rounded-xl text-xs font-bold bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 flex items-center justify-center gap-2 transition-all active:scale-95 shadow-2xs"
              >
                <Trash2 className="w-4 h-4 text-rose-600" />
                <span>Delete ({xtts.size_gb} GB)</span>
              </button>
            ) : (
              <button
                onClick={() => handleDownload('xtts')}
                disabled={downloadingModel === 'xtts'}
                className="flex-1 py-2.5 px-4 rounded-xl text-xs font-bold bg-orange-600 hover:bg-orange-700 text-white flex items-center justify-center gap-2 transition-all active:scale-95 shadow-md shadow-orange-600/20"
              >
                {downloadingModel === 'xtts' ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Downloading (~2.0 GB)...</span>
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    <span>Download XTTS-v2 (~2.0 GB)</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Model 5: Fish Speech 1.5 */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between space-y-5">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-teal-100 text-teal-800 border border-teal-200">
                  Fish Speech
                </span>
                <span className="text-xs text-slate-500 font-medium">Ultra-Quality Cloning</span>
              </div>
              {fish.installed ? (
                <span className="flex items-center gap-1 text-xs text-emerald-700 font-bold">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Installed ({fish.size_gb} GB)
                </span>
              ) : (
                <span className="flex items-center gap-1 text-xs text-amber-700 font-bold">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                  Not Installed (~700 MB)
                </span>
              )}
            </div>

            <h3 className="text-lg font-bold text-slate-900">Fish Speech 1.5 Ultra</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              State-of-the-art dual autoregressive architecture (DAR) + VQ-GAN decoder. Near-perfect voice cloning from 10 seconds of reference audio. Blazing fast, natural prosody, virtually zero artifacts.
            </p>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-[11px] font-mono text-slate-600 space-y-1">
              <div className="flex justify-between">
                <span>Source:</span>
                <span className="text-slate-800 font-semibold">fishaudio/fish-speech-1.5</span>
              </div>
              <div className="flex justify-between">
                <span>Local Directory:</span>
                <span className="text-slate-800 truncate max-w-[200px]">/models/fish-speech-1.5</span>
              </div>
              <div className="flex justify-between">
                <span>VRAM Footprint:</span>
                <span className="text-teal-700 font-bold">~2.0 GB VRAM</span>
              </div>
              <div className="flex justify-between">
                <span>Architecture:</span>
                <span className="text-teal-700 font-bold">DAR + VQ-GAN</span>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-3 pt-2">
            {fish.installed ? (
              <button
                onClick={() => handleDelete('fish_speech')}
                disabled={deletingModel === 'fish_speech'}
                className="flex-1 py-2.5 px-4 rounded-xl text-xs font-bold bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 flex items-center justify-center gap-2 transition-all active:scale-95 shadow-2xs"
              >
                <Trash2 className="w-4 h-4 text-rose-600" />
                <span>Delete ({fish.size_gb} GB)</span>
              </button>
            ) : (
              <button
                onClick={() => handleDownload('fish_speech')}
                disabled={downloadingModel === 'fish_speech'}
                className="flex-1 py-2.5 px-4 rounded-xl text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white flex items-center justify-center gap-2 transition-all active:scale-95 shadow-md shadow-teal-600/20"
              >
                {downloadingModel === 'fish_speech' ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Downloading (~700 MB)...</span>
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    <span>Download Fish Speech (~700 MB)</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Model 6: Faster-Whisper Medium */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between space-y-5">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-sky-100 text-sky-800 border border-sky-200">
                  Faster-Whisper
                </span>
                <span className="text-xs text-slate-500 font-medium">Voice ASR &amp; Cleaner</span>
              </div>
              {whisper.installed ? (
                <span className="flex items-center gap-1 text-xs text-emerald-700 font-bold">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Installed ({whisper.size_gb} GB)
                </span>
              ) : (
                <span className="flex items-center gap-1 text-xs text-amber-700 font-bold">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                  Not Installed (~1.5 GB)
                </span>
              )}
            </div>

            <h3 className="text-lg font-bold text-slate-900">Faster-Whisper Medium</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Automated high-precision speech-to-text running locally on CUDA float16. Auto-transcribes reference audio clips on upload to achieve 100% transcript accuracy and eliminate voice cloning hallucinations.
            </p>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-[11px] font-mono text-slate-600 space-y-1">
              <div className="flex justify-between">
                <span>Source:</span>
                <span className="text-slate-800 font-semibold">Systran/faster-whisper-medium</span>
              </div>
              <div className="flex justify-between">
                <span>Local Directory:</span>
                <span className="text-slate-800 truncate max-w-[200px]">/models/whisper-medium</span>
              </div>
              <div className="flex justify-between">
                <span>VRAM Footprint:</span>
                <span className="text-sky-700 font-bold">~1.5 GB VRAM (Float16)</span>
              </div>
              <div className="flex justify-between">
                <span>Cleaning:</span>
                <span className="text-sky-700 font-bold">VAD Trim + -20 LUFS</span>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-3 pt-2">
            {whisper.installed ? (
              <button
                onClick={() => handleDelete('whisper')}
                disabled={deletingModel === 'whisper'}
                className="flex-1 py-2.5 px-4 rounded-xl text-xs font-bold bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 flex items-center justify-center gap-2 transition-all active:scale-95 shadow-2xs"
              >
                <Trash2 className="w-4 h-4 text-rose-600" />
                <span>Delete ({whisper.size_gb} GB)</span>
              </button>
            ) : (
              <button
                onClick={() => handleDownload('whisper')}
                disabled={downloadingModel === 'whisper'}
                className="flex-1 py-2.5 px-4 rounded-xl text-xs font-bold bg-sky-600 hover:bg-sky-700 text-white flex items-center justify-center gap-2 transition-all active:scale-95 shadow-md shadow-sky-600/20"
              >
                {downloadingModel === 'whisper' ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Downloading (~1.5 GB)...</span>
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    <span>Download Whisper (~1.5 GB)</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
