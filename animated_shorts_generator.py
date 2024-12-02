from moviepy.editor import VideoFileClip, TextClip, ImageClip, ColorClip, CompositeVideoClip
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Callable, Optional
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
            "Guess who I am?",
            "Critics Least Favorite",
            "Audience Least Favorite", 
            "Most Successful",
            "Audience Favorite",
            "Critics Favorite"
        ]
        # Animation timing parameters with pauses
        self.title_phase_duration = 0.15  # 15% for initial title phase
        self.standard_pause_duration = 0.08  # 8% for standard pauses
        self.final_pause_duration = 0.15  # 15% for final pause before actor reveal
        self.poster_reveal_duration = 0.12  # 12% for each poster animation
        self.poster_full_screen_duration = 0.15  # 15% for full screen display
        
        # Calculate total time allocations
        self.total_posters = 5  # Number of movie posters
        self.total_pause_time = (
            (self.standard_pause_duration * self.total_posters) + # Standard pauses
            self.final_pause_duration  # Final longer pause
        )
        self.remaining_time = 1.0 - self.total_pause_time
        self.time_per_phase = self.remaining_time / (self.total_posters + 2)  # +2 for title and actor phases
        
        # Create timing breakpoints
        self.breakpoints = self.calculate_breakpoints()
        
    def calculate_breakpoints(self):
        """Calculate the start and end times for each phase of the animation"""
        breakpoints = []
        current_time = 0
        
        # Initial titles phase
        breakpoints.append({
            'start': current_time,
            'end': current_time + self.time_per_phase,
            'type': 'titles'
        })
        current_time += self.time_per_phase
        
        # First pause
        breakpoints.append({
            'start': current_time,
            'end': current_time + self.standard_pause_duration,
            'type': 'pause'
        })
        current_time += self.standard_pause_duration
        
        # Poster reveals with pauses
        for i in range(self.total_posters):
            # Poster reveal
            breakpoints.append({
                'start': current_time,
                'end': current_time + self.time_per_phase,
                'type': 'poster',
                'index': i
            })
            current_time += self.time_per_phase
            
            # Pause after poster (longer pause if it's the last poster)
            pause_duration = self.final_pause_duration if i == self.total_posters - 1 else self.standard_pause_duration
            breakpoints.append({
                'start': current_time,
                'end': current_time + pause_duration,
                'type': 'pause'
            })
            current_time += pause_duration
        
        # Final actor reveal phase
        breakpoints.append({
            'start': current_time,
            'end': current_time + self.time_per_phase,
            'type': 'actor_reveal'
        })
        current_time += self.time_per_phase
        
        return breakpoints
    
    def get_current_phase(self, progress):
        """Determine the current phase and its progress based on overall animation progress"""
        for breakpoint in self.breakpoints:
            if breakpoint['start'] <= progress <= breakpoint['end']:
                phase_progress = (progress - breakpoint['start']) / (breakpoint['end'] - breakpoint['start'])
                return breakpoint, phase_progress
        return self.breakpoints[-1], 1.0

    def calculate_poster_animation(self, progress: float, target_x: int, target_y: int, 
                                 poster_index: int, total_posters: int) -> tuple:
        """Calculate poster position and size during animation"""
        current_phase, phase_progress = self.get_current_phase(progress)
        
        # If we're not in a poster phase for this poster, return None or final position
        if current_phase['type'] != 'poster' or current_phase['index'] != poster_index:
            if progress > current_phase['end'] and current_phase['type'] == 'poster':
                return (target_x, target_y, self.poster_width, self.row_height)
            return None
        
        # Extended full screen duration
        if phase_progress < self.poster_full_screen_duration:
            # Show at full screen
            start_width = min(self.width, self.height * (self.poster_width / self.row_height))
            start_height = min(self.height, self.width * (self.row_height / self.poster_width))
            start_x = (self.width - start_width) / 2
            start_y = (self.height - start_height) / 2
            return (int(start_x), int(start_y), int(start_width), int(start_height))
        
        # Adjust progress to account for full screen duration
        adjusted_progress = (phase_progress - self.poster_full_screen_duration) / (1 - self.poster_full_screen_duration)
        
        # Ease out cubic function
        t = 1 - adjusted_progress
        ease_progress = 1 - (t * t * t)
        
        # Calculate animated properties
        start_width = min(self.width, self.height * (self.poster_width / self.row_height))
        start_height = min(self.height, self.width * (self.row_height / self.poster_width))
        start_x = (self.width - start_width) / 2
        start_y = (self.height - start_height) / 2
        
        # Interpolate position and size
        current_width = start_width + (self.poster_width - start_width) * ease_progress
        current_height = start_height + (self.row_height - start_height) * ease_progress
        current_x = start_x + (target_x - start_x) * ease_progress
        current_y = start_y + (target_y - start_y) * ease_progress
        
        return (int(current_x), int(current_y), int(current_width), int(current_height))

    def create_frame(self, movies: List[MovieData], progress: float, frame_number: int) -> Image.Image:
        """Create a single frame of the video"""
        current_phase, phase_progress = self.get_current_phase(progress)
        
        # Create base frame and overlay frame
        base_frame = Image.new('RGB', (self.width, self.height), self.background_color)
        overlay_frame = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        base_draw = ImageDraw.Draw(base_frame)
        overlay_draw = ImageDraw.Draw(overlay_frame)
        
        # Calculate which elements should be visible
        if current_phase['type'] == 'titles':
            titles_to_show = int(phase_progress * len(movies))
        else:
            titles_to_show = len(movies) if progress > self.breakpoints[0]['end'] else 0
        
        # Draw vertical lines
        box_office_x = self.width - 50 - 100
        line_x = box_office_x - 20
        base_draw.line((line_x, 0, line_x, self.height), fill=(255, 255, 255), width=2)
        
        current_x = line_x - 120
        line_x = current_x - 20
        base_draw.line((line_x, 0, line_x, self.height), fill=(255, 255, 255), width=2)
        
        # Draw rows
        vertical_spacing = (self.height - 100) // 6
        start_y = 50
        revealed_count = 0
        poster_count = 5
        # Draw mystery actor row
        self.draw_row(base_frame, overlay_frame, base_draw, overlay_draw, start_y, None, 
                     "Mystery Actor", -1, titles_to_show, progress, -1, poster_count)
        
        # Draw movie rows
        for idx, movie in enumerate(movies):
            current_y = start_y + ((idx + 1) * vertical_spacing)
            if idx < titles_to_show:
                revealed_count += 1
            self.draw_row(base_frame, overlay_frame, base_draw, overlay_draw, current_y, movie, 
                         self.descriptors[idx + 1], idx, titles_to_show, progress, idx, poster_count)
        
        # Draw counter
        counter_text = f"{revealed_count}"
        counter_font = self.get_font(size=60)
        counter_bbox = base_draw.textbbox((0, 0), counter_text, font=counter_font)
        counter_width = counter_bbox[2] - counter_bbox[0]
        base_draw.text((self.width // 2 - counter_width // 2, self.height - 100),
                      counter_text,
                      fill=(255, 255, 0),
                      font=counter_font)
        
        # Composite the frames
        result = Image.alpha_composite(base_frame.convert('RGBA'), overlay_frame)
        return result.convert('RGB')
    
    def draw_row(self, base_frame, overlay_frame, base_draw, overlay_draw, y_pos, movie, descriptor, 
             idx, titles_to_show, progress, poster_index, total_posters):
        """Draw a single row with poster and information"""
        descriptor_font = self.get_font(size=30)
        base_draw.text((250, y_pos), descriptor, fill=(200, 200, 200), font=descriptor_font)
        
        # Calculate poster animation
        if movie is not None and poster_index >= 0:
            poster_params = self.calculate_poster_animation(progress, 0, y_pos, 
                                                        poster_index, total_posters)
            if poster_params is not None:
                try:
                    if os.path.exists(movie.get_poster()):
                        poster = Image.open(movie.get_poster())
                        poster = poster.resize((poster_params[2], poster_params[3]))
                        if poster_params[2] > self.poster_width:
                            overlay_frame.paste(poster, (poster_params[0], poster_params[1]))
                        else:
                            base_frame.paste(poster, (poster_params[0], poster_params[1]))
                    else:
                        self.draw_mystery_poster(base_draw if poster_params[2] <= self.poster_width else overlay_draw,
                                            poster_params[0], poster_params[1],
                                            poster_params[2], poster_params[3])
                except Exception as e:
                    self.draw_mystery_poster(base_draw if poster_params[2] <= self.poster_width else overlay_draw,
                                        poster_params[0], poster_params[1],
                                        poster_params[2], poster_params[3])
            else:
                self.draw_mystery_poster(base_draw, 0, y_pos, self.poster_width, self.row_height)
        else:
            self.draw_mystery_poster(base_draw, 0, y_pos, self.poster_width, self.row_height)
        
        if movie is not None and idx < titles_to_show:
            title_y = y_pos + (self.row_height // 2) - 15
            
            # Draw box office
            box_office_text = movie.get_display_box_office()
            box_office_font = self.get_font(size=30)
            box_office_bbox = base_draw.textbbox((0, 0), box_office_text, font=box_office_font)
            box_office_width = box_office_bbox[2] - box_office_bbox[0]
            box_office_x = self.width - 50 - box_office_width
            
            base_draw.text((box_office_x, title_y), box_office_text,
                        fill=(255, 255, 0), font=box_office_font)
            
            # Draw scores
            current_x = box_office_x - 140
            audience_score = movie.get_popcornmeter_int()
            popcorn_path = "icons/FreshPopcorn.png" if audience_score > 60 else "icons/RottenPopcorn.png"
            popcorn_icon = Image.open(popcorn_path).resize((30, 30))
            base_frame.paste(popcorn_icon, (current_x, title_y), popcorn_icon)
            base_draw.text((current_x + 40, title_y), movie.get_display_popcornmeter(),
                        fill=(255, 255, 255), font=self.get_font(size=30))
            
            current_x = current_x - 140
            critics_score = movie.get_tomatometer_int()
            tomato_path = "icons/FreshTomato.png" if critics_score > 60 else "icons/RottenTomato.png"
            tomato_icon = Image.open(tomato_path).resize((30, 30))
            base_frame.paste(tomato_icon, (current_x, title_y), tomato_icon)
            base_draw.text((current_x + 40, title_y), movie.get_display_tomatometer(),
                        fill=(255, 255, 255), font=self.get_font(size=30))
            
            title_x = self.poster_width + 40
            self.draw_title(base_draw, title_x, title_y, movie.get_title())
    def draw_mystery_poster(self, draw, x, y, width, height):
        """Draw a placeholder mystery poster"""
        draw.rectangle((x, y, x + width, y + height),
                      fill=(40, 40, 40), outline=(100, 100, 100))
        font_size = min(width, height) // 3
        draw.text((x + width//4, y + height//3), "?",
                 fill=(150, 150, 150), font=self.get_font(size=font_size))
    
    def draw_title(self, draw, x, y, title):
        """Draw the movie title with fixed positioning"""
        title_font = self.get_font(size=40)
        draw.text((x, y), title, fill=(255, 255, 255), font=title_font)
    
    def get_font(self, size=30):
        """Get PIL font - replace with your preferred font path"""
        return ImageFont.truetype("C:\\Windows\\Fonts\\Arial.ttf", size)
    
    def generate_video(self, movies: List[MovieData], output_path: str, progress_callback: Optional[Callable[[float], None]] = None):
        """Generate the complete video"""
        def make_frame(t):
            progress = t / self.duration
            if progress_callback:
                progress_callback(progress)
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
