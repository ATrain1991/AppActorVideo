from moviepy.editor import VideoFileClip, TextClip, ImageClip, ColorClip, CompositeVideoClip
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import json
from dataclasses import dataclass
from typing import List, Dict, Any
import random
import os

@dataclass
class MovieData:
    title: str
    descriptor: str
    critics_score: int
    audience_score: int
    box_office: str
    poster_path: str

class ShortsGenerator:
    def __init__(self, width=1080, height=1920, duration=15, fps=60):
        self.width = width
        self.height = height
        self.background_color = (20, 20, 20)
        self.duration = duration
        self.fps = fps
        
    def create_frame(self, 
                    movies: List[MovieData],
                    progress: float,
                    frame_number: int) -> Image.Image:
        """Create a single frame of the video"""
        frame = Image.new('RGB', (self.width, self.height), self.background_color)
        draw = ImageDraw.Draw(frame)
        
        # Calculate animation phases
        num_movies = len(movies)
        title_phase_duration = 0.5  # First 50% for titles and scores
        poster_phase_duration = 0.5  # Next 50% for posters
        
        # Calculate which elements should be visible
        if progress <= title_phase_duration:
            titles_to_show = int((progress / title_phase_duration) * num_movies)
        else:
            titles_to_show = num_movies
            
        if progress > title_phase_duration:
            poster_progress = (progress - title_phase_duration) / poster_phase_duration
            posters_to_show = int(poster_progress * num_movies)
        else:
            posters_to_show = 0
        
        # Calculate spacing
        vertical_spacing = min(300, self.height // (num_movies + 1))
        start_y = 100
        
        # Draw elements for each movie
        revealed_count = 0
        for idx, movie in enumerate(movies):
            current_y = start_y + (idx * vertical_spacing)
            
            # Always show descriptor
            draw.text((100, current_y), movie.descriptor,
                     fill=(200, 200, 200), font=self.get_font(size=30))
            current_y += 40
            
            # Show title and scores if it's time
            if idx < titles_to_show:
                revealed_count += 1
                draw.text((100, current_y), movie.title,
                         fill=(255, 255, 255), font=self.get_font(size=40))
                current_y += 50
                
                # Load and paste tomato icon
                tomato_path = "icons/FreshTomato.png" if movie.critics_score > 60 else "icons/RottenTomato.png"
                tomato_icon = Image.open(tomato_path).resize((30, 30))
                frame.paste(tomato_icon, (100, current_y), tomato_icon)
                
                # Draw critics score
                draw.text((140, current_y), f"{movie.critics_score}% |", fill=(255, 255, 255), font=self.get_font(size=30))
                
                # Load and paste popcorn icon 
                popcorn_path = "icons/FreshPopcorn.png" if movie.audience_score > 60 else "icons/RottenPopcorn.png"
                popcorn_icon = Image.open(popcorn_path).resize((30, 30))
                frame.paste(popcorn_icon, (240, current_y), popcorn_icon)
                
                # Draw audience score
                draw.text((280, current_y), f"{movie.audience_score}%", fill=(255, 255, 255), font=self.get_font(size=30))
            
            # Show poster if it's time
            if idx < posters_to_show:
                revealed_count += 1
                try:
                    if os.path.exists(movie.poster_path):
                        poster = Image.open(movie.poster_path)
                        poster_height = 320
                        poster_width = int(poster.width * (poster_height / poster.height))
                        poster = poster.resize((poster_width, poster_height))
                        frame.paste(poster, (self.width - poster_width - 50, current_y - 50))
                except Exception as e:
                    # If poster can't be loaded, draw a placeholder
                    draw.rectangle((self.width - 200, current_y - 50, 
                                  self.width - 50, current_y + 50),
                                 outline=(255, 255, 255))
        
        # Always show running counter
        counter_text = f"{revealed_count}"
        counter_font = self.get_font(size=60)
        counter_bbox = draw.textbbox((0, 0), counter_text, font=counter_font)
        counter_width = counter_bbox[2] - counter_bbox[0]
        draw.text((self.width // 2 - counter_width // 2, self.height - 150),
                 counter_text,
                 fill=(255, 255, 0),
                 font=counter_font)
        draw.text((100, 100),
                 counter_text,
                 fill=(255, 255, 0),
                 font=counter_font)
        return frame
    
    def get_font(self, size=30):
        """Get PIL font - replace with your preferred font path"""
        return ImageFont.truetype("C:\\Windows\\Fonts\\Arial.ttf", size)
    
    def generate_video(self, movies: List[MovieData], output_path: str):
        """Generate the complete video"""
        def make_frame(t):
            """Function to generate frame at time t"""
            progress = t / self.duration
            frame = self.create_frame(movies, progress, int(t * self.fps))
            return np.array(frame)
        
        # Create the video clip - simplified creation
        clip = ColorClip(
            size=(self.width, self.height),
            color=self.background_color,
            duration=self.duration
        ).set_make_frame(make_frame)
        
        clip.write_videofile(
            output_path,
            fps=self.fps,
            codec='libx264',
            audio=False
        )

def generate_sample_data() -> List[MovieData]:
    """Generate sample movie data"""
    return [
        MovieData(
            title="Avengers: Endgame",
            descriptor="Epic Conclusion",
            critics_score=94,
            audience_score=90,
            box_office="2.799B",
            poster_path="Aquaman.jpg"
        ),
        MovieData(
            title="The Dark Knight",
            descriptor="Crime Thriller",
            critics_score=94,
            audience_score=94,
            box_office="1.005B",
            poster_path="Aquaman.jpg"
        ),
        MovieData(
            title="Inception",
            descriptor="Mind-Bending",
            critics_score=87,
            audience_score=91,
            box_office="836.8M",
            poster_path="Aquaman.jpg"
        ),
        MovieData(
            title="Interstellar",
            descriptor="Space Epic",
            critics_score=73,
            audience_score=86,
            box_office="701.7M",
            poster_path="Aquaman.jpg"
        ),
        MovieData(
            title="The Matrix",
            descriptor="Sci-Fi Classic",
            critics_score=88,
            audience_score=85,
            box_office="463.5M",
            poster_path="Aquaman.jpg"
        ),
    ]

if __name__ == "__main__":
    # Generate sample data
    movies = generate_sample_data()
    
    # Create and save video
    generator = ShortsGenerator(duration=20)  # Increased duration for more visibility
    generator.generate_video(movies, "movie_short.mp4")
