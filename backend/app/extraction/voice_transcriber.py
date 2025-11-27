"""
Voice Transcription Module
Uses OpenAI Whisper API for transcription and GPT for summarization
"""

import ffmpeg
import os
import tempfile
from typing import Tuple
from openai import OpenAI
from app.config import settings
from app.extraction.openai_normalizer import openai_normalizer
from app.extraction.schemas import VoiceExtractionResult


class VoiceTranscriber:
    """Transcribe and summarize voice notes"""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def transcribe_and_summarize(
        self,
        audio_file_path: str,
        context: str = "Exhibition lead discussion"
    ) -> VoiceExtractionResult:
        """
        Transcribe audio file and generate summary

        Args:
            audio_file_path: Path to audio file
            context: Context for summarization

        Returns:
            VoiceExtractionResult with transcript, summary, and topics
        """
        print(f" Transcribing audio: {audio_file_path}")

        # Step 1: Convert audio to compatible format (if needed)
        converted_path = self._convert_audio(audio_file_path)

        try:
            # Step 2: Transcribe using Whisper
            transcript = self._transcribe_whisper(converted_path)
            print(f" Transcribed: {len(transcript)} chars")

            # Step 3: Summarize and extract topics using GPT
            result = openai_normalizer.normalize_voice_transcript(transcript, context)
            print(f" Voice processing complete. Topics: {len(result.topics)}")

            return result

        finally:
            # Cleanup converted file if it was created
            if converted_path != audio_file_path and os.path.exists(converted_path):
                os.remove(converted_path)

    def _convert_audio(self, input_path: str) -> str:
        """
        Convert audio to WAV 16kHz mono (optimal for Whisper)

        Returns:
            Path to converted file (or original if already compatible)
        """
        # Check if already in good format
        ext = os.path.splitext(input_path)[1].lower()
        if ext in ['.wav', '.mp3']:
            # Whisper can handle these directly
            return input_path

        # Convert using ffmpeg
        try:
            temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_wav.close()

            (
                ffmpeg
                .input(input_path)
                .output(temp_wav.name, acodec='pcm_s16le', ac=1, ar='16k')
                .overwrite_output()
                .run(quiet=True)
            )

            print(f" Audio converted to WAV: {temp_wav.name}")
            return temp_wav.name

        except Exception as e:
            print(f" Audio conversion error: {e}")
            # Return original file, let Whisper try
            return input_path

    def _transcribe_whisper(self, audio_path: str) -> str:
        """
        Transcribe audio using OpenAI Whisper API
        Supports Hindi, English, and Hinglish (bilingual) audio

        Args:
            audio_path: Path to audio file

        Returns:
            Transcribed text
        """
        try:
            with open(audio_path, 'rb') as audio_file:
                # Don't specify language - let Whisper auto-detect
                # This enables Hindi, English, and Hinglish (code-mixed) transcription
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text",
                    prompt="This is a business conversation at an Indian trade exhibition. The speaker may use Hindi, English, or Hinglish (Hindi-English mix). Common terms: quotation, order, sample, dealer, distributor, price, delivery, payment terms."
                )

            print(f"🎤 Whisper transcribed (auto-detected language): {len(transcript)} chars")
            return transcript.strip()

        except Exception as e:
            print(f" Whisper transcription error: {e}")
            raise Exception(f"Transcription failed: {str(e)}")


# Singleton instance
voice_transcriber = VoiceTranscriber()
