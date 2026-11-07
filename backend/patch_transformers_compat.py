"""
Bulletproof Compatibility Shim for Coqui TTS (0.22.x) with transformers >= 5.0
and modern huggingface_hub.

transformers 5.x uses `transformers.utils.import_utils._LazyModule` as its
module class. Submodules and lazy imports re-instantiate `_LazyModule`, wiping
out any standard module-level monkey-patches.

By monkey-patching `_LazyModule.__getattr__`, any symbol request for deprecated /
removed transformers classes (like BeamSearchScorer, ConstrainedBeamSearchScorer,
DisjunctiveConstraint, PhrasalConstraint, Constraint) is intercepted dynamically
and returned across all module instances.
"""

import sys
import types
import logging

logger = logging.getLogger(__name__)

def _apply_patches():
    try:
        from transformers.utils.import_utils import _LazyModule

        _orig_getattr = _LazyModule.__getattr__

        # 1. Stubs for removed classes
        class _ConstraintStub:
            def __init__(self, *args, **kwargs):
                pass

        class _DisjunctiveConstraintStub(_ConstraintStub):
            pass

        class _PhrasalConstraintStub(_ConstraintStub):
            pass

        class _BeamSearchScorerStub:
            def __init__(self, *args, **kwargs):
                pass

        class _BeamSampleScorerStub(_BeamSearchScorerStub):
            pass

        class _ConstrainedBeamSearchScorerStub(_BeamSearchScorerStub):
            pass

        FALLBACK_SYMBOLS = {
            "BeamSearchScorer": _BeamSearchScorerStub,
            "BeamSampleScorer": _BeamSampleScorerStub,
            "ConstrainedBeamSearchScorer": _ConstrainedBeamSearchScorerStub,
            "Constraint": _ConstraintStub,
            "DisjunctiveConstraint": _DisjunctiveConstraintStub,
            "PhrasalConstraint": _PhrasalConstraintStub,
        }

        # Handle CausalLMOutputWithCrossAttentions if needed
        try:
            import transformers.modeling_outputs as mo
            if hasattr(mo, "CausalLMOutputWithCrossAttentions"):
                FALLBACK_SYMBOLS["CausalLMOutputWithCrossAttentions"] = mo.CausalLMOutputWithCrossAttentions
        except Exception:
            pass

        # Handle LogitsWarper alias
        try:
            import transformers.generation.logits_process as gen_lp
            if hasattr(gen_lp, "LogitsProcessor"):
                FALLBACK_SYMBOLS["LogitsWarper"] = gen_lp.LogitsProcessor
                gen_lp.LogitsWarper = gen_lp.LogitsProcessor
        except Exception:
            pass

        def _patched_getattr(self, name: str):
            if name in FALLBACK_SYMBOLS:
                return FALLBACK_SYMBOLS[name]
            return _orig_getattr(self, name)

        _LazyModule.__getattr__ = _patched_getattr

        # 2. Patch generation subpackage
        import transformers.generation as gen
        for k, v in FALLBACK_SYMBOLS.items():
            if not hasattr(gen, k):
                setattr(gen, k, v)

        # 3. Create dummy constraints module so `import transformers.generation.constraints` works
        if "transformers.generation.constraints" not in sys.modules:
            cmod = types.ModuleType("transformers.generation.constraints")
            cmod.Constraint = _ConstraintStub
            cmod.DisjunctiveConstraint = _DisjunctiveConstraintStub
            cmod.PhrasalConstraint = _PhrasalConstraintStub
            sys.modules["transformers.generation.constraints"] = cmod
            gen.constraints = cmod

        # 4. Create dummy beam_search module so `import transformers.generation.beam_search` works
        if "transformers.generation.beam_search" not in sys.modules:
            bmod = types.ModuleType("transformers.generation.beam_search")
            bmod.BeamSearchScorer = _BeamSearchScorerStub
            bmod.BeamSampleScorer = _BeamSampleScorerStub
            bmod.ConstrainedBeamSearchScorer = _ConstrainedBeamSearchScorerStub
            sys.modules["transformers.generation.beam_search"] = bmod
            gen.beam_search = bmod

        # 5. Patch transformers.generation.utils output aliases
        import transformers.generation.utils as gu
        decoder_out = getattr(gu, "GenerateDecoderOnlyOutput", None)
        beam_out = getattr(gu, "GenerateBeamDecoderOnlyOutput", decoder_out)

        gu.SampleOutput = decoder_out
        gu.BeamSearchOutput = beam_out
        gu.BeamSampleOutput = beam_out
        gu.GreedySearchOutput = decoder_out
        gu.ContrastiveSearchOutput = decoder_out

        FALLBACK_SYMBOLS["SampleOutput"] = decoder_out
        FALLBACK_SYMBOLS["BeamSearchOutput"] = beam_out
        FALLBACK_SYMBOLS["BeamSampleOutput"] = beam_out

        # 6. huggingface_hub StrictDataclassClassValidationError
        try:
            import huggingface_hub.errors as hf_errors
            if not hasattr(hf_errors, "StrictDataclassClassValidationError"):
                class _StrictDataclassClassValidationError(Exception):
                    pass
                hf_errors.StrictDataclassClassValidationError = _StrictDataclassClassValidationError
                import huggingface_hub as hfhub
                hfhub.StrictDataclassClassValidationError = _StrictDataclassClassValidationError
        except Exception:
            pass

        logger.info("[patch_transformers_compat] All transformers 5.x patches applied.")
    except Exception as e:
        logger.warning(f"[patch_transformers_compat] Warning: {e}")

_apply_patches()
