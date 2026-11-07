import re
from typing import List, Tuple

# Regex patterns
BRACKET_CONTENT_PATTERN = re.compile(r"\[([^\]]*)\]|\(([^\)]*)\)|\{([^\}]*)\}")

def extract_tags(text: str) -> List[str]:
    """Returns list of tags found in text, lowercased without brackets."""
    if not text:
        return []
    matches = BRACKET_CONTENT_PATTERN.findall(text)
    tags = []
    for m in matches:
        tag = (m[0] or m[1] or m[2]).strip().lower()
        if tag:
            tags.append(tag)
    return tags

def has_emotion_tags(text: str) -> bool:
    """Returns True if text contains emotion or action tags."""
    return len(extract_tags(text)) > 0

def should_route_to_fish(text: str) -> bool:
    """Returns True if text contains expressive cues best suited for high-quality cloning."""
    tags = extract_tags(text)
    for tag in tags:
        if any(w in tag for w in ["laugh", "whisper", "sigh", "cry", "scream", "angry", "fear", "happy"]):
            return True
    return False

def clean_speech_text(text: str) -> str:
    """
    Cleans text for neural TTS models so that:
    1. Laughter tags [laugh], [laughs] are converted to natural 'Haha!'
    2. Screams [screaming], [scream] are converted to exclamation marks
    3. Sighs and pauses [sigh], [pause] are converted to natural speech pause ellipsis '...'
    4. ALL other brackets AND their interior text (e.g. stage directions like
       '(speaking with fear)', '[whisper]', '[crying]') are completely REMOVED.
    5. No model will ever read 'bracket laugh bracket', 'screaming', or stage directions aloud!
    """
    if not text:
        return ""

    processed = text

    # 1. Convert laughter tags to natural laugh interjection
    processed = re.sub(r"\[(laugh|laughs|laughter|chuckle|giggle|haha)\]", " Haha! ", processed, flags=re.IGNORECASE)
    processed = re.sub(r"\((laugh|laughs|laughter|chuckle|giggle|haha)\)", " Haha! ", processed, flags=re.IGNORECASE)

    # 2. Convert sigh & pause to natural speech pauses
    processed = re.sub(r"\[(sigh|sighs|sighing|pause)\]", "... ", processed, flags=re.IGNORECASE)
    processed = re.sub(r"\((sigh|sighs|sighing|pause)\)", "... ", processed, flags=re.IGNORECASE)

    # 3. Convert scream to exclamation mark
    processed = re.sub(r"\[(scream|screams|screaming)\]", "! ", processed, flags=re.IGNORECASE)
    processed = re.sub(r"\((scream|screams|screaming)\)", "! ", processed, flags=re.IGNORECASE)

    # 4. Remove ALL remaining bracketed tags and stage directions completely (including contents)
    processed = re.sub(r"\[[^\]]*\]", "", processed)
    processed = re.sub(r"\([^\)]*\)", "", processed)
    processed = re.sub(r"\{[^\}]*\}", "", processed)

    # 5. Remove any stray bracket characters
    processed = re.sub(r"[\[\]\(\)\{\}<>]", "", processed)

    # 6. Preserve natural pause ellipsis (...) while cleaning duplicate punctuation
    processed = re.sub(r"\.{4,}", "...", processed)
    processed = re.sub(r"(?:\s*\.\.\.\s*)+", "... ", processed)
    processed = re.sub(r"(!\s*)+", "! ", processed)
    processed = re.sub(r"(\?\s*)+", "? ", processed)
    processed = re.sub(r"(,\s*)+", ", ", processed)
    processed = re.sub(r"\s+([,.\?!;:])", r"\1", processed)  # Remove spaces before punctuation
    processed = re.sub(r"^\s*([!?,;:])", "", processed)  # Remove stray leading punctuation

    # 7. Clean whitespace
    processed = re.sub(r"\s+", " ", processed).strip()

    return processed

def preprocess_for_f5tts(text: str) -> str:
    return clean_speech_text(text)

def preprocess_for_xtts(text: str) -> str:
    return clean_speech_text(text)

def preprocess_for_fish(text: str) -> str:
    return clean_speech_text(text)

def preprocess_text_for_engine(text: str, engine: str) -> Tuple[str, List[str]]:
    detected_tags = extract_tags(text)
    cleaned = clean_speech_text(text)
    return cleaned, detected_tags
