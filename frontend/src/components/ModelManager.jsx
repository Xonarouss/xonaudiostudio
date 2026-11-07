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
  Server
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

  const handleDownload = async (modelKey) => {
    setDownloadingModel(modelKey);
    setMessage({ text: `Downloaden gestart voor ${modelKey}... Dit kan enkele minuten duren afhankelijk van je verbinding.`, type: 'info' });

    try {
      const res = await fetch(`/api/models/download/${modelKey}`, {
        method: 'POST',
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Fout bij downloaden');
      }
      setMessage({ text: `${data.message || 'Model succesvol gedownload!'}`, type: 'success' });
      await onRefresh();
    } catch (err) {
      setMessage({ text: err.message || 'Download mislukt.', type: 'error' });
    } finally {
      setDownloadingModel(null);
    }
  };

  const handleDelete = async (modelKey) => {
    const confirmText = modelKey === 'all'
      ? 'Weet je zeker dat je ALLE modellen wilt verwijderen om schijfruimte vrij te maken?'
      : `Weet je zeker dat je het checkpoint van ${modelKey} wilt verwijderen?`;

    if (!window.confirm(confirmText)) return;

    setDeletingModel(modelKey);
    setMessage({ text: 'Modelbestanden verwijderen van schijf...', type: 'info' });

    try {
      const res = await fetch('/api/models/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_key: modelKey }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Fout bij verwijderen');
      }
      setMessage({ text: data.message || 'Bestanden succesvol verwijderd.', type: 'success' });
      await onRefresh();
    } catch (err) {
      setMessage({ text: err.message || 'Verwijderen mislukt.', type: 'error' });
    } finally {
      setDeletingModel(null);
    }
  };

  const handleUnloadVRAM = async () => {
    try {
      const res = await fetch('/api/models/unload', { method: 'POST' });
      const data = await res.json();
      setMessage({ text: data.message || 'GPU VRAM succesvol vrijgemaakt!', type: 'success' });
      await onRefresh();
    } catch (err) {
      setMessage({ text: 'Kon VRAM niet vrijmaken.', type: 'error' });
    }
  };

  const f5 = modelsStatus?.f5_tts || {};
  const stable = modelsStatus?.stable_audio || {};

  const totalSize = (
    parseFloat(f5.size_gb || 0) + parseFloat(stable.size_gb || 0)
  ).toFixed(2);

  return (
    <div className="space-y-8 animate-fadeIn max-w-6xl mx-auto">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 glass-panel rounded-2xl border border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              Opslag &amp; Hardware Management
            </span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <HardDrive className="w-6 h-6 text-cyan-400" />
            Model Manager &amp; Settings
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Beheer lokale AI-gewichten, monitor VRAM op de RTX 5080 en maak direct schijfruimte vrij.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-studio-900 hover:bg-studio-800 text-slate-300 border border-slate-700 hover:border-slate-600 transition-all active:scale-95"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-cyan-400' : ''}`} />
            <span>Vernieuw Status</span>
          </button>

          <button
            onClick={() => handleDelete('all')}
            disabled={deletingModel === 'all' || totalSize === '0.00'}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Trash2 className="w-3.5 h-3.5 text-rose-400" />
            <span>Verwijder Alles ({totalSize} GB)</span>
          </button>
        </div>
      </div>

      {/* Alert / Feedback message */}
      {message.text && (
        <div
          className={`p-4 rounded-xl border text-sm flex items-center justify-between ${
            message.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : message.type === 'error'
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
              : 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300'
          }`}
        >
          <div className="flex items-center gap-2">
            {message.type === 'success' ? (
              <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
            ) : message.type === 'error' ? (
              <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            ) : (
              <RefreshCw className="w-5 h-5 flex-shrink-0 animate-spin" />
            )}
            <span>{message.text}</span>
          </div>
          <button
            onClick={() => setMessage({ text: '', type: '' })}
            className="text-xs font-semibold hover:underline"
          >
            Sluiten
          </button>
        </div>
      )}

      {/* Hardware Monitor Overview (RTX 5080 + Ryzen 7800X3D + Disk) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* GPU VRAM Card */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5 font-medium">
              <Cpu className="w-4 h-4 text-cyan-400" />
              Nvidia GeForce RTX 5080
            </span>
            <span className="font-mono text-cyan-400">
              {systemInfo?.gpu_vram_used_gb || '0.0'} / {systemInfo?.gpu_vram_total_gb || '16.0'} GB
            </span>
          </div>
          {/* Progress bar */}
          <div className="w-full bg-studio-950 h-2.5 rounded-full overflow-hidden border border-slate-800">
            <div
              className="bg-gradient-to-r from-cyan-500 to-blue-500 h-full rounded-full transition-all duration-300"
              style={{
                width: `${Math.min(
                  100,
                  ((parseFloat(systemInfo?.gpu_vram_used_gb || 0) /
                    parseFloat(systemInfo?.gpu_vram_total_gb || 16)) *
                    100)
                )}%`,
              }}
            />
          </div>
          <div className="flex items-center justify-between pt-1">
            <span className="text-[11px] text-slate-500 font-mono">16 GB GDDR7 VRAM</span>
            <button
              onClick={handleUnloadVRAM}
              className="text-[11px] text-cyan-400 hover:text-cyan-300 font-medium hover:underline"
            >
              Maak VRAM Vrij
            </button>
          </div>
        </div>

        {/* Disk Space Card */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5 font-medium">
              <Database className="w-4 h-4 text-purple-400" />
              Schijfruimte (D: Schijf)
            </span>
            <span className="font-mono text-purple-400">
              {systemInfo?.disk_free_gb || 'Beschikbaar'} GB Vrij
            </span>
          </div>
          <div className="w-full bg-studio-950 h-2.5 rounded-full overflow-hidden border border-slate-800">
            <div
              className="bg-gradient-to-r from-purple-500 to-indigo-500 h-full rounded-full"
              style={{ width: '45%' }}
            />
          </div>
          <div className="flex items-center justify-between pt-1 text-[11px] text-slate-500 font-mono">
            <span>Model map: /models</span>
            <span className="text-slate-400 font-medium">{totalSize} GB in gebruik</span>
          </div>
        </div>

        {/* System RAM Card */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5 font-medium">
              <Layers className="w-4 h-4 text-emerald-400" />
              Systeemgeheugen (RAM)
            </span>
            <span className="font-mono text-emerald-400">
              {systemInfo?.ram_used_gb || '8.2'} / {systemInfo?.ram_total_gb || '64.0'} GB
            </span>
          </div>
          <div className="w-full bg-studio-950 h-2.5 rounded-full overflow-hidden border border-slate-800">
            <div
              className="bg-gradient-to-r from-emerald-500 to-teal-500 h-full rounded-full"
              style={{
                width: `${Math.min(
                  100,
                  ((parseFloat(systemInfo?.ram_used_gb || 8) /
                    parseFloat(systemInfo?.ram_total_gb || 64)) *
                    100)
                )}%`,
              }}
            />
          </div>
          <div className="flex items-center justify-between pt-1 text-[11px] text-slate-500 font-mono">
            <span>AMD Ryzen 7 7800X3D</span>
            <span className="text-emerald-400 font-medium">64 GB DDR5</span>
          </div>
        </div>
      </div>

      {/* Model Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Model 1: F5-TTS */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col justify-between space-y-5">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-md text-xs font-mono font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  F5-TTS
                </span>
                <span className="text-xs text-slate-400">Voice Synthesis &amp; Cloning</span>
              </div>
              {f5.installed ? (
                <span className="flex items-center gap-1 text-xs text-emerald-400 font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Geïnstalleerd ({f5.size_gb} GB)
                </span>
              ) : (
                <span className="flex items-center gap-1 text-xs text-amber-400 font-medium">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  Niet geïnstalleerd (~2.3 GB)
                </span>
              )}
            </div>

            <h3 className="text-lg font-bold text-white">F5-TTS Base Model</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              State-of-the-art non-autoregressieve flow-matching architectuur voor natuurlijke stemgeneratie en zero-shot stemkloonen met slechts 5-10 seconden referentie-audio.
            </p>

            <div className="p-3 rounded-xl bg-studio-950/70 border border-slate-800 text-[11px] font-mono text-slate-400 space-y-1">
              <div className="flex justify-between">
                <span>Bron:</span>
                <span className="text-slate-300">Hugging Face (SWivid/F5-TTS)</span>
              </div>
              <div className="flex justify-between">
                <span>Lokale Map:</span>
                <span className="text-slate-300 truncate max-w-[200px]">/models/f5-tts</span>
              </div>
              <div className="flex justify-between">
                <span>VRAM Voetafdruk:</span>
                <span className="text-cyan-400">~2.2 GB VRAM</span>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-3 pt-2">
            {f5.installed ? (
              <button
                onClick={() => handleDelete('f5_tts')}
                disabled={deletingModel === 'f5_tts'}
                className="flex-1 py-2.5 px-4 rounded-xl text-xs font-semibold bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 flex items-center justify-center gap-2 transition-all active:scale-95"
              >
                <Trash2 className="w-4 h-4 text-rose-400" />
                <span>Verwijder ({f5.size_gb} GB)</span>
              </button>
            ) : (
              <button
                onClick={() => handleDownload('f5_tts')}
                disabled={downloadingModel === 'f5_tts'}
                className="flex-1 py-2.5 px-4 rounded-xl text-xs font-semibold bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 flex items-center justify-center gap-2 transition-all active:scale-95 shadow-glow-cyan"
              >
                {downloadingModel === 'f5_tts' ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin text-cyan-400" />
                    <span>Downloaden (~2.3 GB)...</span>
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
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col justify-between space-y-5">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-md text-xs font-mono font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                  Stable Audio Open
                </span>
                <span className="text-xs text-slate-400">SFX &amp; Foley Diffusion</span>
              </div>
              {stable.installed ? (
                <span className="flex items-center gap-1 text-xs text-emerald-400 font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Geïnstalleerd ({stable.size_gb} GB)
                </span>
              ) : (
                <span className="flex items-center gap-1 text-xs text-amber-400 font-medium">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  Niet geïnstalleerd (~4.8 GB)
                </span>
              )}
            </div>

            <h3 className="text-lg font-bold text-white">Stable Audio Open 1.0</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Generatieve audiomodel van Stability AI voor geluidseffecten, foley, achtergrondatmosferen en instrumentale samples in 44.1kHz stereo tot 47 seconden.
            </p>

            <div className="p-3 rounded-xl bg-studio-950/70 border border-slate-800 text-[11px] font-mono text-slate-400 space-y-1">
              <div className="flex justify-between">
                <span>Bron:</span>
                <span className="text-slate-300">stabilityai/stable-audio-open-1.0</span>
              </div>
              <div className="flex justify-between">
                <span>Lokale Map:</span>
                <span className="text-slate-300 truncate max-w-[200px]">/models/stable-audio-open</span>
              </div>
              <div className="flex justify-between">
                <span>VRAM Voetafdruk:</span>
                <span className="text-purple-400">~4.5 GB VRAM (Float16)</span>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-3 pt-2">
            {stable.installed ? (
              <button
                onClick={() => handleDelete('stable_audio')}
                disabled={deletingModel === 'stable_audio'}
                className="flex-1 py-2.5 px-4 rounded-xl text-xs font-semibold bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 flex items-center justify-center gap-2 transition-all active:scale-95"
              >
                <Trash2 className="w-4 h-4 text-rose-400" />
                <span>Verwijder ({stable.size_gb} GB)</span>
              </button>
            ) : (
              <button
                onClick={() => handleDownload('stable_audio')}
                disabled={downloadingModel === 'stable_audio'}
                className="flex-1 py-2.5 px-4 rounded-xl text-xs font-semibold bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 border border-purple-500/40 flex items-center justify-center gap-2 transition-all active:scale-95 shadow-glow-purple"
              >
                {downloadingModel === 'stable_audio' ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin text-purple-400" />
                    <span>Downloaden (~4.8 GB)...</span>
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
      </div>
    </div>
  );
}

