from io import BytesIO
from moviepy.editor import VideoFileClip, TextClip, ImageClip, ColorClip, CompositeVideoClip
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass
from typing import List, Dict, Any, Callable, Optional, Tuple
import os
import sys
from Actor import Actor
from Movie import Movie

class ShortsGenerator:
    def __init__(self, width=1080, height=1920, duration=15, fps=60, title_phase_percentage=35):
        self.width = width
        self.height = height
        self.duration = duration
        self.fps = fps
        self.background_color = (20, 20, 20)
        self.icon_size = 100
        # Layout parameters
        self.row_height = 320
        self.poster_width = 180
        self.actor_start_size = 400
        self.vertical_spacing = (self.height - 100) // 6
        self.box_office_x = self.width - 150
        
        # Timing distribution (in percentages of total duration)
        self.title_phase_percentage = title_phase_percentage
        self.actor_reveal_duration = 1.0  # Fixed 1 second for actor reveal
        
        # Calculate actual time allocations
        self.title_phase_time = (self.duration * self.title_phase_percentage) / 100
        self.poster_phase_time = self.duration - self.title_phase_time - self.actor_reveal_duration
        
        # Calculate individual timings
        self.title_reveal_duration = self.title_phase_time / 5
        self.poster_reveal_duration = self.poster_phase_time / 5
        self.poster_fullscreen_duration = min(0.2, self.poster_reveal_duration * 0.3)
        
        self.breakpoints = self.calculate_breakpoints()
    
    def calculate_breakpoints(self):
        breakpoints = []
        current_time = 0
        
        # Title reveals
        for i in range(5):
            breakpoints.append({
                'start': current_time,
                'end': current_time + self.title_reveal_duration,
                'type': 'title_reveal',
                'index': i
            })
            current_time += self.title_reveal_duration
        
        # Poster reveals
        poster_start_time = self.title_phase_time
        for i in range(5):
            breakpoints.append({
                'start': poster_start_time + (i * self.poster_reveal_duration),
                'end': poster_start_time + ((i + 1) * self.poster_reveal_duration),
                'type': 'poster',
                'index': i
            })
        
        # Actor reveal
        actor_start_time = self.duration - self.actor_reveal_duration
        breakpoints.append({
            'start': actor_start_time,
            'end': self.duration,
            'type': 'actor_reveal'
        })
        
        return breakpoints
    
    def get_current_phase(self, progress):
        """Return current phase and progress within that phase"""
        current_time = progress * self.duration
        
        for breakpoint in self.breakpoints:
            if breakpoint['start'] <= current_time <= breakpoint['end']:
                phase_progress = (current_time - breakpoint['start']) / (breakpoint['end'] - breakpoint['start'])
                return breakpoint, phase_progress
        
        # If we're past all breakpoints, return the last one with full progress
        return self.breakpoints[-1], 1.0
    
    def count_revealed_clues(self, current_phase):
        clues = 0
        if current_phase['type'] == 'title_reveal':
            clues = current_phase['index'] + 1
        elif current_phase['type'] == 'poster':
            clues = 5 + current_phase['index'] + 1
        elif current_phase['type'] == 'actor_reveal':
            clues = 11  # 5 titles + 5 posters + actor
        return clues
    
    def draw_clue_counter(self, draw: ImageDraw, current_phase: dict):
        clues = self.count_revealed_clues(current_phase)
        font = self.get_font(size=60)  # Increased from 60
        counter_text = f"{clues}"
        bbox = draw.textbbox((0, 0), counter_text, font=font)
        text_width = bbox[2] - bbox[0]
        x = self.width - text_width - 30
        y = 30
        
        # Draw counter background
        padding = 15  # Increased padding for larger text
        draw.rectangle((x - padding, y - padding,
                       x + text_width + padding, y + bbox[3] - bbox[1] + padding),
                      fill=(40, 40, 40), outline=(100, 100, 100))
        
        # Draw counter text
        draw.text((x, y), counter_text, fill=(255, 255, 255), font=font)
    
    def calculate_poster_animation(self, start_time: float, end_time: float,
                                 progress: float, target_x: int, target_y: int) -> Optional[Tuple[int, int, int, int]]:
        animation_duration = end_time - start_time
        local_progress = progress
        
        # Full screen phase
        if local_progress < self.poster_fullscreen_duration / animation_duration:
            start_width = min(self.width, self.height * (self.poster_width / self.row_height))
            start_height = min(self.height, self.width * (self.row_height / self.poster_width))
            start_x = (self.width - start_width) // 2
            start_y = (self.height - start_height) // 2
            return (int(start_x), int(start_y), int(start_width), int(start_height))
        
        # Shrinking animation phase
        shrink_progress = (local_progress - self.poster_fullscreen_duration / animation_duration) / (1 - self.poster_fullscreen_duration / animation_duration)
        if shrink_progress > 1:
            return (target_x, target_y, self.poster_width, self.row_height)
        
        # Calculate current size and position with cubic easing
        t = 1 - shrink_progress
        ease_progress = 1 - (t * t * t)
        
        start_width = min(self.width, self.height * (self.poster_width / self.row_height))
        start_height = min(self.height, self.width * (self.row_height / self.poster_width))
        start_x = (self.width - start_width) // 2
        start_y = (self.height - start_height) // 2
        
        current_width = start_width + (self.poster_width - start_width) * ease_progress
        current_height = start_height + (self.row_height - start_height) * ease_progress
        current_x = start_x + (target_x - start_x) * ease_progress
        current_y = start_y + (target_y - start_y) * ease_progress
        
        return (int(current_x), int(current_y), int(current_width), int(current_height))
    
    def draw_actor(self, frame: Image, actor: Actor, progress: float):
        if actor.url and os.path.exists(actor.url):
            try:
                actor_image = Image.open(actor.url)
                t = progress
                ease_progress = 1 - (1 - t) * (1 - t) * (1 - t)
                
                target_size = min(self.width, self.height)
                current_size = int(self.actor_start_size + (target_size - self.actor_start_size) * ease_progress)
                
                aspect_ratio = actor_image.width / actor_image.height
                if aspect_ratio > 1:
                    width = current_size
                    height = int(current_size / aspect_ratio)
                else:
                    height = current_size
                    width = int(current_size * aspect_ratio)
                
                actor_image = actor_image.resize((width, height), Image.Resampling.LANCZOS)
                x = (self.width - width) // 2
                y = (self.height - height) // 2
                
                overlay = Image.new('RGBA', frame.size, (0, 0, 0, 0))
                overlay.paste(actor_image, (x, y))
                frame.paste(overlay, (0, 0), overlay)
                
                draw = ImageDraw.Draw(frame)
                text = "How many clues did you need?"
                font = self.get_font(size=40)  # Increased from 60
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_x = (self.width - text_width) // 2
                text_y = y + height + 40
                
                draw.text((text_x + 2, text_y + 2), text, fill=(0, 0, 0), font=font)
                draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)
                
            except Exception as e:
                print(f"Error loading actor image: {e}")
    
    def draw_movie_info(self, draw: ImageDraw, base_frame: Image, movie: Movie, y_pos: int):
        title_y = y_pos + (self.row_height // 2) - 15
        font = self.get_font(size=30)  # Increased from 30
        title_font = self.get_font(size=40)  # Increased from 40
        
        # Draw box office
        box_office_text = movie.get_display_box_office()
        bbox = draw.textbbox((0, 0), box_office_text, font=font)
        box_office_width = bbox[2] - bbox[0]
        box_office_x = self.width - 50 - box_office_width
        draw.text((box_office_x, title_y), box_office_text, fill=(255, 255, 0), font=font)
        
        # Draw scores
        current_x = box_office_x - 180  # Increased spacing
        
        # Draw popcornmeter score before icon
        popcorn_score = movie.get_display_popcornmeter()
        bbox = draw.textbbox((0, 0), popcorn_score, font=font)
        score_width = bbox[2] - bbox[0]
        draw.text((current_x - score_width - 10, title_y), popcorn_score, fill=(255, 255, 255), font=font)
        self.draw_score(draw, base_frame, current_x, title_y,
                       movie.get_popcornmeter_int(), "",  # Empty string since we draw score separately
                       "icons/FreshPopcorn.png", "icons/RottenPopcorn.png")
        
        current_x -= 180  # Increased spacing
        
        # Draw tomatometer score before icon
        tomato_score = movie.get_display_tomatometer()
        bbox = draw.textbbox((0, 0), tomato_score, font=font)
        score_width = bbox[2] - bbox[0]
        draw.text((current_x - score_width - 10, title_y), tomato_score, fill=(255, 255, 255), font=font)
        self.draw_score(draw, base_frame, current_x, title_y,
                       movie.get_tomatometer_int(), "",  # Empty string since we draw score separately
                       "icons/FreshTomato.png", "icons/RottenTomato.png")
        
        # Draw title
        draw.text((self.poster_width + 40, title_y), movie.get_title(),
                 fill=(255, 255, 255), font=title_font)
    
    def draw_score(self, draw: ImageDraw, frame: Image, x: int, y: int,
                  score: int, display_score: str, fresh_icon: str, rotten_icon: str):
        icon_path = fresh_icon if score > 60 else rotten_icon
        icon = Image.open(icon_path).resize((self.icon_size, self.icon_size))
        frame.paste(icon, (x, y-self.icon_size//2), icon)
    
    def draw_mystery_poster(self, draw: ImageDraw, x: int, y: int, width: int, height: int):
        draw.rectangle((x, y, x + width, y + height),
                      fill=(40, 40, 40), outline=(100, 100, 100))
        font_size = min(width, height) // 2  # Increased from 3
        draw.text((x + width//4, y + height//3), "?",
                 fill=(150, 150, 150), font=self.get_font(size=font_size))
    
    def get_font(self, size=30):
    # Always use the default font since TrueType isn't available
        default_font = ImageFont.load_default()
        
        # Calculate a scaling factor based on desired size
        base_size = 10  # approximate default font size
        scale = max(1, size / base_size)
        
        # Instead of trying to resize the font, we'll modify the text position
        # and size when drawing. We can do this by wrapping default_font in a class
        class ScaledFont:
            def __init__(self, font, scale):
                self.font = font
                self.scale = scale
        
            def getbbox(self, text, *args, **kwargs):
                # Handle all the extra parameters that PIL might pass
                bbox = self.font.getbbox(text, *args, **kwargs)
                return tuple(int(x * self.scale) for x in bbox)
            
            def getsize(self, text, *args, **kwargs):
                bbox = self.getbbox(text, *args, **kwargs)
                return bbox[2] - bbox[0], bbox[3] - bbox[1]
            
            def getmask(self, text, *args, **kwargs):
                return self.font.getmask(text, *args, **kwargs)
            
            def getlength(self, text, *args, **kwargs):
                return self.font.getlength(text, *args, **kwargs) * self.scale
            
            # Add any other font methods that might be called
            def __getattr__(self, name):
                return getattr(self.font, name)
        
        return ScaledFont(default_font, scale)
    


    def draw_row(self, base_frame: Image, overlay_frame: Image, y_pos: int,
                 movie: Optional[Movie], descriptor: str, current_phase: dict, 
                 poster_index: Optional[int], phase_progress: float):
        base_draw = ImageDraw.Draw(base_frame)
        overlay_draw = ImageDraw.Draw(overlay_frame)
        
        # Show descriptor if current phase is past this row's reveal
        show_descriptor = False
        if current_phase['type'] == 'title_reveal':
            show_descriptor = current_phase['index'] >= poster_index
        elif current_phase['type'] in ['poster', 'actor_reveal']:
            show_descriptor = True
        
        if show_descriptor and poster_index >= 0:
            # Use a more reasonable font size
            descriptor_font = self.get_font(size=50)  # Adjusted from 2060
            
            # Calculate text position to align with poster top
            text_y = y_pos + 10  # Small padding from top of poster
            
            # Draw the descriptor text
            base_draw.text((self.poster_width + 40, text_y), descriptor, 
                          fill=(200, 200, 200), 
                          font=descriptor_font)
        
        # Handle poster visibility and animation
        show_poster = False
        if current_phase['type'] == 'poster':
            if current_phase['index'] == poster_index:
                # This is the currently animating poster
                poster_params = self.calculate_poster_animation(current_phase['start'],
                                                              current_phase['end'],
                                                              phase_progress,
                                                              0, y_pos)
                if poster_params and movie:
                    try:
                        poster_data = movie.get_poster_from_omdb()
                        if poster_data:
                            poster = Image.open(BytesIO(poster_data))
                            poster = poster.resize((poster_params[2], poster_params[3]))
                            target_frame = overlay_frame if poster_params[2] > self.poster_width else base_frame
                            target_frame.paste(poster, (poster_params[0], poster_params[1]))
                            show_poster = True
                    except:
                        pass
            elif current_phase['index'] > poster_index:
                # This poster has already been revealed
                show_poster = True
                if movie:
                    try:
                        poster_data = movie.get_poster_from_omdb()
                        if poster_data:
                            poster = Image.open(BytesIO(poster_data))
                            poster = poster.resize((self.poster_width, self.row_height))
                            base_frame.paste(poster, (0, y_pos))
                    except:
                        self.draw_mystery_poster(base_draw, 0, y_pos, self.poster_width, self.row_height)
        elif current_phase['type'] == 'actor_reveal':
            # All posters should be visible during actor reveal
            show_poster = True
            if movie:
                try:
                    poster_data = movie.get_poster_from_omdb()
                    if poster_data:
                        poster = Image.open(BytesIO(poster_data))
                        poster = poster.resize((self.poster_width, self.row_height))
                        base_frame.paste(poster, (0, y_pos))
                except:
                    self.draw_mystery_poster(base_draw, 0, y_pos, self.poster_width, self.row_height)
        
        if not show_poster:
            self.draw_mystery_poster(base_draw, 0, y_pos, self.poster_width, self.row_height)
        
        # Show movie info if descriptor is shown
        if movie is not None and show_descriptor:
            self.draw_movie_info(base_draw, base_frame, movie, y_pos)

    def create_frame(self, actor: Actor, movies_with_descriptors: List[Tuple[Movie, str]], 
                    progress: float) -> Image:
        # Get current phase based on progress
        current_phase, phase_progress = self.get_current_phase(progress)
        
        base_frame = Image.new('RGB', (self.width, self.height), self.background_color)
        overlay_frame = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        base_draw = ImageDraw.Draw(base_frame)
        
        # Draw clue counter
        self.draw_clue_counter(base_draw, current_phase)
        
        start_y = 50
        self.draw_row(base_frame, overlay_frame, start_y, None, "Mystery Actor", 
                     current_phase, -1, phase_progress)
        
        for idx, (movie, descriptor) in enumerate(movies_with_descriptors):
            current_y = start_y + ((idx + 1) * self.vertical_spacing)
            self.draw_row(base_frame, overlay_frame, current_y, movie, descriptor,
                         current_phase, idx, phase_progress)
        
        if current_phase['type'] == 'actor_reveal':
            self.draw_actor(base_frame, actor, phase_progress)
        
        result = Image.alpha_composite(base_frame.convert('RGBA'), overlay_frame)
        return result.convert('RGB')

    def generate_video(self, actor: Actor, movies_with_descriptors: List[Tuple[Movie, str]], 
                    output_path: str, progress_callback: Optional[Callable[[float], None]] = None):
        def make_frame(t):
            progress = t / self.duration
            if progress_callback:
                progress_callback(progress)
            frame = self.create_frame(actor, movies_with_descriptors, progress)
            return np.array(frame)
        
        clip = ColorClip(size=(self.width, self.height), color=self.background_color, duration=self.duration)
        clip = clip.set_make_frame(make_frame)
        
        # Common video settings
        bitrate = "15000k"  # Adjust based on your quality needs
        
        try:
            # Try CPU encoding first with optimized settings
            print("Using CPU encoding with x264...")
            ffmpeg_params = [
                '-c:v', 'libx264',
                '-preset', 'medium',  # Balance between speed and compression
                '-crf', '23',        # Constant Rate Factor (18-28 is good, lower = better quality)
                '-pix_fmt', 'yuv420p',  # Required for compatibility
                '-movflags', '+faststart',  # Enable streaming
                '-b:v', bitrate,
                '-maxrate', bitrate,
                '-bufsize', f"{int(bitrate[:-1])*2}k",
                '-profile:v', 'high',
                '-level', '4.2'
            ]
            
            clip.write_videofile(
                output_path,
                fps=self.fps,
                codec='libx264',
                ffmpeg_params=ffmpeg_params,
                audio=False,
                threads=4  # Adjust based on your CPU
            )
            return
            
        except Exception as e:
            print(f"CPU encoding failed: {e}")
            print("Trying alternative encoding settings...")
            
            try:
                # Simplified fallback settings
                clip.write_videofile(
                    output_path,
                    fps=self.fps,
                    codec='libx264',
                    preset='medium',
                    bitrate=bitrate,
                    audio=False
                )
                return
                
            except Exception as e:
                print(f"Alternative encoding failed: {e}")
                print("Please ensure ffmpeg is properly installed and try again.")
                raise

    def generate_video_helper(self, actor: Actor, movies: List[Movie] = None, 
                            movies_with_descriptors: List[Tuple[Movie, str]] = None,
                            output_path = "", progress_callback: Optional[Callable[[float], None]] = None):
        if movies_with_descriptors is None:
            if movies is None:
                print("no movies provided")
                return
            movies_with_descriptors = [
                (movies[0], "Critics Least Favorite"),
                (movies[1], "Audience Least Favorite"),
                (movies[2], "Most Successful"),
                (movies[3], "Audience Favorite"),
                (movies[4], "Critics Favorite")
            ]
        if output_path == "":
            output_path = f"{actor.name} quiz.mp4"  # Added .mp4 extension
        
        def update_progress(progress):
            sys.stdout.write(f"\rProgress: {progress*100:.1f}%")
            sys.stdout.flush()
if __name__ == "__main__":
    movie1 = Movie("role models", "2024", "100M", "85%", "90%","")
    movie2 = Movie("Prestige", "2023", "150M", "75%", "30%","")
    movie3 = Movie("Alien", "2022", "200M", "95%", "100%","")
    movie4 = Movie("Red", "2021", "120M", "41%", "85%","")
    movie5 = Movie("Moana", "2020", "180M", "90%", "95%","")
    movies = [movie1, movie2, movie3, movie4, movie5]
    actor = Actor("Dwayne Johnson", movies, "Dwayne_Johnson.jpg")
    movies_with_descriptors = [
        (movie1, "Critics Least Favorite"),
        (movie2, "Audience Least Favorite"),
        (movie3, "Most Successful"),
        (movie4, "Audience Favorite"),
        (movie5, "Critics Favorite")
    ]
    # generator = ShortsGenerator(duration=20)
    def update_progress(progress):
        sys.stdout.write(f"\rProgress: {progress*100:.1f}%")
        sys.stdout.flush()

    generator = ShortsGenerator(duration=20, title_phase_percentage=30)
    generator.generate_video(actor, movies_with_descriptors, "output5.mp4", update_progress)