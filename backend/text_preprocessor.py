import re
from typing import List, Dict, Any, Tuple

# Supported Fish Speech tokens
FISH_CANONICAL_TAGS = {
    "laugh": "[laugh]",
    "laughs": "[laugh]",
    "laughter": "[laugh]",
    "chuckle": "[laugh]",
    "giggle": "[laugh]",
    "snicker": "[snicker]",
    "sigh": "[sigh]",
    "sighs": "[sigh]",
    "gasp": "[gasp]",
    "gasps": "[gasp]",
    "whisper": "[whisper]",
    "whispers": "[whisper]",
    "whispering": "[whisper]",
    "scream": "[screaming]",
    "screams": "[screaming]",
    "screaming": "[screaming]",
    "cry": "[crying]",
    "cries": "[crying]",
    "crying": "[crying]",
    "weeping": "[crying]",
    "yawn": "[yawn]",
    "yawns": "[yawn]",
    "groan": "[groan]",
    "groans": "[groan]",
    "cough": "[cough]",
    "coughs": "[cough]",
}

# Regex to match any bracketed tag: [tag] or (tag)
TAG_PATTERN = re.compile(r"\[([a-zA-Z0-9_\-\s]+)\]|\(([a-zA-Z0-9_\-\s]+)\)")
SQUARE_BRACKET_PATTERN = re.compile(r"\[([a-zA-Z0-9_\-\s]+)\]")

def extract_tags(text: str) -> List[str]:
    """Returns list of tags found in text, lowercased without brackets."""
    if not text:
        return []
    matches = TAG_PATTERN.findall(text)
    tags = []
    for m in matches:
        tag = (m[0] or m[1]).strip().lower()
        if tag:
            tags.append(tag)
    return tags

def has_emotion_tags(text: str) -> bool:
    """Returns True if text contains emotion or action tags."""
    return len(extract_tags(text)) > 0

def should_route_to_fish(text: str) -> bool:
    """Returns True if text contains emotion tags that Fish Speech supports natively."""
    tags = extract_tags(text)
    for tag in tags:
        if tag in FISH_CANONICAL_TAGS or tag in [
            "angry", "sad", "happy", "excited", "whisper", "screams", "laughs", "sighs"
        ]:
            return True
    return False

def preprocess_for_fish(text: str) -> str:
    """
    Normalizes emotion tags for Fish Speech 1.5.
    Converts synonyms like [laughs] -> [laugh], [screams] -> [screaming],
    and removes unsupported tags/brackets so they aren't vocalized as 'bracket tag bracket'.
    """
    if not text:
        return ""

    def replace_fish_tag(match):
        raw_tag = match.group(1).strip().lower()
        if raw_tag in FISH_CANONICAL_TAGS:
            return f" {FISH_CANONICAL_TAGS[raw_tag]} "
        # If tag is generic descriptive emotion (e.g. [angry], [sad]) that Fish does not have
        # a special token for, strip brackets so the model does not read 'bracket angry bracket'
        return ""

    processed = SQUARE_BRACKET_PATTERN.sub(replace_fish_tag, text)
    # Clean whitespace and punctuation
    processed = re.sub(r"\s+([,.\?!;:])", r"\1", processed)
    processed = re.sub(r"\s+", " ", processed).strip()
    return processed

def preprocess_for_f5tts(text: str) -> str:
    """
    Strips all bracketed emotion tags from text for F5-TTS so that
    bracket tokens like [laugh] or [whisper] are NEVER read aloud as words
    like 'bracket laughs bracket'.
    """
    if not text:
        return ""

    # Remove all square brackets and parentheses tags
    processed = TAG_PATTERN.sub("", text)
    # Also strip any stray brackets
    processed = re.sub(r"[\[\]\(\)\{\}]", "", processed)
    # Clean up duplicate punctuation and whitespace
    processed = re.sub(r"\s+([,.\?!;:])", r"\1", processed)
    processed = re.sub(r"([,.\?!;:])\s*([,.\?!;:])+", r"\1", processed)
    processed = re.sub(r"\s+", " ", processed).strip()
    return processed

def preprocess_for_xtts(text: str) -> str:
    """
    Strips all bracketed tags for XTTS-v2 so brackets are never pronounced.
    """
    if not text:
        return ""
    processed = TAG_PATTERN.sub("", text)
    processed = re.sub(r"[\[\]\(\)\{\}]", "", processed)
    processed = re.sub(r"\s+([,.\?!;:])", r"\1", processed)
    processed = re.sub(r"([,.\?!;:])\s*([,.\?!;:])+", r"\1", processed)
    processed = re.sub(r"\s+", " ", processed).strip()
    return processed

def preprocess_text_for_engine(text: str, engine: str) -> Tuple[str, List[str]]:
    """
    Routes and cleans text for the selected engine.
    Returns (cleaned_text, detected_tags).
    """
    detected_tags = extract_tags(text)
    engine_lower = (engine or "f5_tts").lower()

    if "fish" in engine_lower:
        cleaned = preprocess_for_fish(text)
    elif "xtts" in engine_lower:
        cleaned = preprocess_for_xtts(text)
    else:  # f5_tts or default
        cleaned = preprocess_for_f5tts(text)

    return cleaned, detected_tags
