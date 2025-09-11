import logging
import re
import time
from pathlib import Path
from typing import List, Optional, Set

from langchain_ollama import OllamaLLM
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModerationRequest(BaseModel):
    text: str


class ModerationResponse(BaseModel):
    should_moderate: bool
    reason: Optional[str] = None
    flagged_words: Optional[List[str]] = None
    processing_time_ms: float


class ContentModerationService:
    def __init__(self):
        self.slur_words: Set[str] = set()
        self.flagged_list_words: Set[str] = set()
        self.llama_guard_model = None
        self._load_word_lists()
        self._initialize_llama_guard()

    def _load_word_lists(self):
        """Load slur list and flagged list from files"""
        try:
            slur_file_path = Path("assets/slur-list.txt")
            if slur_file_path.exists():
                with open(slur_file_path, "r", encoding="utf-8") as f:
                    words = f.readlines()
                self.slur_words = {w.strip().lower() for w in words if w.strip()}
                logger.info(f"Loaded {len(self.slur_words)} words from slur list")
            else:
                logger.warning("Slur list file not found")

            flagged_file_path = Path("assets/flagged-list.txt")
            if flagged_file_path.exists():
                with open(flagged_file_path, "r", encoding="utf-8") as f:
                    words = f.readlines()
                self.flagged_list_words = {
                    w.strip().lower() for w in words if w.strip()
                }
                logger.info(
                    f"Loaded {len(self.flagged_list_words)} words from flagged list"
                )
            else:
                logger.warning("Flagged list file not found")
        except Exception as e:
            logger.error(f"Error loading word lists: {e}")

    def _initialize_llama_guard(self):
        """Initialize Llama Guard model"""
        try:
            self.llama_guard_model = OllamaLLM(model="llama-guard3:1b")
            logger.info("Llama Guard model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Llama Guard model: {e}")
            self.llama_guard_model = None

    def _check_slur_list(self, text: str) -> tuple[bool, List[str]]:
        """
        Step 1: Check for words from slur list
        Returns (is_flagged, flagged_words)
        """
        text_lower = text.lower()
        flagged_words = []

        # Use word boundaries to avoid partial matches
        for slur in self.slur_words:
            # Create regex pattern with word boundaries
            pattern = r"\b" + re.escape(slur) + r"\b"
            if re.search(pattern, text_lower):
                flagged_words.append(slur)

        return len(flagged_words) > 0, flagged_words

    def _check_llama_guard(self, text: str) -> tuple[bool, Optional[str]]:
        """
        Step 2: Check with Llama Guard model
        Returns (is_unsafe, response)
        """
        if not self.llama_guard_model:
            logger.warning("Llama Guard model not available, skipping check")
            return False, "model_unavailable"

        try:
            response = self.llama_guard_model.invoke(text)
            is_unsafe = "unsafe" in response.lower()
            return is_unsafe, response
        except Exception as e:
            logger.error(f"Error calling Llama Guard: {e}")
            return False, f"model_error: {str(e)}"

    def _check_flagged_list(self, text: str) -> tuple[bool, List[str]]:
        """
        Step 3: Check for words from flagged list (override to safe)
        Returns (has_flagged_words, matched_words)
        """
        text_lower = text.lower()
        matched_words = []

        for flagged_word in self.flagged_list_words:
            pattern = r"\b" + re.escape(flagged_word) + r"\b"
            if re.search(pattern, text_lower):
                matched_words.append(flagged_word)

        return len(matched_words) > 0, matched_words

    def moderate_content(self, text: str) -> dict:
        """
        Main moderation function that implements the 3-step flow
        """
        start_time = time.time()

        if not text or not text.strip():
            return {
                "should_moderate": False,
                "reason": "empty_input",
                "flagged_words": [],
                "processing_time_ms": (time.time() - start_time) * 1000,
            }

        # Step 1: Check slur list
        is_slur_flagged, slur_words = self._check_slur_list(text)
        if is_slur_flagged:
            return {
                "should_moderate": True,
                "reason": "flagged_by_slur_list",
                "flagged_words": slur_words,
                "processing_time_ms": (time.time() - start_time) * 1000,
            }

        # Step 2: Check with Llama Guard
        is_llama_unsafe, llama_response = self._check_llama_guard(text)
        if is_llama_unsafe:
            return {
                "should_moderate": True,
                "reason": "flagged_by_llama_guard",
                "flagged_words": [],
                "processing_time_ms": (time.time() - start_time) * 1000,
            }

        # Step 3: Check flagged list (override to safe)
        has_flagged_words, flagged_matches = self._check_flagged_list(text)
        if has_flagged_words:
            return {
                "should_moderate": False,  # Override to safe
                "reason": "flagged_list_match",
                "flagged_words": flagged_matches,
                "processing_time_ms": (time.time() - start_time) * 1000,
            }

        # If none of the above, content is safe
        return {
            "should_moderate": False,
            "reason": "content_safe",
            "flagged_words": [],
            "processing_time_ms": (time.time() - start_time) * 1000,
        }
