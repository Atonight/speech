"""Utilities for generating short-video voice-over audio with CosyVoice."""

from .client import CosyVoiceClient, SynthesisResult
from .voice_design import VoiceDesignClient, VoiceDesignResult

__all__ = ["CosyVoiceClient", "SynthesisResult", "VoiceDesignClient", "VoiceDesignResult"]
