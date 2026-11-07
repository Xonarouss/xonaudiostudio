import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Mic, Upload, Sparkles, Volume2, Music, CheckCircle2, AlertCircle,
  RefreshCw, Sliders, History, Play, Activity, User, Users, Trash2,
  Plus, ChevronRight, X, Star
} from 'lucide-react';
import AudioPlayer from './AudioPlayer';

const GENDER_COLORS = {
  female: { bg: 'bg-pink-50', border: 'border-pink-200', badge: 'bg-pink-100 text-pink-700', icon: '👩' },
  male:   { bg: 'bg-blue-50',  border: 'border-blue-200',  badge: 'bg-blue-100  text-blue-700',  icon: '👨' },
  neutral:{ bg: 'bg-slate-50', border: 'border-slate-200', badge: 'bg-slate-100 text-slate-700', icon: '🧑' },
  custom: { bg: 'bg-purple-50',border: 'border-purple-200',badge: 'bg-purple-100 text-purple-700',icon: '⭐' },
};

function VoiceCard({ voice, selected, onSelect, onPreview, onDelete }) {
  const c = GENDER_COLORS[voice.gender] || GENDER_COLORS.neutral;
  const isSelected = selected?.id === voice.id;

  return (
    <div
      onClick={() => onSelect(voice)}
      className={`relative group cursor-pointer rounded-2xl border-2 p-4 transition-all duration-200 select-none
        ${isSelected
          ? 'border-cyan-500 bg-cyan-50 shadow-md shadow-cyan-100'
          : `${c.border} ${c.bg} hover:border-cyan-300 hover:shadow-sm`
        }`}
    >
      {/* Selected checkmark */}
      {isSelected && (
        <div className="absolute top-2.5 right-2.5 w-5 h-5 bg-cyan-500 rounded-full flex items-center justify-center">
          <CheckCircle2 className="w-3.5 h-3.5 text-white" />
        </div>
      )}

      {/* Avatar */}
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-xl mb-3
        ${isSelected ? 'bg-cyan-100' : 'bg-white border border-slate-200'}`}>
        {c.icon}
      </div>

      <p className="text-sm font-bold text-slate-900 leading-tight">{voice.name}</p>
      <p className="text-[11px] text-slate-500 mt-0.5 leading-tight">{voice.description}</p>

      {/* Badge */}
      <span className={`inline-block mt-2 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wide ${c.badge}`}>
        {voice.type === 'custom' ? 'Custom' : voice.gender}
      </span>

      {/* Hover action buttons */}
      <div className="absolute bottom-3 right-3 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        {voice.audio_url && (
          <button
            onClick={(e) => { e.stopPropagation(); onPreview(voice); }}
            title="Preview voice"
            className="w-7 h-7 rounded-lg bg-white border border-slate-200 shadow-sm flex items-center justify-center hover:bg-cyan-50 hover:border-cyan-300 text-slate-600 hover:text-cyan-700 transition-colors"
          >
            <Play className="w-3.5 h-3.5" />
          </button>
        )}
        {voice.type === 'custom' && (
          <button
            onClick={(e) => { e.stopPropagation(); onDelete(voice); }}
            title="Delete custom voice"
            className="w-7 h-7 rounded-lg bg-white border border-rose-200 shadow-sm flex items-center justify-center hover:bg-rose-50 text-rose-500 hover:text-rose-700 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
}

export default function VoiceLab({ modelsStatus, onOpenModelManager }) {
  const [text, setText] = useState('Welcome to XonAudio Studio. This voice is generated locally with the F5-TTS architecture on your GPU.');

  // Voice selection state
  const [voices, setVoices] = useState([]);
  const [loadingVoices, setLoadingVoices] = useState(true);
  const [selectedVoice, setSelectedVoice] = useState(null);  // null = use default
  const [voiceMode, setVoiceMode] = useState('preset'); // 'preset' | 'upload'
  const [previewingVoice, setPreviewingVoice] = useState(null);
  const [previewAudio, setPreviewAudio] = useState(null);

  // Upload custom voice state
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadName, setUploadName] = useState('');
  const [uploadRefText, setUploadRefText] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState('');

  // Manual ref audio for one-time use (not saved to library)
  const [refAudioFile, setRefAudioFile] = useState(null);
  const [refAudioName, setRefAudioName] = useState('');
  const [refText, setRefText] = useState('');

  // Generation state
  const [speed, setSpeed] = useState(1.0);
  const [nfeSteps, setNfeSteps] = useState(32);
  const [removeSilence, setRemoveSilence] = useState(true);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [progressPercent, setProgressPercent] = useState(0);
  const [progressStage, setProgressStage] = useState('');
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [generatedAudioUrl, setGeneratedAudioUrl] = useState(null);
  const [lastGenText, setLastGenText] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [history, setHistory] = useState([]);

  const fileInputRef = useRef(null);
  const uploadInputRef = useRef(null);
  const previewAudioRef = useRef(null);
  const isF5Ready = modelsStatus?.f5_tts?.installed;

  // Load voices from API
  const loadVoices = useCallback(async () => {
    setLoadingVoices(true);
    try {
      const res = await fetch('/api/voices');
      if (res.ok) {
        const data = await res.json();
        setVoices(data);
        // Auto-select the first available preset
        if (!selectedVoice) {
          const first = data.find(v => v.available && v.type === 'preset');
          if (first) setSelectedVoice(first);
        }
      }
    } catch (e) {
      console.warn('Could not load voices:', e);
    } finally {
      setLoadingVoices(false);
    }
  }, []);

  useEffect(() => { loadVoices(); }, [loadVoices]);

  // Progress simulation
  useEffect(() => {
    let timer = null;
    let stepTimer = null;
    if (isGenerating) {
      setProgressPercent(10);
      setProgressStage('Preparing reference voice & loading F5-TTS weights...');
      setElapsedSeconds(0);
      timer = setInterval(() => setElapsedSeconds(s => s + 1), 1000);
      stepTimer = setInterval(() => {
        setProgressPercent(p => {
          if (p < 35) { setProgressStage('Computing flow-matching voice conditioning...'); return p + 6; }
          else if (p < 75) { setProgressStage(`Running ODE neural diffusion steps (${nfeSteps} steps)...`); return p + 4; }
          else if (p < 92) { setProgressStage('Vocoder synthesis & silence trimming...'); return p + 2; }
          return p;
        });
      }, 350);
    } else {
      if (progressPercent > 0 && progressPercent < 100) {
        setProgressPercent(100);
        setProgressStage('Complete!');
      }
    }
    return () => { clearInterval(timer); clearInterval(stepTimer); };
  }, [isGenerating, nfeSteps]);

  const handleEnhanceWithLlama = async () => {
    if (!text.trim() || isEnhancing) return;
    setIsEnhancing(true);
    try {
      const res = await fetch('/api/llama/enhance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: text, mode: 'voice' })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.enhanced) setText(data.enhanced);
      }
    } catch (e) {
      console.warn('Llama enhance error:', e);
    } finally {
      setIsEnhancing(false);
    }
  };

  const handleOneTimeFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('audio/')) {
      setErrorMessage('Please select a valid audio file (.wav, .mp3, .flac, etc.)');
      return;
    }
    setRefAudioFile(file);
    setRefAudioName(file.name);
    setSelectedVoice(null); // override preset
    setErrorMessage('');
  };

  const handlePreviewVoice = async (voice) => {
    if (!voice.audio_url) return;
    setPreviewingVoice(voice.id);
    try {
      if (previewAudioRef.current) {
        previewAudioRef.current.pause();
      }
      const audio = new Audio(voice.audio_url);
      previewAudioRef.current = audio;
      audio.onended = () => setPreviewingVoice(null);
      audio.onerror = () => setPreviewingVoice(null);
      await audio.play();
    } catch (e) {
      setPreviewingVoice(null);
    }
  };

  const handleDeleteCustomVoice = async (voice) => {
    // voice.id = "custom_stem", audio_url = "/api/voices/custom/stem.wav/audio"
    // Extract filename from audio_url
    const parts = voice.audio_url?.split('/') || [];
    const filename = parts[parts.length - 2]; // e.g. "myvoice.wav"
    if (!filename) return;
    try {
      await fetch(`/api/voices/custom/${filename}`, { method: 'DELETE' });
      if (selectedVoice?.id === voice.id) setSelectedVoice(null);
      await loadVoices();
    } catch (e) {
      console.warn('Delete custom voice error:', e);
    }
  };

  const handleUploadCustomVoice = async () => {
    if (!uploadFile) return;
    setIsUploading(true);
    setUploadSuccess('');
    try {
      const form = new FormData();
      form.append('voice_file', uploadFile);
      form.append('voice_name', uploadName || uploadFile.name.replace(/\.[^.]+$/, ''));
      const res = await fetch('/api/voices/upload', { method: 'POST', body: form });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(err.detail || 'Upload failed');
      }
      const data = await res.json();
      setUploadSuccess(`"${data.name}" saved! Click the Preset Voices tab to select it.`);
      setUploadFile(null);
      setUploadName('');
      if (uploadInputRef.current) uploadInputRef.current.value = '';
      // Reload voices, then auto-select the newly uploaded one
      const refreshRes = await fetch('/api/voices');
      if (refreshRes.ok) {
        const freshVoices = await refreshRes.json();
        setVoices(freshVoices);
        const newVoice = freshVoices.find(v => v.id === data.voice_id);
        if (newVoice) {
          setSelectedVoice(newVoice);
          // Switch to preset tab so user can see it selected
          setVoiceMode('preset');
        }
      }
    } catch (e) {
      setErrorMessage(e.message || 'Could not upload custom voice.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleGenerate = async () => {
    if (!text.trim()) { setErrorMessage('Please enter the text you want the voice to speak.'); return; }
    if (!isF5Ready) { setErrorMessage('F5-TTS model checkpoint is missing. Please download it via the Model Manager.'); return; }

    setIsGenerating(true);
    setErrorMessage('');

    try {
      const formData = new FormData();
      formData.append('gen_text', text);
      formData.append('speed', speed.toString());
      formData.append('nfe_steps', nfeSteps.toString());
      formData.append('remove_silence', removeSilence.toString());

      if (refAudioFile) {
        // One-time file upload takes priority
        formData.append('ref_audio', refAudioFile);
        formData.append('ref_text', refText);
      } else if (selectedVoice) {
        // Use voice from library
        formData.append('voice_id', selectedVoice.id);
        formData.append('ref_text', selectedVoice.ref_text || '');
      }

      const res = await fetch('/api/tts/generate', { method: 'POST', body: formData });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Generation error' }));
        throw new Error(err.detail || 'Voice generation failed');
      }

      const data = await res.json();
      setProgressPercent(100);
      setProgressStage('Voice rendered successfully!');
      setGeneratedAudioUrl(data.audio_url);
      setLastGenText(text);

      setHistory(prev => [{
        id: Date.now(),
        title: text.length > 45 ? text.substring(0, 45) + '...' : text,
        url: data.audio_url,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        voice: selectedVoice?.name || (refAudioFile ? refAudioName : 'Default'),
      }, ...prev.slice(0, 9)]);
    } catch (err) {
      setErrorMessage(err.message || 'An error occurred during voice synthesis.');
    } finally {
      setIsGenerating(false);
    }
  };

  const presetVoices = voices.filter(v => v.type === 'preset');
  const customVoices = voices.filter(v => v.type === 'custom');

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 bg-white rounded-2xl border border-slate-200/90 shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-cyan-100 text-cyan-800 border border-cyan-200">F5-TTS v1</span>
            <span className="text-xs text-slate-500 font-medium">Zero-Shot Voice Cloning & High-Fidelity Neural Speech</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Mic className="w-6 h-6 text-cyan-600" />
            Voice Lab
          </h2>
        </div>
        <div className="flex items-center gap-2">
          {isF5Ready ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-semibold">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Model Ready</span>
            </div>
          ) : (
            <button onClick={onOpenModelManager} className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-700 text-xs font-semibold hover:bg-amber-100 transition-colors">
              <AlertCircle className="w-4 h-4 text-amber-600" />
              <span>Model Missing — Download</span>
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
          <button onClick={() => setErrorMessage('')} className="text-xs font-semibold text-rose-600 hover:text-rose-800">Dismiss</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LEFT: Script + Voice Picker */}
        <div className="lg:col-span-7 space-y-6">

          {/* Text to Speak */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-bold text-slate-800">Text to Speak</label>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleEnhanceWithLlama}
                  disabled={isEnhancing || !text.trim()}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 transition-all active:scale-95 disabled:opacity-50"
                >
                  <Sparkles className={`w-3.5 h-3.5 text-purple-600 ${isEnhancing ? 'animate-spin' : ''}`} />
                  <span>{isEnhancing ? 'Refining...' : 'Refine with Llama 🪄'}</span>
                </button>
                <span className="text-xs font-mono text-slate-500">{text.length} chars</span>
              </div>
            </div>
            <textarea
              rows={5}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Enter speech script here (multilingual support)..."
              className="w-full rounded-xl p-4 text-sm glass-input text-slate-900 placeholder-slate-400 resize-none font-sans leading-relaxed shadow-xs"
            />
            {/* F5-TTS Style Token Quick-Insert Buttons */}
            <div className="space-y-2 pt-1">
              <p className="text-[11px] text-slate-500 font-semibold uppercase tracking-wide">Quick-Insert Speech Cues</p>
              <div className="flex flex-wrap gap-1.5">
                {[
                  { label: '😄 Ha ha ha!',   insert: ' Ha ha ha!' },
                  { label: '😤 Hmm...',       insert: ' Hmm...' },
                  { label: '😮 Oh!',          insert: ' Oh!' },
                  { label: '😯 Wow!',         insert: ' Wow!' },
                  { label: '⏸ Pause',         insert: '...' },
                  { label: '🤔 Well...',      insert: ' Well...' },
                  { label: '😲 Whoa!',        insert: ' Whoa!' },
                  { label: '💨 (sighs)',       insert: ' (sighs)' },
                  { label: '😬 Ugh',          insert: ' Ugh.' },
                  { label: '🎉 Yes!',         insert: ' Yes!' },
                  { label: '🔡 EMPHASIS',     insert: ' ' },
                ].map((token) => (
                  <button
                    key={token.label}
                    type="button"
                    onClick={() => {
                      if (token.label === '🔡 EMPHASIS') {
                        // Uppercase the last word
                        setText(prev => {
                          const words = prev.trimEnd().split(' ');
                          if (words.length > 0) {
                            words[words.length - 1] = words[words.length - 1].toUpperCase();
                          }
                          return words.join(' ');
                        });
                      } else {
                        setText(prev => prev + token.insert);
                      }
                    }}
                    className="px-2 py-1 rounded-lg text-[11px] font-semibold bg-slate-100 hover:bg-cyan-50 text-slate-600 hover:text-cyan-700 border border-slate-200 hover:border-cyan-300 transition-all active:scale-95"
                    title={`Insert: ${token.insert}`}
                  >
                    {token.label}
                  </button>
                ))}
              </div>
              <p className="text-[10px] text-slate-400">
                💡 F5-TTS reads text naturally — punctuation controls rhythm. Use "..." for pauses, "!" for emphasis, and UPPERCASE WORDS for stress.
              </p>
            </div>
          </div>

          {/* ===== VOICE PICKER ===== */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            {/* Tab Header */}
            <div className="flex border-b border-slate-100">
              <button
                onClick={() => setVoiceMode('preset')}
                className={`flex-1 py-3.5 text-sm font-semibold flex items-center justify-center gap-2 transition-colors ${voiceMode === 'preset' ? 'bg-white text-cyan-700 border-b-2 border-cyan-500' : 'bg-slate-50 text-slate-500 hover:text-slate-700'}`}
              >
                <Users className="w-4 h-4" />
                Preset Voices
                {presetVoices.length > 0 && (
                  <span className="ml-1 px-1.5 py-0.5 bg-cyan-100 text-cyan-700 text-[10px] font-bold rounded-full">{presetVoices.length}</span>
                )}
              </button>
              <button
                onClick={() => setVoiceMode('upload')}
                className={`flex-1 py-3.5 text-sm font-semibold flex items-center justify-center gap-2 transition-colors ${voiceMode === 'upload' ? 'bg-white text-purple-700 border-b-2 border-purple-500' : 'bg-slate-50 text-slate-500 hover:text-slate-700'}`}
              >
                <Upload className="w-4 h-4" />
                Upload / Clone
                {customVoices.length > 0 && (
                  <span className="ml-1 px-1.5 py-0.5 bg-purple-100 text-purple-700 text-[10px] font-bold rounded-full">{customVoices.length}</span>
                )}
              </button>
            </div>

            <div className="p-5">
              {/* PRESET VOICES TAB */}
              {voiceMode === 'preset' && (
                <div className="space-y-5">
                  <p className="text-xs text-slate-500">
                    Choose a built-in voice for immediate synthesis — no upload required. Click <Play className="inline w-3 h-3 text-slate-500" /> to preview each voice.
                  </p>

                  {loadingVoices ? (
                    <div className="flex items-center justify-center py-8 gap-2 text-slate-400 text-sm">
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Loading voices...
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      {presetVoices.map(voice => (
                        <VoiceCard
                          key={voice.id}
                          voice={voice}
                          selected={selectedVoice}
                          onSelect={(v) => { setSelectedVoice(v); setRefAudioFile(null); setRefAudioName(''); }}
                          onPreview={handlePreviewVoice}
                          onDelete={handleDeleteCustomVoice}
                        />
                      ))}
                    </div>
                  )}

                  {/* Custom voices section */}
                  {customVoices.length > 0 && (
                    <div className="pt-4 border-t border-slate-100 space-y-3">
                      <p className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                        <Star className="w-3.5 h-3.5 text-purple-500" /> Your Custom Voices
                      </p>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                        {customVoices.map(voice => (
                          <VoiceCard
                            key={voice.id}
                            voice={voice}
                            selected={selectedVoice}
                            onSelect={(v) => { setSelectedVoice(v); setRefAudioFile(null); setRefAudioName(''); }}
                            onPreview={handlePreviewVoice}
                            onDelete={handleDeleteCustomVoice}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Selected voice info bar */}
                  {selectedVoice && (
                    <div className="flex items-center gap-3 p-3 bg-cyan-50 rounded-xl border border-cyan-200 animate-fadeIn">
                      <div className="text-xl">{GENDER_COLORS[selectedVoice.gender]?.icon || '🧑'}</div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-bold text-cyan-900">{selectedVoice.name} selected</p>
                        <p className="text-[11px] text-cyan-700 truncate">{selectedVoice.description}</p>
                      </div>
                      <button onClick={() => setSelectedVoice(null)} className="text-[10px] text-cyan-600 hover:text-cyan-800 font-medium underline">Use default</button>
                    </div>
                  )}
                </div>
              )}

              {/* UPLOAD / CLONE TAB */}
              {voiceMode === 'upload' && (
                <div className="space-y-5">
                  <p className="text-xs text-slate-500">
                    Upload a 5–10 second clean audio clip to clone any voice. Files are saved to your personal voice library.
                  </p>

                  {/* Upload area */}
                  <input type="file" ref={uploadInputRef} accept="audio/*" className="hidden"
                    onChange={(e) => { const f = e.target.files?.[0]; if (f) { setUploadFile(f); setUploadName(f.name.replace(/\.[^.]+$/, '')); }}}
                  />
                  <div
                    onClick={() => uploadInputRef.current?.click()}
                    className={`p-6 rounded-xl border-2 border-dashed cursor-pointer transition-all flex flex-col items-center justify-center gap-2 ${
                      uploadFile ? 'border-purple-400 bg-purple-50/60' : 'border-slate-300 hover:border-purple-400 hover:bg-purple-50/30'
                    }`}
                  >
                    <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center border border-slate-200 shadow-xs">
                      {uploadFile ? <CheckCircle2 className="w-6 h-6 text-purple-600" /> : <Upload className="w-6 h-6 text-slate-400" />}
                    </div>
                    <p className="text-sm font-semibold text-slate-800 text-center">
                      {uploadFile ? uploadFile.name : 'Click to select reference audio'}
                    </p>
                    <span className="text-xs text-slate-500 font-mono">
                      {uploadFile ? `${(uploadFile.size / 1024 / 1024).toFixed(2)} MB` : 'WAV, MP3, FLAC, M4A — 5–10 seconds recommended'}
                    </span>
                  </div>

                  {uploadFile && (
                    <div className="space-y-3 animate-fadeIn">
                      <div className="space-y-1.5">
                        <label className="text-xs font-semibold text-slate-700">Voice Name (for your library)</label>
                        <input
                          type="text"
                          value={uploadName}
                          onChange={e => setUploadName(e.target.value)}
                          placeholder="e.g. Morgan Freeman, My Voice, Client Voice..."
                          className="w-full px-3.5 py-2.5 text-xs rounded-lg glass-input text-slate-900 placeholder-slate-400 shadow-xs"
                        />
                      </div>
                      <button
                        onClick={handleUploadCustomVoice}
                        disabled={isUploading}
                        className="w-full py-3 rounded-xl font-bold text-sm bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:brightness-105 active:scale-[0.99] shadow-md disabled:opacity-60 flex items-center justify-center gap-2"
                      >
                        {isUploading ? <><RefreshCw className="w-4 h-4 animate-spin" /> Saving to library...</> : <><Plus className="w-4 h-4" /> Save to Voice Library</>}
                      </button>
                    </div>
                  )}

                  {uploadSuccess && (
                    <div className="flex items-center gap-2 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-700 text-xs font-semibold animate-fadeIn">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      {uploadSuccess}
                    </div>
                  )}

                  {/* One-time upload — not saved to library */}
                  <div className="pt-4 border-t border-slate-100 space-y-3">
                    <p className="text-xs font-bold text-slate-700 uppercase tracking-wider">One-Time Reference (not saved)</p>
                    <input type="file" ref={fileInputRef} onChange={handleOneTimeFileChange} accept="audio/*" className="hidden" />
                    <div
                      onClick={() => fileInputRef.current?.click()}
                      className={`p-4 rounded-xl border-2 border-dashed cursor-pointer transition-all flex items-center gap-3 ${
                        refAudioFile ? 'border-cyan-400 bg-cyan-50/40' : 'border-slate-200 hover:border-cyan-300 hover:bg-slate-50'
                      }`}
                    >
                      <div className="w-9 h-9 rounded-lg bg-white border border-slate-200 flex items-center justify-center flex-shrink-0">
                        {refAudioFile ? <CheckCircle2 className="w-5 h-5 text-cyan-600" /> : <Mic className="w-5 h-5 text-slate-400" />}
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs font-semibold text-slate-800 truncate">{refAudioName || 'Select audio for this generation only'}</p>
                        <p className="text-[11px] text-slate-500">Will not be saved to your voice library</p>
                      </div>
                      {refAudioFile && (
                        <button onClick={(e) => { e.stopPropagation(); setRefAudioFile(null); setRefAudioName(''); setRefText(''); if (fileInputRef.current) fileInputRef.current.value = ''; }}
                          className="ml-auto text-slate-400 hover:text-rose-500 p-1">
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </div>

                    {refAudioFile && (
                      <div className="space-y-1.5 animate-fadeIn">
                        <label className="text-xs font-semibold text-slate-700">What does this audio say? (Reference transcript)</label>
                        <input
                          type="text"
                          value={refText}
                          onChange={e => setRefText(e.target.value)}
                          placeholder="e.g. 'Hello, this is a sample recording for voice cloning.'"
                          className="w-full px-3.5 py-2.5 text-xs rounded-lg glass-input text-slate-900 placeholder-slate-400 shadow-xs"
                        />
                        <p className="text-[11px] text-slate-500">A matching transcript ensures the highest fidelity and zero pronunciation artifacts.</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* RIGHT: Parameters + Output */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-slate-800 flex items-center gap-2">
                <Sliders className="w-4 h-4 text-cyan-600" />
                Parameters
              </span>
              <button onClick={() => setShowAdvanced(!showAdvanced)} className="text-xs text-cyan-700 hover:text-cyan-800 font-semibold">
                {showAdvanced ? 'Simple' : 'Advanced'}
              </button>
            </div>

            {/* Active voice indicator */}
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-0.5">
              <span className="text-slate-500 font-medium">Active voice: </span>
              <span className="font-bold text-slate-800">
                {refAudioFile ? `📎 ${refAudioName} (one-time)` : selectedVoice ? `${GENDER_COLORS[selectedVoice.gender]?.icon} ${selectedVoice.name}` : '🤖 Default (basic_ref_en)'}
              </span>
            </div>

            {/* Speed slider */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-slate-700 font-medium">
                <span>Speaking Rate</span>
                <span className="font-mono text-cyan-700 font-bold">{speed.toFixed(2)}x</span>
              </div>
              <input type="range" min="0.6" max="1.6" step="0.05" value={speed} onChange={e => setSpeed(parseFloat(e.target.value))} className="w-full accent-cyan-600" />
            </div>

            {showAdvanced && (
              <div className="space-y-4 pt-3 border-t border-slate-100 animate-fadeIn">
                <div className="space-y-2">
                  <div className="flex justify-between text-xs text-slate-700 font-medium">
                    <span>NFE Steps (Sampling Quality)</span>
                    <span className="font-mono text-cyan-700 font-bold">{nfeSteps} steps</span>
                  </div>
                  <input type="range" min="16" max="64" step="4" value={nfeSteps} onChange={e => setNfeSteps(parseInt(e.target.value))} className="w-full accent-cyan-600" />
                  <p className="text-[11px] text-slate-500">32 steps is optimal for high speed and natural flow.</p>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-700 font-medium">Auto-trim silence</span>
                  <input type="checkbox" checked={removeSilence} onChange={e => setRemoveSilence(e.target.checked)} className="w-4 h-4 rounded text-cyan-600 focus:ring-cyan-500 border-slate-300" />
                </div>
              </div>
            )}

            {/* Progress bar */}
            {isGenerating && (
              <div className="space-y-2 pt-2 p-4 bg-slate-50 rounded-xl border border-cyan-100 animate-fadeIn">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-800 flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-cyan-600 animate-pulse" />
                    {progressStage}
                  </span>
                  <span className="font-mono font-bold text-cyan-700">{progressPercent}% ({elapsedSeconds}s)</span>
                </div>
                <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden shadow-inner">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500 transition-all duration-300 shadow-sm"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>
            )}

            {/* Generate button */}
            <button
              onClick={handleGenerate}
              disabled={isGenerating || !text.trim() || !isF5Ready}
              className={`w-full py-4 px-6 rounded-xl font-bold text-sm flex items-center justify-center gap-2.5 shadow-md transition-all duration-200 ${
                isGenerating
                  ? 'bg-slate-200 text-slate-400 cursor-not-allowed border border-slate-300'
                  : !isF5Ready
                  ? 'bg-amber-100 text-amber-800 cursor-not-allowed border border-amber-300'
                  : 'bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 text-white hover:brightness-105 active:scale-[0.99] shadow-cyan-600/20'
              }`}
            >
              {isGenerating ? (
                <><RefreshCw className="w-5 h-5 animate-spin text-cyan-600" /><span>Synthesizing Voice ({progressPercent}%)...</span></>
              ) : !isF5Ready ? (
                <><AlertCircle className="w-5 h-5 text-amber-700" /><span>F5-TTS Not Installed (Download in Manager)</span></>
              ) : (
                <><Sparkles className="w-5 h-5" /><span>Generate Voice (F5-TTS)</span></>
              )}
            </button>
          </div>

          {/* Audio Output */}
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
              <p className="text-xs text-slate-500 max-w-xs">Select a voice above, type your script, and click Generate Voice.</p>
            </div>
          )}

          {/* History */}
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
                    onClick={() => { setGeneratedAudioUrl(item.url); setLastGenText(item.title); }}
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
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className="text-[10px] text-slate-400 font-medium">{item.voice}</span>
                      <span className="text-[10px] text-slate-400 font-mono">{item.timestamp}</span>
                    </div>
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
