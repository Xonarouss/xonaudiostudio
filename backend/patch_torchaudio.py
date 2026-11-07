"""
XonAudio Studio - Torchaudio Soundfile Fallback Patch
Ensures reliable audio I/O using soundfile instead of the broken torchcodec on Windows.
"""
import os
import torch
import torchaudio
import soundfile as sf

_orig_load = getattr(torchaudio, "_orig_load", torchaudio.load)
_orig_save = getattr(torchaudio, "_orig_save", torchaudio.save)

def _soundfile_load(uri, frame_offset=0, num_frames=-1, normalize=True, channels_first=True, format=None, buffer_size=4096, backend=None):
    try:
        data, sr = sf.read(
            uri,
            start=frame_offset,
            stop=(frame_offset + num_frames) if num_frames > 0 else None,
            dtype="float32"
        )
        tensor = torch.from_numpy(data)
        if tensor.ndim == 1:
            tensor = tensor.unsqueeze(0)
        elif channels_first:
            tensor = tensor.t()
        return tensor, sr
    except Exception:
        return _orig_load(uri, frame_offset=frame_offset, num_frames=num_frames, normalize=normalize, channels_first=channels_first, format=format, buffer_size=buffer_size, backend=backend)

def _soundfile_save(uri, src, sample_rate, channels_first=True, format=None, encoding=None, bits_per_sample=None, buffer_size=4096, backend=None, compression=None):
    try:
        data = src.detach().cpu().numpy()
        if channels_first and data.ndim == 2:
            data = data.T
        sf.write(uri, data, sample_rate)
    except Exception:
        _orig_save(uri, src, sample_rate, channels_first=channels_first, format=format, encoding=encoding, bits_per_sample=bits_per_sample, buffer_size=buffer_size, backend=backend, compression=compression)

def apply_torchaudio_patch():
    torchaudio.load = _soundfile_load
    torchaudio.save = _soundfile_save

apply_torchaudio_patch()
