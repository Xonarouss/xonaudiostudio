import os
import gc
import re
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional
import torch

BASE_DIR = Path(__file__).resolve().parent.parent
LLAMA_DIR = BASE_DIR / "models" / "llama"
LLAMA_DIR.mkdir(parents=True, exist_ok=True)

class LlamaEngine:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        print(f"[LlamaEngine] Initialized on device: {self.device}")

    def is_installed(self) -> bool:
        """Checks if Llama weights exist locally in models/llama."""
        if not LLAMA_DIR.exists():
            return False
        files = list(LLAMA_DIR.glob("**/*.safetensors")) + list(LLAMA_DIR.glob("**/*.bin")) + list(LLAMA_DIR.glob("**/*.gguf"))
        return len(files) > 0

    def load_model(self):
        """Loads Llama 3 model into VRAM/RAM."""
        if self.is_loaded and self.model is not None:
            return

        print(f"[LlamaEngine] Loading Llama model on {self.device}...")
        from transformers import AutoTokenizer, AutoModelForCausalLM

        model_path = str(LLAMA_DIR) if self.is_installed() else "unsloth/Llama-3.2-1B-Instruct"

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            dtype = torch.float16 if self.device == "cuda" else torch.float32

            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                dtype=dtype,          # NOTE: use 'dtype=', NOT 'torch_dtype=' (deprecated)
                low_cpu_mem_usage=True
            ).to(self.device)

            self.is_loaded = True
            print("[LlamaEngine] Llama model loaded successfully into memory!")
        except Exception as e:
            if self.device == "cuda":
                print(f"[LlamaEngine] CUDA error loading Llama ({e}). Falling back to CPU...")
                try:
                    self.device = "cpu"
                    self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                    self.model = AutoModelForCausalLM.from_pretrained(
                        model_path,
                        dtype=torch.float32,
                        low_cpu_mem_usage=True
                    ).to("cpu")
                    self.is_loaded = True
                    print("[LlamaEngine] Llama loaded on CPU successfully!")
                    return
                except Exception as e_cpu:
                    print(f"[LlamaEngine] Could not load Llama on CPU: {e_cpu}")
                    traceback.print_exc()
            self.is_loaded = False
            print(f"[LlamaEngine] Failed to load Llama: {e}")
            traceback.print_exc()

    def _run_inference(self, messages: list, max_new_tokens: int = 256) -> str:
        """
        Core inference helper — handles BatchEncoding vs plain tensor correctly.
        apply_chat_template returns a BatchEncoding on newer transformers, not a plain tensor.
        """
        encoded = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt"
        )

        # Handle both BatchEncoding and plain tensor returns
        if hasattr(encoded, "input_ids"):
            input_ids = encoded.input_ids.to(self.device)
            # Also pass attention_mask if available to suppress warnings
            attention_mask = encoded.attention_mask.to(self.device) if hasattr(encoded, "attention_mask") else None
        else:
            input_ids = encoded.to(self.device)
            attention_mask = None

        input_len = input_ids.shape[1]

        generate_kwargs = dict(
            input_ids=input_ids,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            pad_token_id=self.tokenizer.eos_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
        )
        if attention_mask is not None:
            generate_kwargs["attention_mask"] = attention_mask

        with torch.no_grad():
            output_ids = self.model.generate(**generate_kwargs)

        # Decode only the new tokens (skip prompt)
        response = self.tokenizer.decode(
            output_ids[0][input_len:],
            skip_special_tokens=True
        ).strip()
        return response

    def enhance_prompt(self, user_input: str, mode: str = "sfx") -> str:
        """
        Enhances user's simple prompt into a professional, cinematic audio prompt.
        Uses neural Llama if loaded, or expert acoustic prompt heuristics as fallback.
        """
        user_input = user_input.strip()
        if not user_input:
            return user_input

        # Load model on demand if installed but not yet loaded
        from models_manager import is_llama_installed
        if is_llama_installed() and not self.is_loaded:
            try:
                self.load_model()
            except Exception as _le:
                print(f"[LlamaEngine] Could not auto-load for enhance: {_le}")

        # If neural model is loaded, use Llama generation
        if self.is_loaded and self.model is not None and self.tokenizer is not None:
            try:
                if mode == "sfx":
                    system_msg = (
                        "You are an expert Hollywood sound designer and Foley artist for Stable Audio Open. "
                        "Transform the user's idea into a single highly-detailed, acoustic-rich prompt. "
                        "Include environment, materials, dynamics, reverberation, and quality terms. "
                        "OUTPUT ONLY THE ENHANCED PROMPT, no introduction, no quotes, no extra lines."
                    )
                else:
                    system_msg = (
                        "You are a master voice director for neural text-to-speech (F5-TTS). "
                        "Refine the script for maximum natural cadence, emotional resonance, and clear punctuation. "
                        "OUTPUT ONLY THE REFINED SCRIPT, nothing else."
                    )

                messages = [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": f"Enhance this: {user_input}"}
                ]

                response = self._run_inference(messages, max_new_tokens=200)
                response = re.sub(r'^["\']|["\']$', '', response).strip()
                if response:
                    return response
            except Exception as e:
                print(f"[LlamaEngine] Neural enhance error: {e}")
                traceback.print_exc()

        # High-Quality Expert Acoustic Heuristics (Instant & Reliable Fallback)
        if mode == "sfx":
            lower = user_input.lower()
            if any(w in lower for w in ["explosion", "blast", "bomb", "detonate"]):
                return f"Massive cinematic {user_input}, deep sub-bass shockwave rumbling through the air, reverberating debris falling onto concrete, intense Hollywood trailer impact, 44.1kHz stereo"
            elif any(w in lower for w in ["rain", "storm", "thunder", "water"]):
                return f"Ultra-detailed ambient recording of {user_input}, crisp droplets hitting leaves and asphalt, distant rolling thunder clap, gentle wind acoustics, immersive stereo foley"
            elif any(w in lower for w in ["laser", "sci-fi", "gun", "weapon", "blaster", "space"]):
                return f"Futuristic high-energy sci-fi {user_input}, electromagnetic plasma charging up, crisp mechanical servo clicks, heavy laser discharge with stereo delay echo"
            elif any(w in lower for w in ["car", "engine", "motor", "drive", "vehicle"]):
                return f"High-fidelity mechanical foley of {user_input}, aggressive engine roar, exhaust rumble, tires gripping pavement, wide stereo spatial acoustics"
            elif any(w in lower for w in ["footstep", "walk", "run", "step"]):
                return f"Crisp close-up foley of {user_input}, natural weight and cadence, detailed surface texture, realistic acoustic room reflections, clean studio recording"
            else:
                return f"Cinematic high-definition {user_input}, rich spatial reverberation, tactile acoustic foley, dynamic frequency response, 44.1kHz high-resolution stereo"
        else:
            if not user_input.endswith(('.', '!', '?')):
                user_input += '.'
            return user_input

    def chat(self, user_message: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Conversational assistant for creative sound design, scriptwriting, and studio advice.
        Raises RuntimeError if the model is not installed.
        """
        user_message = user_message.strip()
        if not user_message:
            return "How can I assist you with your audio production today?"

        from models_manager import is_llama_installed
        if not is_llama_installed():
            raise RuntimeError("Llama 3 model is not installed. Please download Llama 3 in Model Manager or run Start_AudioStudio.bat.")

        if not self.is_loaded or self.model is None:
            self.load_model()

        if self.is_loaded and self.model is not None and self.tokenizer is not None:
            try:
                system_prompt = (
                    "You are the XonAudio Studio AI Assistant by Xonarous Inc. "
                    "You are an expert sound designer, Foley artist, and voice director. "
                    "Provide concise, highly actionable advice on audio generation, prompts, voice cloning, and audio acoustics. "
                    "Keep responses professional, friendly, and structured. Max 3 paragraphs."
                )

                messages = [{"role": "system", "content": system_prompt}]
                if history:
                    for h in history[-4:]:
                        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
                messages.append({"role": "user", "content": user_message})

                response = self._run_inference(messages, max_new_tokens=256)
                if response:
                    return response
                raise RuntimeError("Empty response from model")

            except Exception as e:
                print(f"[LlamaEngine] Chat generation error: {e}")
                traceback.print_exc()
                raise RuntimeError(f"Llama inference failed: {e}")

        raise RuntimeError("Llama model could not be loaded. Check the backend logs for details.")

    def unload(self):
        """Frees Llama from VRAM."""
        print("[LlamaEngine] Unloading Llama model from VRAM...")
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

llama_engine = LlamaEngine()
