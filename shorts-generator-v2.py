from moviepy.editor import VideoFileClip, TextClip, ImageClip, ColorClip, CompositeVideoClip
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import json
from dataclasses import dataclass
from typing import List, Dict, Any
import random
import os
from sample_data import generate_sample_data, MovieData

class ShortsGenerator:
    def __init__(self, width=1080, height=1920, duration=15, fps=60):
        self.width = width
        self.height = height
        self.background_color = (20, 20, 20)
        self.duration = duration
        self.fps = fps
        self.row_height = 320
        self.poster_width = 180
        self.descriptors = [
            "Mystery Actor",
            "Critics Worst",
            "Audience Worst",
            "Most Successful",
            "Audience Best",
            "Critics Best"
        ]
        
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
        
        # Draw each row
        vertical_spacing = (self.height - 100) // 6  # 6 rows with padding
        start_y = 50  # Starting Y position
        
        # Draw vertical lines first
        box_office_x = self.width - 50 - 100  # Approximate width for box office
        line_x = box_office_x - 20
        draw.line((line_x, 0, line_x, self.height), fill=(255, 255, 255), width=2)
        
        current_x = line_x - 120
        line_x = current_x - 20
        draw.line((line_x, 0, line_x, self.height), fill=(255, 255, 255), width=2)
        
        # Draw mystery actor row first
        self.draw_row(frame, draw, start_y, None, "Mystery Actor", -1, titles_to_show, posters_to_show)
        
        # Draw movie rows
        revealed_count = 0
        for idx, movie in enumerate(movies):
            current_y = start_y + ((idx + 1) * vertical_spacing)  # +1 to skip mystery actor row
            if idx < titles_to_show:
                revealed_count += 1
            self.draw_row(frame, draw, current_y, movie, self.descriptors[idx + 1], 
                         idx, titles_to_show, posters_to_show)
        
        # Draw counter
        counter_text = f"{revealed_count}"
        counter_font = self.get_font(size=60)
        counter_bbox = draw.textbbox((0, 0), counter_text, font=counter_font)
        counter_width = counter_bbox[2] - counter_bbox[0]
        draw.text((self.width // 2 - counter_width // 2, self.height - 100),
                 counter_text,
                 fill=(255, 255, 0),
                 font=counter_font)
        
        return frame
    
    def draw_row(self, frame, draw, y_pos, movie, descriptor, idx, titles_to_show, posters_to_show):
        """Draw a single row with poster and information"""
        # Draw mystery poster or actual poster
        if idx < posters_to_show and movie is not None:
            try:
                if os.path.exists(movie.poster_path):
                    poster = Image.open(movie.poster_path)
                    poster = poster.resize((self.poster_width, self.row_height))
                    frame.paste(poster, (0, y_pos))
                else:
                    self.draw_mystery_poster(draw, 0, y_pos)
            except Exception as e:
                self.draw_mystery_poster(draw, 0, y_pos)
        else:
            self.draw_mystery_poster(draw, 0, y_pos)
        
        # Draw permanent descriptor
        descriptor_font = self.get_font(size=30)
        draw.text((250, y_pos), descriptor,
                 fill=(200, 200, 200), font=descriptor_font)
        
        if movie is not None and idx < titles_to_show:
            # Center point for title
            title_y = y_pos + (self.row_height // 2) - 15
            
            # Draw right-aligned box office first
            box_office_text = f"${movie.box_office}"
            box_office_font = self.get_font(size=30)
            box_office_bbox = draw.textbbox((0, 0), box_office_text, font=box_office_font)
            box_office_width = box_office_bbox[2] - box_office_bbox[0]
            box_office_x = self.width - 50 - box_office_width
            
            draw.text((box_office_x, title_y), box_office_text,
                     fill=(255, 255, 0), font=box_office_font)
            
            # Draw audience score and icon
            current_x = box_office_x - 140
            popcorn_path = "icons/FreshPopcorn.png" if movie.audience_score > 60 else "icons/RottenPopcorn.png"
            popcorn_icon = Image.open(popcorn_path).resize((30, 30))
            frame.paste(popcorn_icon, (current_x, title_y), popcorn_icon)
            draw.text((current_x + 40, title_y), f"{movie.audience_score}%",
                     fill=(255, 255, 255), font=self.get_font(size=30))
            
            # Draw critics score and icon
            current_x = current_x - 140
            tomato_path = "icons/FreshTomato.png" if movie.critics_score > 60 else "icons/RottenTomato.png"
            tomato_icon = Image.open(tomato_path).resize((30, 30))
            frame.paste(tomato_icon, (current_x, title_y), tomato_icon)
            draw.text((current_x + 40, title_y), f"{movie.critics_score}%",
                     fill=(255, 255, 255), font=self.get_font(size=30))
            
            # Draw title centered on poster
            self.draw_title(draw, self.poster_width + 20, title_y, movie.title)
            
    def draw_title(self, draw, x, y, title):
        title_font = self.get_font(size=40)
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = x + (self.poster_width // 2) - (title_width // 2)
        draw.text((title_x, y), title, fill=(255, 255, 255), font=title_font)
        
    def draw_mystery_poster(self, draw, x, y):
        """Draw a placeholder mystery poster"""
        draw.rectangle((x, y, x + self.poster_width, y + self.row_height),
                      fill=(40, 40, 40), outline=(100, 100, 100))
        draw.text((x + 20, y + self.row_height//2), "?",
                 fill=(150, 150, 150), font=self.get_font(size=60))
    
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
