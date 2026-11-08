import React, { useState, useEffect, useRef } from 'react';
import {
  Music2,
  Disc,
  Upload,
  Link2,
  Sliders,
  Play,
  Pause,
  Download,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Sparkles,
  Volume2,
  FileAudio,
  Layers,
  ArrowRight,
  Headphones,
  Settings2,
  Radio,
  FileUp,
  X
} from 'lucide-react';

export default function SongCoverLab({ modelsStatus, onOpenModelManager }) {
  // Input mode: 'file' | 'url'
  const [inputMode, setInputMode] = useState('file');
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileAudioPath, setFileAudioPath] = useState('');
  const [urlInput, setUrlInput] = useState('');
  const [isFetchingUrl, setIsFetchingUrl] = useState(false);
  const [fetchedUrlData, setFetchedUrlData] = useState(null);

  // Voice & Tuning
  const [rvcModels, setRvcModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [pitchShift, setPitchShift] = useState(0);
  const [indexRate, setIndexRate] = useState(0.75);

  // Volume sliders (0% - 150%)
  const [vocalVolume, setVocalVolume] = useState(100);
  const [instVolume, setInstVolume] = useState(100);

  // Upload modal for custom RVC voice (.pth + .index)
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [modelPthFile, setModelPthFile] = useState(null);
  const [modelIndexFile, setModelIndexFile] = useState(null);
  const [isUploadingModel, setIsUploadingModel] = useState(false);
  const [uploadError, setUploadError] = useState('');

  // Generation & Pipeline state
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeStage, setActiveStage] = useState(0); // 0 = idle, 1 = fetch, 2 = separate, 3 = convert, 4 = mix
  const [stageProgressText, setStageProgressText] = useState('');
  const [generationResult, setGenerationResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  // Audio player state
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeTrack, setActiveTrack] = useState('mix'); // 'mix' | 'vocals' | 'inst'
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef(null);

  // Check prerequisites
  const bsRoformerInstalled = !!modelsStatus?.bs_roformer?.installed;
  const rmvpeInstalled = !!modelsStatus?.rmvpe?.installed;

  // Fetch installed RVC models
  const fetchRvcModels = async () => {
    try {
      const res = await fetch('/api/song-cover/models');
      if (res.ok) {
        const data = await res.json();
        const list = data.models || [];
        setRvcModels(list);
        if (list.length > 0 && !selectedModel) {
          setSelectedModel(list[0].filename);
        }
      }
    } catch (e) {
      console.warn('Could not fetch RVC models:', e);
    }
  };

  useEffect(() => {
    fetchRvcModels();
  }, []);

  // Handle file drop / select
  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setSelectedFile(file);
    setErrorMessage('');

    // Auto-upload audio to server
    const formData = new FormData();
    formData.append('audio_file', file);

    try {
      const res = await fetch('/api/song-cover/upload-audio', {
        method: 'POST',
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        setFileAudioPath(data.audio_path);
      } else {
        const err = await res.json();
        setErrorMessage(err.detail || 'Fout bij uploaden van audio.');
      }
    } catch (err) {
      setErrorMessage(`Uploadfout: ${err.message}`);
    }
  };

  // Handle URL fetch
  const handleFetchUrl = async () => {
    if (!urlInput.trim()) {
      setErrorMessage('Vul een geldige YouTube of Spotify link in.');
      return;
    }
    setIsFetchingUrl(true);
    setErrorMessage('');
    try {
      const res = await fetch('/api/song-cover/fetch-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: urlInput.trim() }),
      });
      if (res.ok) {
        const data = await res.json();
        setFetchedUrlData(data);
        setFileAudioPath(data.audio_path);
      } else {
        const err = await res.json();
        setErrorMessage(err.detail || 'Kon audio niet downloaden vanaf de opgegeven URL.');
      }
    } catch (err) {
      setErrorMessage(`Netwerkfout bij ophalen URL: ${err.message}`);
    } finally {
      setIsFetchingUrl(false);
    }
  };

  // Upload custom RVC model (.pth + .index)
  const handleUploadRvcModel = async (e) => {
    e.preventDefault();
    if (!modelPthFile) {
      setUploadError('Selecteer minimaal een .pth stemmodel bestand.');
      return;
    }

    setIsUploadingModel(true);
    setUploadError('');

    const formData = new FormData();
    formData.append('model_file', modelPthFile);
    if (modelIndexFile) {
      formData.append('index_file', modelIndexFile);
    }

    try {
      const res = await fetch('/api/song-cover/upload-model', {
        method: 'POST',
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        await fetchRvcModels();
        setSelectedModel(data.model_filename);
        setShowUploadModal(false);
        setModelPthFile(null);
        setModelIndexFile(null);
      } else {
        const err = await res.json();
        setUploadError(err.detail || 'Fout bij uploaden van model.');
      }
    } catch (err) {
      setUploadError(`Upload mislukt: ${err.message}`);
    } finally {
      setIsUploadingModel(false);
    }
  };

  // Trigger full pipeline
  const handleGenerateCover = async () => {
    setErrorMessage('');

    // Pre-flight checks
    if (!fileAudioPath) {
      setErrorMessage('Kies eerst een audiobestand of importeer een YouTube/Spotify link.');
      return;
    }
    if (!selectedModel) {
      setErrorMessage('Selecteer of upload een RVC-stemmodel (.pth).');
      return;
    }
    if (!bsRoformerInstalled) {
      setErrorMessage('BS-RoFormer is nog niet geïnstalleerd. Open de Model Manager om hem te downloaden.');
      return;
    }
    if (!rmvpeInstalled) {
      setErrorMessage('RMVPE pitch model is nog niet geïnstalleerd. Open de Model Manager om hem te downloaden.');
      return;
    }

    setIsProcessing(true);
    setActiveStage(1);
    setStageProgressText('Audio ophalen & klaarmaken...');

    // Progress simulation stages
    const timer1 = setTimeout(() => {
      setActiveStage(2);
      setStageProgressText('Vocals & Instrumental scheiden met BS-RoFormer...');
    }, 1800);

    const timer2 = setTimeout(() => {
      setActiveStage(3);
      setStageProgressText('Zangstem transformeren via RVC v2 (RMVPE F0 pitch tuning)...');
    }, 7500);

    const timer3 = setTimeout(() => {
      setActiveStage(4);
      setStageProgressText('Vocals en instrumental mixen met volumebalans...');
    }, 15000);

    try {
      const res = await fetch('/api/song-cover/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_type: inputMode,
          audio_source: fileAudioPath,
          model_name: selectedModel,
          pitch_shift: pitchShift,
          index_rate: indexRate,
          vocal_vol: vocalVolume / 100,
          inst_vol: instVolume / 100,
        }),
      });

      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);

      if (res.ok) {
        const data = await res.json();
        setGenerationResult(data);
        setActiveStage(4);
        setStageProgressText('AI Song Cover succesvol voltooid!');
      } else {
        const err = await res.json();
        setErrorMessage(err.detail || 'Fout tijdens het verwerken van de song cover.');
        setActiveStage(0);
      }
    } catch (err) {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      setErrorMessage(`Fout tijdens generatie: ${err.message}`);
      setActiveStage(0);
    } finally {
      setIsProcessing(false);
    }
  };

  // Audio player controls
  const currentAudioUrl = generationResult
    ? activeTrack === 'mix'
      ? generationResult.mix_url
      : activeTrack === 'vocals'
      ? generationResult.vocals_url
      : generationResult.instrumental_url
    : null;

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

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
      setDuration(audioRef.current.duration || 0);
    }
  };

  const handleSeek = (e) => {
    const newTime = parseFloat(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = newTime;
      setCurrentTime(newTime);
    }
  };

  const formatTime = (secs) => {
    if (!secs || isNaN(secs)) return '0:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-900 via-purple-900 to-slate-900 text-white p-6 shadow-md border border-indigo-700/30">
        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-pink-500 to-indigo-500 flex items-center justify-center shadow-lg">
                <Music2 className="w-5 h-5 text-white" />
              </div>
              <h2 className="text-xl sm:text-2xl font-black tracking-tight">Song Cover Lab</h2>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-pink-500/20 text-pink-300 border border-pink-500/30">
                BS-RoFormer + RVC v2 RMVPE
              </span>
            </div>
            <p className="text-xs sm:text-sm text-indigo-200/80 mt-1.5 max-w-2xl">
              Transformeer elk nummer naar een realistische AI-cover. Automatische stemisolatie met Band-Split RoFormer,
              pitch-perfect RVC v2 conversie met RMVPE en dynamisch afmixen.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs px-3 py-1.5 rounded-xl bg-white/10 backdrop-blur-md border border-white/10 flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${bsRoformerInstalled && rmvpeInstalled ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse'}`}></span>
              <span className="text-[11px] font-medium text-slate-200">
                {bsRoformerInstalled && rmvpeInstalled ? 'RoFormer & RMVPE Gereed' : 'Models Configureren'}
              </span>
            </span>
          </div>
        </div>
      </div>

      {/* Error alert if prerequisite models missing */}
      {(!bsRoformerInstalled || !rmvpeInstalled) && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="text-xs flex-1">
            <p className="font-bold">Vereiste AI-modellen nog niet gedownload</p>
            <p className="text-amber-800 mt-0.5">
              Voor Song Cover Lab zijn <b>BS-RoFormer</b> (Vocal Separator) en <b>RMVPE</b> (Pitch Extractor) nodig.
            </p>
          </div>
          <button
            onClick={onOpenModelManager}
            className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold transition-colors"
          >
            Open Model Manager
          </button>
        </div>
      )}

      {/* Main Grid: 2 Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Input Selector & Voice Tuning (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Card 1: Input Selector */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <FileAudio className="w-4 h-4 text-indigo-600" />
                <h3 className="text-sm font-bold text-slate-900">1. Audio Bron Kiezen</h3>
              </div>
              {/* Toggle Mode */}
              <div className="flex bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => setInputMode('file')}
                  className={`px-3 py-1 rounded-lg transition-all ${
                    inputMode === 'file'
                      ? 'bg-white text-indigo-700 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Audio Bestand
                </button>
                <button
                  type="button"
                  onClick={() => setInputMode('url')}
                  className={`px-3 py-1 rounded-lg transition-all ${
                    inputMode === 'url'
                      ? 'bg-white text-indigo-700 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Link Importeren
                </button>
              </div>
            </div>

            {inputMode === 'file' ? (
              <div>
                <label className="border-2 border-dashed border-slate-300 hover:border-indigo-500 rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer transition-colors bg-slate-50/50 hover:bg-indigo-50/30">
                  <Upload className="w-8 h-8 text-indigo-600 mb-2" />
                  <span className="text-xs font-bold text-slate-800">
                    {selectedFile ? selectedFile.name : 'Sleep hier een audiobestand heen of klik om te kiezen'}
                  </span>
                  <span className="text-[11px] text-slate-500 mt-1">Ondersteunt MP3, WAV, FLAC, M4A tot 100MB</span>
                  <input
                    type="file"
                    accept="audio/*"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </label>
                {fileAudioPath && (
                  <p className="text-[11px] text-emerald-600 font-semibold mt-2 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Bestand geüpload en klaar voor verwerking
                  </p>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Link2 className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      placeholder="Plak YouTube of Spotify track URL..."
                      value={urlInput}
                      onChange={(e) => setUrlInput(e.target.value)}
                      className="w-full pl-9 pr-3 py-2.5 text-xs rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <button
                    onClick={handleFetchUrl}
                    disabled={isFetchingUrl || !urlInput.trim()}
                    className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-bold transition-colors flex items-center gap-1.5 whitespace-nowrap"
                  >
                    {isFetchingUrl ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Ophalen...
                      </>
                    ) : (
                      'Ophalen'
                    )}
                  </button>
                </div>
                {fetchedUrlData && (
                  <p className="text-[11px] text-emerald-600 font-semibold flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Audio opgehaald: {fetchedUrlData.filename}
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Card 2: Stem & Tuning Paneel */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Disc className="w-4 h-4 text-indigo-600" />
                <h3 className="text-sm font-bold text-slate-900">2. Stem &amp; Tuning Instellingen</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowUploadModal(true)}
                className="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 border border-slate-200 text-xs font-bold text-slate-700 transition-colors flex items-center gap-1.5"
              >
                <FileUp className="w-3.5 h-3.5 text-indigo-600" />
                Stem Uploaden (.pth)
              </button>
            </div>

            {/* RVC Model Dropdown */}
            <div>
              <label className="text-xs font-bold text-slate-700 mb-1.5 block">
                RVC v2 Stemmodel Selecteren
              </label>
              {rvcModels.length > 0 ? (
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full px-3 py-2.5 text-xs rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium"
                >
                  {rvcModels.map((m) => (
                    <option key={m.filename} value={m.filename}>
                      {m.name} ({m.version.toUpperCase()} · {m.sample_rate / 1000}kHz{m.has_index ? ' · +Index' : ''})
                    </option>
                  ))}
                </select>
              ) : (
                <div className="p-3 rounded-xl bg-slate-50 border border-dashed border-slate-200 text-xs text-slate-500 flex items-center justify-between">
                  <span>Nog geen stemmodellen in /models/rvc.</span>
                  <button
                    onClick={() => setShowUploadModal(true)}
                    className="text-xs font-bold text-indigo-600 hover:underline"
                  >
                    + Upload .pth model
                  </button>
                </div>
              )}
            </div>

            {/* Pitch Shift Slider & Presets */}
            <div className="space-y-2 pt-2 border-t border-slate-100">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-slate-700">
                  Pitch Shift (Halve Tonen): <span className="font-mono text-indigo-600">{pitchShift > 0 ? `+${pitchShift}` : pitchShift}</span>
                </label>
                <span className="text-[11px] text-slate-400">-12 tot +12</span>
              </div>
              <input
                type="range"
                min="-12"
                max="12"
                step="1"
                value={pitchShift}
                onChange={(e) => setPitchShift(parseInt(e.target.value))}
                className="w-full accent-indigo-600 cursor-pointer"
              />
              {/* Presets */}
              <div className="flex gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setPitchShift(-12)}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all border ${
                    pitchShift === -12
                      ? 'bg-indigo-600 text-white border-indigo-600'
                      : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  Vrouw → Man [-12]
                </button>
                <button
                  type="button"
                  onClick={() => setPitchShift(0)}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all border ${
                    pitchShift === 0
                      ? 'bg-indigo-600 text-white border-indigo-600'
                      : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  Neutraal [0]
                </button>
                <button
                  type="button"
                  onClick={() => setPitchShift(12)}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all border ${
                    pitchShift === 12
                      ? 'bg-indigo-600 text-white border-indigo-600'
                      : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  Man → Vrouw [+12]
                </button>
              </div>
            </div>

            {/* Index Rate Slider */}
            <div className="space-y-2 pt-2 border-t border-slate-100">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-slate-700">
                  Index Sterkte (Feature Retrieval): <span className="font-mono text-indigo-600">{indexRate.toFixed(2)}</span>
                </label>
                <span className="text-[11px] text-slate-400">0.00 tot 1.00</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={indexRate}
                onChange={(e) => setIndexRate(parseFloat(e.target.value))}
                className="w-full accent-indigo-600 cursor-pointer"
              />
              <p className="text-[10px] text-slate-400">
                Bepaalt hoeveel kenmerken van het bronmodel behouden blijven t.o.v. de originele zanger. Standaard 0.75.
              </p>
            </div>
          </div>

          {/* Card 3: Dynamic Mix Sliders */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-indigo-600" />
              <h3 className="text-sm font-bold text-slate-900">3. Dynamic Mix Sliders</h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Vocal Volume */}
              <div className="space-y-2 p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                    <Mic className="w-3.5 h-3.5 text-pink-600" /> Zang Volume
                  </label>
                  <span className="font-mono text-xs font-bold text-indigo-600">{vocalVolume}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="150"
                  step="5"
                  value={vocalVolume}
                  onChange={(e) => setVocalVolume(parseInt(e.target.value))}
                  className="w-full accent-indigo-600 cursor-pointer"
                />
              </div>

              {/* Instrumental Volume */}
              <div className="space-y-2 p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                    <Radio className="w-3.5 h-3.5 text-indigo-600" /> Instrumental Volume
                  </label>
                  <span className="font-mono text-xs font-bold text-indigo-600">{instVolume}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="150"
                  step="5"
                  value={instVolume}
                  onChange={(e) => setInstVolume(parseInt(e.target.value))}
                  className="w-full accent-indigo-600 cursor-pointer"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Generation, Progress & Audio Player (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Action Card: Genereer AI Cover */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-600" /> 4. AI Cover Produceren
            </h3>

            <button
              onClick={handleGenerateCover}
              disabled={isProcessing || !fileAudioPath || !selectedModel}
              className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-700 hover:via-purple-700 hover:to-pink-700 disabled:opacity-50 text-white font-extrabold text-sm shadow-md hover:shadow-lg transition-all duration-200 flex items-center justify-center gap-2"
            >
              {isProcessing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> Verwerken...
                </>
              ) : (
                <>
                  <Music2 className="w-4 h-4" /> Genereer AI Cover
                </>
              )}
            </button>

            {/* Error Display */}
            {errorMessage && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* 4-Stage Progress Indicator */}
            <div className="space-y-2 pt-2 border-t border-slate-100">
              <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block">
                Productiestatus
              </span>

              <div className="grid grid-cols-1 gap-2 text-xs">
                {/* Step 1 */}
                <div className={`p-2.5 rounded-xl border flex items-center gap-2.5 transition-all ${
                  activeStage === 1
                    ? 'bg-indigo-50 border-indigo-300 text-indigo-900 font-bold'
                    : activeStage > 1
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                    : 'bg-slate-50 border-slate-200 text-slate-400'
                }`}>
                  {activeStage > 1 ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : activeStage === 1 ? (
                    <RefreshCw className="w-4 h-4 text-indigo-600 animate-spin" />
                  ) : (
                    <span className="w-4 h-4 rounded-full border border-slate-300 flex items-center justify-center text-[10px]">1</span>
                  )}
                  <span>1/4 Audio Ophalen (Upload / URL)</span>
                </div>

                {/* Step 2 */}
                <div className={`p-2.5 rounded-xl border flex items-center gap-2.5 transition-all ${
                  activeStage === 2
                    ? 'bg-indigo-50 border-indigo-300 text-indigo-900 font-bold'
                    : activeStage > 2
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                    : 'bg-slate-50 border-slate-200 text-slate-400'
                }`}>
                  {activeStage > 2 ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : activeStage === 2 ? (
                    <RefreshCw className="w-4 h-4 text-indigo-600 animate-spin" />
                  ) : (
                    <span className="w-4 h-4 rounded-full border border-slate-300 flex items-center justify-center text-[10px]">2</span>
                  )}
                  <span>2/4 Vocals Scheiden (BS-RoFormer)</span>
                </div>

                {/* Step 3 */}
                <div className={`p-2.5 rounded-xl border flex items-center gap-2.5 transition-all ${
                  activeStage === 3
                    ? 'bg-indigo-50 border-indigo-300 text-indigo-900 font-bold'
                    : activeStage > 3
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                    : 'bg-slate-50 border-slate-200 text-slate-400'
                }`}>
                  {activeStage > 3 ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : activeStage === 3 ? (
                    <RefreshCw className="w-4 h-4 text-indigo-600 animate-spin" />
                  ) : (
                    <span className="w-4 h-4 rounded-full border border-slate-300 flex items-center justify-center text-[10px]">3</span>
                  )}
                  <span>3/4 Stem Converteren (RVC v2 RMVPE)</span>
                </div>

                {/* Step 4 */}
                <div className={`p-2.5 rounded-xl border flex items-center gap-2.5 transition-all ${
                  activeStage === 4 && isProcessing
                    ? 'bg-indigo-50 border-indigo-300 text-indigo-900 font-bold'
                    : activeStage === 4 && !isProcessing && generationResult
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-800 font-bold'
                    : 'bg-slate-50 border-slate-200 text-slate-400'
                }`}>
                  {activeStage === 4 && !isProcessing && generationResult ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : activeStage === 4 ? (
                    <RefreshCw className="w-4 h-4 text-indigo-600 animate-spin" />
                  ) : (
                    <span className="w-4 h-4 rounded-full border border-slate-300 flex items-center justify-center text-[10px]">4</span>
                  )}
                  <span>4/4 Afmixen (Volume Multipliers)</span>
                </div>
              </div>

              {stageProgressText && (
                <p className="text-[11px] font-medium text-indigo-600 text-center pt-1 animate-pulse">
                  {stageProgressText}
                </p>
              )}
            </div>
          </div>

          {/* Result Player Card */}
          {generationResult && (
            <div className="bg-white rounded-2xl border border-indigo-100 p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Headphones className="w-4 h-4 text-pink-600" /> Resultaat Speler
                </h4>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                  {generationResult.elapsed_seconds}s
                </span>
              </div>

              {/* Track Selector Tabs */}
              <div className="flex bg-slate-100 p-1 rounded-xl text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => {
                    setActiveTrack('mix');
                    setIsPlaying(false);
                  }}
                  className={`flex-1 py-1.5 rounded-lg transition-all ${
                    activeTrack === 'mix'
                      ? 'bg-white text-indigo-700 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Volledige Mix
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setActiveTrack('vocals');
                    setIsPlaying(false);
                  }}
                  className={`flex-1 py-1.5 rounded-lg transition-all ${
                    activeTrack === 'vocals'
                      ? 'bg-white text-pink-700 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Vocals Alleen
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setActiveTrack('inst');
                    setIsPlaying(false);
                  }}
                  className={`flex-1 py-1.5 rounded-lg transition-all ${
                    activeTrack === 'inst'
                      ? 'bg-white text-blue-700 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Instrumental
                </button>
              </div>

              {/* Native Audio Element */}
              <audio
                ref={audioRef}
                src={currentAudioUrl}
                onTimeUpdate={handleTimeUpdate}
                onEnded={() => setIsPlaying(false)}
                className="hidden"
              />

              {/* Custom Player Controls */}
              <div className="p-4 rounded-xl bg-slate-900 text-white space-y-3">
                <div className="flex items-center gap-3">
                  <button
                    onClick={togglePlay}
                    className="w-10 h-10 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white flex items-center justify-center transition-transform hover:scale-105 shadow-md"
                  >
                    {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
                  </button>
                  <div className="flex-1 space-y-1">
                    <input
                      type="range"
                      min="0"
                      max={duration || 100}
                      value={currentTime}
                      onChange={handleSeek}
                      className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-pink-500"
                    />
                    <div className="flex justify-between text-[10px] font-mono text-slate-400">
                      <span>{formatTime(currentTime)}</span>
                      <span>{formatTime(duration)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* 3 Download Buttons */}
              <div className="grid grid-cols-1 gap-2 pt-2 border-t border-slate-100">
                <a
                  href={generationResult.mix_url}
                  download="cover_full_mix.wav"
                  className="w-full py-2 px-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition-colors flex items-center justify-center gap-2 shadow-xs"
                >
                  <Download className="w-3.5 h-3.5" /> Download Volledige Mix
                </a>

                <div className="grid grid-cols-2 gap-2">
                  <a
                    href={generationResult.vocals_url}
                    download="cover_vocals_only.wav"
                    className="py-2 px-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold transition-colors flex items-center justify-center gap-1.5 border border-slate-200"
                  >
                    <Download className="w-3.5 h-3.5 text-pink-600" /> Vocals Alleen
                  </a>
                  <a
                    href={generationResult.instrumental_url}
                    download="cover_instrumental_only.wav"
                    className="py-2 px-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold transition-colors flex items-center justify-center gap-1.5 border border-slate-200"
                  >
                    <Download className="w-3.5 h-3.5 text-indigo-600" /> Instrumental Alleen
                  </a>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Upload Model Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <FileUp className="w-5 h-5 text-indigo-600" /> RVC Stemmodel Toevoegen
              </h3>
              <button
                onClick={() => setShowUploadModal(false)}
                className="w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-700"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleUploadRvcModel} className="space-y-4">
              {/* .pth file input */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700">
                  Stemmodel Bestand (*.pth) <span className="text-rose-500">*</span>
                </label>
                <input
                  type="file"
                  accept=".pth"
                  required
                  onChange={(e) => setModelPthFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-slate-500 file:mr-3 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 cursor-pointer border border-slate-200 rounded-xl p-1"
                />
              </div>

              {/* .index file input */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700">
                  Feature Retrieval Index (*.index) <span className="text-slate-400 font-normal">(Optioneel)</span>
                </label>
                <input
                  type="file"
                  accept=".index"
                  onChange={(e) => setModelIndexFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-slate-500 file:mr-3 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200 cursor-pointer border border-slate-200 rounded-xl p-1"
                />
              </div>

              {uploadError && (
                <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">
                  {uploadError}
                </div>
              )}

              <div className="flex gap-2 justify-end pt-2">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2 rounded-xl border border-slate-200 hover:bg-slate-100 text-xs font-semibold text-slate-700"
                >
                  Annuleren
                </button>
                <button
                  type="submit"
                  disabled={isUploadingModel || !modelPthFile}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-bold transition-colors flex items-center gap-1.5"
                >
                  {isUploadingModel ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Uploaden...
                    </>
                  ) : (
                    'Opslaan in /models/rvc'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
