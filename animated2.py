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
        # Animation timing parameters
        self.title_phase_duration = 0.25  # 25% for titles and scores
        self.poster_reveal_duration = 0.15  # 15% for each poster animation
        self.poster_full_screen_stall = 0.3  # 30% of the poster_reveal_duration for full screen stall
        self.wait_between_posters = 0.05  # 5% wait time between poster animations
        self.final_actor_duration = 0.15  # 15% for final actor reveal
        self.final_actor_stall = 0.05  # 5% for initial pause before actor reveal
        self.poster_phase_start = self.title_phase_duration
        
    def calculate_poster_animation(self, progress: float, target_x: int, target_y: int, 
                                 poster_index: int, total_posters: int) -> tuple:
        """Calculate poster position and size during animation"""
        # Calculate timing for each poster including wait time
        available_time = 1 - self.title_phase_duration - self.final_actor_duration - self.final_actor_stall
        total_time_per_poster = self.poster_reveal_duration + self.wait_between_posters
        poster_phase_per_poster = available_time / total_posters
        poster_start = self.title_phase_duration + (poster_index * poster_phase_per_poster)
        poster_end = poster_start + self.poster_reveal_duration
        
        if progress < poster_start:
            return None  # Poster not yet visible
        
        if progress > poster_end + self.wait_between_posters:
            return (target_x, target_y, self.poster_width, self.row_height)  # Final position
        
        # Calculate animation progress
        anim_progress = (progress - poster_start) / self.poster_reveal_duration
        
        # Stall at full screen for the specified duration
        if anim_progress < self.poster_full_screen_stall:
            # Show at full screen
            start_width = min(self.width, self.height * (self.poster_width / self.row_height))
            start_height = min(self.height, self.width * (self.row_height / self.poster_width))
            start_x = (self.width - start_width) / 2
            start_y = (self.height - start_height) / 2
            return (int(start_x), int(start_y), int(start_width), int(start_height))
        
        # Adjust progress to account for stall time
        adjusted_progress = (anim_progress - self.poster_full_screen_stall) / (1 - self.poster_full_screen_stall)
        
        # Ease out cubic function
        t = 1 - adjusted_progress
        ease_progress = 1 - (t * t * t)
        
        # Calculate animated properties
        start_width = min(self.width, self.height * (self.poster_width / self.row_height))
        start_height = min(self.height, self.width * (self.row_height / self.poster_width))
        start_x = (self.width - start_width) / 2
        start_y = (self.height - start_height) / 2
        
        current_width = start_width + (self.poster_width - start_width) * ease_progress
        current_height = start_height + (self.row_height - start_height) * ease_progress
        current_x = start_x + (target_x - start_x) * ease_progress
        current_y = start_y + (target_y - start_y) * ease_progress
        
        return (int(current_x), int(current_y), int(current_width), int(current_height))

    def calculate_actor_reveal(self, progress: float, actor_image_path: str) -> tuple:
        """Calculate actor reveal animation parameters"""
        reveal_start = 1 - self.final_actor_duration
        
        if progress < reveal_start - self.final_actor_stall:
            return None
            
        if progress < reveal_start:
            return ('mystery', 0, 0, self.width, self.height)  # Show full screen mystery box
            
        # Calculate reveal animation
        reveal_progress = (progress - reveal_start) / self.final_actor_duration
        
        # Ease in-out cubic
        t = reveal_progress
        if t < 0.5:
            ease_progress = 4 * t * t * t
        else:
            t = t - 1
            ease_progress = 1 + 4 * t * t * t
            
        return ('actor', 0, 0, self.width, self.height, ease_progress)

    def create_frame(self, movies: List[MovieData], progress: float, frame_number: int, actor_image_path: str) -> Image.Image:
        """Create a single frame of the video"""
        # Create base frame and overlay frame
        base_frame = Image.new('RGB', (self.width, self.height), self.background_color)
        overlay_frame = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        base_draw = ImageDraw.Draw(base_frame)
        overlay_draw = ImageDraw.Draw(overlay_frame)
        
        # Check for actor reveal phase
        actor_params = self.calculate_actor_reveal(progress, actor_image_path)
        if actor_params is not None:
            if actor_params[0] == 'mystery':
                # Draw full screen mystery box
                self.draw_mystery_poster(base_draw, 0, 0, self.width, self.height)
                return Image.alpha_composite(base_frame.convert('RGBA'), overlay_frame).convert('RGB')
            elif actor_params[0] == 'actor':
                try:
                    if os.path.exists(actor_image_path):
                        actor_image = Image.open(actor_image_path)
                        # Resize maintaining aspect ratio
                        aspect = actor_image.width / actor_image.height
                        if aspect > 1:
                            new_width = self.width
                            new_height = int(self.width / aspect)
                        else:
                            new_height = self.height
                            new_width = int(self.height * aspect)
                        
                        actor_image = actor_image.resize((new_width, new_height))
                        # Center the image
                        x_offset = (self.width - new_width) // 2
                        y_offset = (self.height - new_height) // 2
                        
                        # Create transition effect
                        if actor_params[5] < 1:
                            # Draw mystery box fading out
                            overlay_draw.rectangle((0, 0, self.width, self.height),
                                                fill=(40, 40, 40, int(255 * (1 - actor_params[5]))))
                        
                        base_frame.paste(actor_image, (x_offset, y_offset))
                    else:
                        self.draw_mystery_poster(base_draw, 0, 0, self.width, self.height)
                except Exception as e:
                    self.draw_mystery_poster(base_draw, 0, 0, self.width, self.height)
                    
                return Image.alpha_composite(base_frame.convert('RGBA'), overlay_frame).convert('RGB')
        
        # Calculate which elements should be visible
        if progress <= self.title_phase_duration:
            titles_to_show = int((progress / self.title_phase_duration) * len(movies))
        else:
            titles_to_show = len(movies)
        
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
        
        # Draw mystery actor row
        self.draw_row(base_frame, overlay_frame, base_draw, overlay_draw, start_y, None, 
                     "Mystery Actor", -1, titles_to_show, progress, -1, len(movies))
        
        # Draw movie rows
        for idx, movie in enumerate(movies):
            current_y = start_y + ((idx + 1) * vertical_spacing)
            if idx < titles_to_show:
                revealed_count += 1
            self.draw_row(base_frame, overlay_frame, base_draw, overlay_draw, current_y, movie, 
                         self.descriptors[idx + 1], idx, titles_to_show, progress, idx, len(movies))
        
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
        # Draw permanent descriptor
        descriptor_font = self.get_font(size=30)
        base_draw.text((250, y_pos), descriptor, fill=(200, 200, 200), font=descriptor_font)
        
        # Calculate poster animation
        if movie is not None and poster_index >= 0:
            poster_params = self.calculate_poster_animation(progress, 0, y_pos, 
                                                         poster_index, total_posters)
            if poster_params is not None:
                try:
                    if os.path.exists(movie.poster_path):
                        poster = Image.open(movie.poster_path)
                        poster = poster.resize((poster_params[2], poster_params[3]))
                        # Draw to overlay if in fullscreen mode
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
            # Calculate vertical center of the row for text alignment
            title_y = y_pos + (self.row_height // 2) - 15
            
            # Draw box office
            box_office_text = f"${movie.box_office:,}"
            box_office_font = self.get_font(size=30)
            box_office_bbox = base_draw.textbbox((0, 0), box_office_text, font=box_office_font)
            box_office_width = box_office_bbox[2] - box_office_bbox[0]
            box_office_x = self.width - 50 - box_office_width
            
            base_draw.text((box_office_x, title_y), box_office_text,
                         fill=(255, 255, 0), font=box_office_font)
            
            # Draw scores
            current_x = box_office_x - 140
            popcorn_path = "icons/FreshPopcorn.png" if movie.audience_score > 60 else "icons/RottenPopcorn.png"
            popcorn_icon = Image.open(popcorn_path).resize((30, 30))
            base_frame.paste(popcorn_icon, (current_x, title_y), popcorn_icon)
            base_draw.text((current_x + 40, title_y), f"{movie.audience_score}%",
                         fill=(255, 255, 255), font=self.get_font(size=30))
            
            current_x = current_x - 140
            tomato_path = "icons/FreshTomato.png" if movie.critics_score > 60 else "icons/RottenTomato.png"
            tomato_icon = Image.open(tomato_path).resize((30, 30))
            base_frame.paste(tomato_icon, (current_x, title_y), tomato_icon)
            base_draw.text((current_x + 40, title_y), f"{movie.critics_score}%",
                         fill=(255, 255, 255), font=self.get_font(size=30))
            
            # Draw title to the right of the final poster position
            title_x = self.poster_width + 40
            self.draw_title(base_draw, title_x, title_y, movie.title)

    def draw_mystery_poster(self, draw, x, y, width, height):
        """Draw a placeholder mystery poster"""
        draw.rectangle((x, y, x + width, y + height),
                      fill=(40, 40, 40), outline=(100, 100, 100))
        font_size = min(width, height) // 3
        draw.text((x + width//4))