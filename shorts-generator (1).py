from moviepy.editor import VideoFileClip, TextClip, ImageClip, ColorClip, CompositeVideoClip
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import json
from dataclasses import dataclass
from typing import List, Dict, Any
import random
import os
from sample_data import generate_sample_data
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
        reveal_phase_duration = 0.8  # Use 80% of video for revealing elements
        hold_duration = 0.2  # Keep everything on screen for final 20%
        
        # Calculate which elements should be visible
        if progress <= reveal_phase_duration:
            movies_to_show = int((progress / reveal_phase_duration) * num_movies)
        else:
            movies_to_show = num_movies
        
        # Calculate spacing
        poster_height = 320
        vertical_spacing = poster_height + 5  # Add some padding between entries
        start_y = 1  # Starting Y position
        
        # Draw elements for each movie
        revealed_count = 0
        for idx, movie in enumerate(movies):
            if idx >= movies_to_show:
                continue
                
            revealed_count += 1
            current_y = start_y + (idx * vertical_spacing)
            
            # Load and display poster
            try:
                if os.path.exists(movie.poster_path):
                    poster = Image.open(movie.poster_path)
                    poster_width = int(poster.width * (poster_height / poster.height))
                    poster = poster.resize((poster_width, poster_height))
                    frame.paste(poster, (50, current_y))
                    content_start_x = poster_width + 80  # Start content after poster with padding
                else:
                    # Placeholder if poster doesn't exist
                    draw.rectangle((50, current_y, 50 + (poster_height * 0.7), current_y + poster_height),
                                 outline=(255, 255, 255))
                    content_start_x = 50 + int(poster_height * 0.7) + 30
            except Exception as e:
                content_start_x = 280  # Default if poster fails
            
            # Draw descriptor at the top
            draw.text((content_start_x, current_y), movie.descriptor,
                     fill=(200, 200, 200), font=self.get_font(size=30))
            
            # Calculate center point for the rest of the content
            content_y = current_y + (poster_height // 2) - 30
            current_x = content_start_x
            
            # Draw title
            title_font = self.get_font(size=40)
            draw.text((current_x, content_y), movie.title,
                     fill=(255, 255, 255), font=title_font)
            title_bbox = draw.textbbox((current_x, content_y), movie.title, font=title_font)
            current_x = title_bbox[2] + 100  # Move past title
            icon_spacing = 10
            icon_size = 100
            icon_y_offset = -icon_size // 4
            # Draw critics score with tomato
            tomato_path = "icons/FreshTomato.png" if movie.critics_score > 60 else "icons/RottenTomato.png"
            tomato_icon = Image.open(tomato_path).resize((icon_size, icon_size))
            frame.paste(tomato_icon, (current_x, content_y + icon_y_offset), tomato_icon)
            current_x += tomato_icon.width + icon_spacing
            
            score_text = f"{movie.critics_score}%"
            draw.text((current_x, content_y), score_text,
                     fill=(255, 255, 255), font=self.get_font(size=30))
            score_bbox = draw.textbbox((current_x, content_y), score_text, font=self.get_font(size=30))
            current_x = score_bbox[2] + 20
            
            # Draw audience score with popcorn
            popcorn_path = "icons/FreshPopcorn.png" if movie.audience_score > 60 else "icons/RottenPopcorn.png"
            popcorn_icon = Image.open(popcorn_path).resize((icon_size, icon_size))
            frame.paste(popcorn_icon, (current_x, content_y + icon_y_offset), popcorn_icon)
            current_x += popcorn_icon.width + icon_spacing
            
            score_text = f"{movie.audience_score}%"
            draw.text((current_x, content_y), score_text,
                     fill=(255, 255, 255), font=self.get_font(size=30))
            score_bbox = draw.textbbox((current_x, content_y), score_text, font=self.get_font(size=30))
            current_x = score_bbox[2] + 20
            
            # Draw box office
            draw.text((current_x, content_y), f"${movie.box_office}",
                     fill=(255, 255, 0), font=self.get_font(size=30))
        
        # Draw counter
        counter_text = f"{revealed_count}"
        counter_font = self.get_font(size=60)
        counter_bbox = draw.textbbox((0, 0), counter_text, font=counter_font)
        counter_width = counter_bbox[2] - counter_bbox[0]
        draw.text((self.width // 2 - counter_width // 2, self.height - 150),
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

if __name__ == "__main__":
    movies = generate_sample_data()
    generator = ShortsGenerator(duration=20)
    generator.generate_video(movies, "movie_short.mp4")
