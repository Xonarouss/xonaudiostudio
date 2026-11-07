import os
import gc
import re
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
                torch_dtype=dtype,
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
                        torch_dtype=torch.float32,
                        low_cpu_mem_usage=True
                    ).to("cpu")
                    self.is_loaded = True
                    print("[LlamaEngine] Llama loaded on CPU successfully!")
                    return
                except Exception as e_cpu:
                    print(f"[LlamaEngine] Could not load Llama on CPU: {e_cpu}")
            self.is_loaded = False
            print(f"[LlamaEngine] Note: Llama neural weights not yet loaded ({e}). Using expert acoustic rule engine.")

    def enhance_prompt(self, user_input: str, mode: str = "sfx") -> str:
        """
        Enhances user's simple prompt into a professional, cinematic audio prompt.
        Uses neural Llama if loaded, or expert acoustic prompt heuristics as fallback.
        """
        user_input = user_input.strip()
        if not user_input:
            return user_input

        # If neural model is loaded, use Llama generation
        if self.is_loaded and self.model is not None and self.tokenizer is not None:
            try:
                if mode == "sfx":
                    system_msg = (
                        "You are an expert Hollywood sound designer and Foley artist for Stable Audio Open. "
                        "Transform the user's idea into a single highly-detailed, acoustic-rich prompt. "
                        "Include environment, materials, dynamics, reverberation, and quality terms. "
                        "OUTPUT ONLY THE ENHANCED PROMPT, no introduction, no quotes."
                    )
                else:
                    system_msg = (
                        "You are a master voice director for neural text-to-speech (F5-TTS). "
                        "Refine the script for maximum natural cadence, emotional resonance, and clear punctuation. "
                        "OUTPUT ONLY THE REFINED SCRIPT, no commentary."
                    )

                messages = [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": f"Enhance this: {user_input}"}
                ]

                inputs = self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=True,
                    add_generation_prompt=True,
                    return_tensors="pt"
                ).to(self.device)

                with torch.no_grad():
                    outputs = self.model.generate(
                        inputs,
                        max_new_tokens=90,
                        temperature=0.7,
                        do_sample=True,
                        pad_token_id=self.tokenizer.eos_token_id
                    )

                response = self.tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True).strip()
                # Clean up quotes
                response = re.sub(r'^["\']|["\']$', '', response)
                if len(response) > 10:
                    return response
            except Exception as e:
                print(f"[LlamaEngine] Neural inference note: {e}")

        # High-Quality Expert Acoustic Heuristics (Instant & Reliable Fallback)
        if mode == "sfx":
            lower = user_input.lower()
            enhancements = []
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
            # Voice refinement: adds expressive cadence
            if not user_input.endswith(('.', '!', '?')):
                user_input += '.'
            return user_input

    def chat(self, user_message: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Conversational assistant for creative sound design, scriptwriting, and studio advice.
        Raises an error if the model is not installed.
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
                    "Keep responses professional, friendly, and structured."
                )

                messages = [{"role": "system", "content": system_prompt}]
                if history:
                    for h in history[-4:]: # Keep recent context
                        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
                messages.append({"role": "user", "content": user_message})

                inputs = self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=True,
                    add_generation_prompt=True,
                    return_tensors="pt"
                ).to(self.device)

                with torch.no_grad():
                    outputs = self.model.generate(
                        inputs,
                        max_new_tokens=256,
                        temperature=0.7,
                        do_sample=True,
                        pad_token_id=self.tokenizer.eos_token_id
                    )

                response = self.tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True).strip()
                return response
            except Exception as e:
                print(f"[LlamaEngine] Chat generation error: {e}")

        # Intelligent Fallback Advisor
        lower = user_message.lower()
        if "f5" in lower or "voice" in lower or "clone" in lower:
            return (
                "🎙️ **Voice Lab Tips:**\n"
                "• **Reference Audio:** 5–10 seconds of clear, dry speech (no background music) gives the best similarity.\n"
                "• **Reference Transcript:** Entering what the speaker says in the audio eliminates accent mismatches.\n"
                "• **NFE Steps:** 32 steps is the sweet spot for crisp flow-matching on your GPU.\n\n"
                "Would you like me to write or refine a script for you?"
            )
        elif "sound" in lower or "sfx" in lower or "foley" in lower or "prompt" in lower:
            return (
                "🎛️ **Sound Studio Tips:**\n"
                "• **Acoustic Descriptions:** Always specify materials (*metal, gravel, glass*) and acoustics (*reverberant hall, close-up, outdoor*).\n"
                "• **Duration:** Match your duration to the natural sound (e.g. 3–5s for punches/lasers, 15–30s for ambient weather).\n"
                "• **Magic Wand (🪄):** Type a basic keyword and click the magic wand to let me expand it into a Hollywood-grade prompt!"
            )
        else:
            return (
                f"Hello! I am your **XonAudio AI Assistant** powered by local Llama.\n\n"
                f"You asked: *\"{user_message}\"*\n\n"
                f"I can help you:\n"
                f"1. 🪄 **Craft & Enhance Prompts** for Foley, ambient drones, and sound effects.\n"
                f"2. 🗣️ **Refine Scripts** for F5-TTS voice cloning with natural cadence.\n"
                f"3. 🎚️ **Suggest Optimal Settings** for CFG scale, NFE steps, and durations.\n\n"
                f"What sound or voice are you looking to create?"
            )

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

