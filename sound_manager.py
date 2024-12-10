import os
from typing import Optional, Dict, List
# from elevenlabs import generate, save, set_api_key
from pydub import AudioSegment
from pydub.playback import play
import threading
import time

class SoundManager:
    def __init__(self, api_key: str):
        # Initialize ElevenLabs
        # set_api_key(api_key)
        
        # Audio settings
        self.background_volume = -20  # dB
        self.narration_volume = 0     # dB
        
        # Store audio segments
        self.background_music: Optional[AudioSegment] = None
        self.narrations: Dict[float, AudioSegment] = {}
        
        # Playback control
        self.is_playing = False
        self.playback_thread: Optional[threading.Thread] = None
        self.start_time = 0
    
    def load_background_music(self, music_path: str, loop: bool = True):
        """Load background music from file"""
        if not os.path.exists(music_path):
            raise FileNotFoundError(f"Background music file not found: {music_path}")
            
        self.background_music = AudioSegment.from_file(music_path)
        if loop:
            # Loop music to match video duration
            self.background_music = self.background_music * 3  # Loop 3 times
            
        # Apply volume adjustment
        self.background_music = self.background_music + self.background_volume
    
    # def add_narration(self, timestamp: float, text: str, voice: str = "Josh"):
    #     """Generate and add narration at specific timestamp"""
    #     try:
    #         audio = generate(text=text, voice=voice)
            
    #         # Save temporarily and load as AudioSegment
    #         temp_path = f"temp_narration_{timestamp}.mp3"
    #         save(audio, temp_path)
    #         narration = AudioSegment.from_file(temp_path)
    #         os.remove(temp_path)
            
    #         # Apply volume adjustment
    #         narration = narration + self.narration_volume
            
    #         self.narrations[timestamp] = narration
            
    #     except Exception as e:
    #         print(f"Error generating narration: {e}")
    
    def start_playback(self, duration: float):
        """Start audio playback"""
        if self.is_playing:
            return
            
        self.is_playing = True
        self.start_time = time.time()
        
        def playback_loop():
            current_time = 0
            
            # Play background music if available
            if self.background_music:
                background_thread = threading.Thread(
                    target=play,
                    args=(self.background_music,)
                )
                background_thread.start()
            
            # Monitor and play narrations at timestamps
            while self.is_playing and current_time < duration:
                current_time = time.time() - self.start_time
                
                # Check for narrations at current timestamp
                for timestamp, narration in self.narrations.items():
                    if abs(current_time - timestamp) < 0.1:  # 100ms tolerance
                        narration_thread = threading.Thread(
                            target=play,
                            args=(narration,)
                        )
                        narration_thread.start()
                
                time.sleep(0.05)  # Small sleep to prevent CPU overuse
            
            self.is_playing = False
        
        self.playback_thread = threading.Thread(target=playback_loop)
        self.playback_thread.start()
    
    def stop_playback(self):
        """Stop audio playback"""
        self.is_playing = False
        if self.playback_thread:
            self.playback_thread.join()
    
    def set_background_volume(self, volume_db: float):
        """Adjust background music volume"""
        self.background_volume = volume_db
        if self.background_music:
            self.background_music = self.background_music + volume_db
    
    def set_narration_volume(self, volume_db: float):
        """Adjust narration volume"""
        self.narration_volume = volume_db
        for timestamp, narration in self.narrations.items():
            self.narrations[timestamp] = narration + volume_db
    # def get_background_music(self, duration: float):
    #     """Get background music clip for the specified duration"""
    #     # Load background music if not already loaded
    #     if not self.background_music:
    #         music_path = os.path.join("assets", "music", "background.mp3")
    #         if os.path.exists(music_path):
    #             self.background_music = AudioFileClip(music_path)
        
    #     if self.background_music:
    #         # Return a copy of background music trimmed to duration and with volume adjusted 
    #         return self.background_music.subclip(0, duration).volumex(self.background_volume)
    #     return None