from dataclasses import dataclass
from typing import Optional
# from elevenlabs import Voice, voices, generate, save, set_api_key, VoiceSettings
import tempfile
import os
from enum import Enum

class ElevenLabsVoice(Enum):
    RACHEL = "21m00Tcm4TlvDq8ikWAM"      # Female, conversational
    DOMI = "AZnzlk1XvdvUeBnXmlld"        # Female, professional
    BELLA = "EXAVITQu4vr4xnSDxMaL"       # Female, soft
    ANTONI = "ErXwobaYiN019PkySvjV"      # Male, deep
    JOSH = "TxGEqnHWrfWFTfGW9XjX"        # Male, broadcast
    ARNOLD = "VR6AewLTigWG4xSOukaG"      # Male, movie trailer
    ADAM = "pNInz6obpgDQGcFmaJgB"        # Male, conversational
    SAM = "yoZ06aMxZJJ28mfd3POQ"         # Male, thoughtful

    @classmethod
    def get_description(cls, voice: 'ElevenLabsVoice') -> str:
        descriptions = {
            cls.RACHEL: "Professional female voice with a warm, conversational tone",
            cls.DOMI: "Clear and professional female voice for business content",
            cls.BELLA: "Soft and gentle female voice for calming content",
            cls.ANTONI: "Deep male voice with gravitas",
            cls.JOSH: "Professional male voice perfect for news or announcements",
            cls.ARNOLD: "Dramatic male voice suited for promotional content",
            cls.ADAM: "Natural male voice for casual conversation",
            cls.SAM: "Thoughtful male voice for educational content"
        }
        return descriptions.get(voice, "No description available")

@dataclass
class TTSConfig:
    api_key: str
    voice: ElevenLabsVoice = ElevenLabsVoice.RACHEL
    model: str = "eleven_monolingual_v1"
    stability: float = 0.5
    similarity_boost: float = 0.75

class TTSManager:
    def __init__(self, config: TTSConfig):
        self.config = config
        set_api_key(config.api_key)
    
    def generate_narration(self, text: str, output_path: str) -> bool:
        """Generate narration using ElevenLabs API"""
        try:
            voice_settings = VoiceSettings(
                stability=self.config.stability,
                similarity_boost=self.config.similarity_boost
            )
            
            audio = generate(
                text=text,
                voice=Voice(
                    voice_id=self.config.voice.value,
                    settings=voice_settings
                ),
                model=self.config.model
            )
            
            with open(output_path, 'wb') as f:
                f.write(audio)
            return True
        except Exception as e:
            print(f"Error generating TTS: {e}")
            return False

    @staticmethod
    def list_voices():
        """Print available voices with descriptions"""
        print("\nAvailable ElevenLabs Voices:")
        print("-" * 50)
        for voice in ElevenLabsVoice:
            print(f"{voice.name}:")
            print(f"  ID: {voice.value}")
            print(f"  Description: {ElevenLabsVoice.get_description(voice)}")
            print()

@dataclass
class AudioConfig:
    background_music_path: Optional[str] = None
    use_tts: bool = False
    tts_config: Optional[TTSConfig] = None
    bg_music_volume: float = 0.3
    narration_volume: float = 1.0
    fade_duration: float = 0.5

def create_sample_tts_config(api_key: str, voice: ElevenLabsVoice = ElevenLabsVoice.RACHEL) -> TTSConfig:
    """Create a sample TTS configuration"""
    return TTSConfig(
        api_key=api_key,
        voice=voice,
        stability=0.5,
        similarity_boost=0.75
    )

if __name__ == "__main__":
    # Example usage
    TTSManager.list_voices()
    
    # Example configuration
    config = TTSConfig(
        api_key="YOUR_API_KEY",
        voice=ElevenLabsVoice.JOSH,  # Using Josh's voice
    )
    
    # Example text generation
    tts = TTSManager(config)
    result = tts.generate_narration(
        "This is a test of the text to speech system.",
        "test_output.mp3"
    )
    
    if result:
        print("Audio generated successfully!")
    else:
        print("Failed to generate audio.")
