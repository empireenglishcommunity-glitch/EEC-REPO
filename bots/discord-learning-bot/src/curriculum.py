"""Empire English Community Bot — Curriculum Data Loader.

Loads curated L0 curriculum from data/ and content/ JSON files.
Provides structured access to vocabulary, speaking missions, writing prompts,
accent drills, and grammar patterns per week and day.

This module bridges Phase 2 (curated content) with Phase 3 (bot delivery).
"""
import json
import logging
import datetime
from pathlib import Path
from typing import Optional

from . import config

logger = logging.getLogger("empire-bot.curriculum")

# ============================================================
#  DATA DIRECTORIES
# ============================================================
DATA_DIR = config.BASE_DIR / "data"
CONTENT_DIR = config.BASE_DIR / "content"

# ============================================================
#  CACHE (loaded once at startup)
# ============================================================
_weekly_data: dict = {}  # {1: {...}, 2: {...}, ...}
_accent_data: dict = {}  # {1: {...}, 2: {...}, ...}
_grammar_data: dict = {}  # {1: {...}, 2: {...}, ...}


def load_all():
    """Load all curriculum data from JSON files. Call once at bot startup."""
    global _weekly_data, _accent_data, _grammar_data

    # Load weekly data for ALL levels (L0-L3)
    level_weeks = {"L0": 8, "L1": 10, "L2": 12, "L3": 8}
    for level, max_week in level_weeks.items():
        for week in range(1, max_week + 1):
            path = DATA_DIR / f"{level.lower()}_week{week}.json"
            if path.exists():
                try:
                    with open(path, encoding="utf-8") as f:
                        key = f"{level}_{week}"
                        _weekly_data[key] = json.load(f)
                except Exception as e:
                    logger.error(f"Failed to load {path}: {e}")

    # Count loaded
    l0_count = sum(1 for k in _weekly_data if k.startswith("L0_"))
    l1_count = sum(1 for k in _weekly_data if k.startswith("L1_"))
    l2_count = sum(1 for k in _weekly_data if k.startswith("L2_"))
    l3_count = sum(1 for k in _weekly_data if k.startswith("L3_"))
    logger.info(f"Weekly data: L0={l0_count}, L1={l1_count}, L2={l2_count}, L3={l3_count}")

    # Load accent drills (L0 only for now)
    accent_dir = CONTENT_DIR / "l0" / "accent"
    if accent_dir.exists():
        accent_files = sorted(accent_dir.glob("week*.json"))
        for i, path in enumerate(accent_files, 1):
            try:
                with open(path, encoding="utf-8") as f:
                    _accent_data[i] = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load {path}: {e}")
        logger.info(f"Loaded {len(_accent_data)} accent drill files")

    # Load grammar patterns (L0 only for now)
    grammar_dir = CONTENT_DIR / "l0" / "grammar"
    if grammar_dir.exists():
        grammar_files = sorted([f for f in grammar_dir.glob("week*.json")])
        for i, path in enumerate(grammar_files, 1):
            try:
                with open(path, encoding="utf-8") as f:
                    _grammar_data[i] = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load {path}: {e}")
        logger.info(f"Loaded {len(_grammar_data)} grammar pattern files")

    total_vocab = sum(len(w.get("vocabulary", [])) for w in _weekly_data.values())
    logger.info(f"Curriculum loaded: {len(_weekly_data)} total weeks, {total_vocab} vocab words, {len(_accent_data)} accent, {len(_grammar_data)} grammar")


# ============================================================
#  VOCABULARY ACCESS
# ============================================================

def get_vocabulary_for_week(week: int, level: str = "L0") -> list[dict]:
    """Get the vocabulary words for a given week and level.
    Each word: {word, pronunciation, arabic, pos}
    """
    key = f"{level}_{week}"
    data = _weekly_data.get(key, {})
    return data.get("vocabulary", [])


def get_vocabulary_for_day(week: int, day_index: int, level: str = "L0") -> list[dict]:
    """Get the 8 vocabulary words for a specific day (0=Saturday, 6=Friday).
    Splits the weekly words into 7 days of 8 words each.
    """
    all_words = get_vocabulary_for_week(week, level)
    if not all_words:
        return []
    day_index = day_index % 7
    words_per_day = max(1, len(all_words) // 7)
    start = day_index * words_per_day
    end = start + words_per_day
    return all_words[start:end]


def get_quiz_words(week: int, count: int = 10, level: str = "L0") -> list[dict]:
    """Get random words from this week + previous weeks for quiz verification."""
    import random
    all_words = []
    # Current week + last 2 weeks for spaced repetition
    for w in range(max(1, week - 2), week + 1):
        all_words.extend(get_vocabulary_for_week(w, level))
    if not all_words:
        return []
    return random.sample(all_words, min(count, len(all_words)))


# ============================================================
#  SPEAKING MISSIONS
# ============================================================

def get_speaking_mission(week: int, day_name: str, level: str = "L0") -> Optional[dict]:
    """Get the speaking mission for a specific week, day, and level.
    Returns: {type, prompt, target_seconds} or None.
    """
    key = f"{level}_{week}"
    data = _weekly_data.get(key, {})
    missions = data.get("speaking_missions", {})
    if isinstance(missions, dict):
        return missions.get(day_name)
    return None


# ============================================================
#  WRITING PROMPTS
# ============================================================

def get_writing_prompt(week: int, day_index: int, level: str = "L0") -> Optional[str]:
    """Get the writing prompt for a specific week, day (0-indexed), and level."""
    key = f"{level}_{week}"
    data = _weekly_data.get(key, {})
    prompts = data.get("writing_prompts", [])
    if isinstance(prompts, list) and day_index < len(prompts):
        return prompts[day_index]
    return None


# ============================================================
#  ACCENT DRILLS
# ============================================================

def get_accent_drill(week: int, day_index: int) -> Optional[dict]:
    """Get the accent drill for a specific week and day (0-indexed).
    Returns the daily drill dict from content/l0/accent/weekX.json.
    """
    week = min(8, max(1, week))
    data = _accent_data.get(week, {})
    daily_drills = data.get("daily_drills", [])
    if isinstance(daily_drills, list) and day_index < len(daily_drills):
        return daily_drills[day_index]
    return None


def get_accent_focus(week: int) -> str:
    """Get this week's accent focus description."""
    week = min(8, max(1, week))
    data = _accent_data.get(week, {})
    return data.get("focus", config.PHONEME_WEEKS.get(week, {}).get("focus", "Review"))


def get_accent_focus_ar(week: int) -> str:
    """Get this week's accent focus in Arabic."""
    week = min(8, max(1, week))
    data = _accent_data.get(week, {})
    return data.get("focus_ar", "")


# ============================================================
#  GRAMMAR PATTERNS
# ============================================================

def get_grammar_pattern(week: int) -> Optional[dict]:
    """Get the grammar pattern card for a specific week.
    Returns full grammar pattern dict with formula, examples, practice, etc.
    """
    week = min(8, max(1, week))
    return _grammar_data.get(week)


# ============================================================
#  DAILY TASK CONTENT (complete daily bundle)
# ============================================================

def get_daily_content(week: int, day_name: str, day_index: int, level: str = "L0") -> dict:
    """Get all curriculum content for a specific day.
    Returns a dict with all 7 tasks pre-populated from curated data.
    """
    vocab = get_vocabulary_for_day(week, day_index, level)
    speaking = get_speaking_mission(week, day_name, level)
    writing = get_writing_prompt(week, day_index, level)
    accent = get_accent_drill(week, day_index)
    accent_focus = get_accent_focus(week)
    grammar = get_grammar_pattern(week)

    key = f"{level}_{week}"
    theme = _weekly_data.get(key, {}).get("theme", config.VOCAB_THEMES.get(week, "General"))

    return {
        "week": week,
        "day_name": day_name,
        "day_index": day_index,
        "level": level,
        "vocabulary": vocab,
        "speaking_mission": speaking,
        "writing_prompt": writing,
        "accent_drill": accent,
        "accent_focus": accent_focus,
        "grammar_pattern": grammar.get("pattern_name", "") if grammar else "",
        "theme": theme,
    }


# ============================================================
#  UTILITY
# ============================================================

def get_theme(week: int, level: str = "L0") -> str:
    """Get the vocabulary theme for a week and level."""
    key = f"{level}_{week}"
    data = _weekly_data.get(key, {})
    return data.get("theme", config.VOCAB_THEMES.get(week, "General"))


def is_loaded() -> bool:
    """Check if curriculum data has been loaded."""
    return len(_weekly_data) > 0


def stats() -> dict:
    """Get curriculum data statistics."""
    total_vocab = sum(len(w.get("vocabulary", [])) for w in _weekly_data.values())
    total_speaking = sum(
        len(w.get("speaking_missions", {})) if isinstance(w.get("speaking_missions"), dict) else 0
        for w in _weekly_data.values()
    )
    total_writing = sum(
        len(w.get("writing_prompts", [])) if isinstance(w.get("writing_prompts"), list) else 0
        for w in _weekly_data.values()
    )
    return {
        "weeks_loaded": len(_weekly_data),
        "total_vocabulary": total_vocab,
        "total_speaking_missions": total_speaking,
        "total_writing_prompts": total_writing,
        "accent_weeks": len(_accent_data),
        "grammar_patterns": len(_grammar_data),
    }
