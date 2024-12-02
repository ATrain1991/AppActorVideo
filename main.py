# from shorts_generator import ShortsGenerator, MovieData
from tts_manager import TTSConfig, AudioConfig, ElevenLabsVoice
from youtube_shorts_generator import ShortsGenerator, MovieData
def main():
    # Sample movie data
    movie_data = MovieData(
        title="Avengers: Endgame",
        descriptor="Critics Favorite",
        critics_score=65,
        audience_score=65,
        box_office="2.799B",
        poster_path="path/to/poster.jpg"
    )
    
    # Configure TTS
    # tts_config = TTSConfig(
    #     api_key="YOUR_ELEVENLABS_API_KEY",  # Replace with your API key
    #     voice= ElevenLabsVoice.Rachel,   # Rachel voice
    #     stability=0.5,
    #     similarity_boost=0.75
    # )
    
    # Configure audio
    audio_config = AudioConfig(
        background_music_path="background_music.mp3",  # Optional
        use_tts=True,
        # tts_config=tts_config,
        bg_music_volume=0.3,
        narration_volume=1.0
    )
    
    # Generate video
    generator = ShortsGenerator(duration=15)
    generator.generate_video(
        movie_data,
        "movie_short_with_tts.mp4",
        audio_config
    )

if __name__ == "__main__":
    main()
