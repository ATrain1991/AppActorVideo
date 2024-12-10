import cv2
import numpy as np
from typing import List, Dict, Any, Callable, Optional, Tuple
import os
import sys
from dataclasses import dataclass
from Actor import Actor
from Movie import Movie
import requests
from io import BytesIO
from opencv_font_handler import OpenCVFontHandler
from opencv_layout_config import LayoutConfig

from opencv_drawing_utils import DrawingUtils

class OpenCVShortsGenerator:
    def __init__(self, width=1080, height=1920, duration=15, fps=60, title_phase_percentage=35):
        # Initialize configuration
        self.config = LayoutConfig(width, height)
        self.font_handler = OpenCVFontHandler()
        self.drawing = DrawingUtils(self.config, self.font_handler)
        
        self.width = width
        self.height = height
        self.duration = duration
        self.fps = fps
        self.background_color = (20, 20, 20)  # BGR format
        
        # Timing distribution
        self.title_phase_percentage = title_phase_percentage
        self.actor_reveal_duration = 1.0
        
        # Calculate time allocations
        self.title_phase_time = (self.duration * self.title_phase_percentage) / 100
        self.poster_phase_time = self.duration - self.title_phase_time - self.actor_reveal_duration
        
        # Individual timings
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
            'type': 'actor_reveal',
            'index': -1
        })
        
        return breakpoints

    def get_current_phase(self, progress):
        current_time = progress * self.duration
        
        for breakpoint in self.breakpoints:
            if breakpoint['start'] <= current_time <= breakpoint['end']:
                phase_progress = (current_time - breakpoint['start']) / (breakpoint['end'] - breakpoint['start'])
                return breakpoint, phase_progress
        
        return self.breakpoints[-1], 1.0

    def calculate_poster_animation(self, phase_progress: float, target_x: int, target_y: int) -> Tuple[int, int, int, int]:
        # Calculate full screen dimensions
        if self.width / self.height > 1 / 1.5:  # 1.5 is standard poster aspect ratio
            poster_height = self.height
            poster_width = int(poster_height / 1.5)
        else:
            poster_width = self.width
            poster_height = int(poster_width * 1.5)
            
        start_x = (self.width - poster_width) // 2
        start_y = (self.height - poster_height) // 2
        
        if phase_progress < self.poster_fullscreen_duration / self.poster_reveal_duration:
            return start_x, start_y, poster_width, poster_height
        
        # Calculate shrinking animation
        shrink_progress = (phase_progress - self.poster_fullscreen_duration / self.poster_reveal_duration) / (1 - self.poster_fullscreen_duration / self.poster_reveal_duration)
        
        t = 1 - shrink_progress
        ease_progress = 1 - (t * t * t)
        
        current_width = int(poster_width + (self.config.poster_width - poster_width) * ease_progress)
        current_height = int(poster_height + (self.config.row_height - poster_height) * ease_progress)
        current_x = int(start_x + (target_x - start_x) * ease_progress)
        current_y = int(start_y + (target_y - start_y) * ease_progress)
        
        return current_x, current_y, current_width, current_height

    def draw_poster(self, frame: np.ndarray, movie: Movie, x: int, y: int, width: int, height: int) -> None:
        if not movie or not movie.poster_path:
            return
            
        poster_img = cv2.imread(movie.poster_path)
        if poster_img is None:
            return
            
        resized_poster = cv2.resize(poster_img, (width, height))
        y_end = min(y + height, frame.shape[0])
        x_end = min(x + width, frame.shape[1])
        
        # Create alpha mask for smooth transition
        alpha = np.ones((height, width, 1), dtype=np.float32)
        frame[y:y_end, x:x_end] = cv2.addWeighted(
            frame[y:y_end, x:x_end], 
            1 - alpha[:y_end-y, :x_end-x], 
            resized_poster[:y_end-y, :x_end-x], 
            alpha[:y_end-y, :x_end-x], 
            0
        )

    def create_frame(self, actor: Actor, movies_with_descriptors: List[Tuple[Movie, str]], progress: float) -> np.ndarray:
        current_phase, phase_progress = self.get_current_phase(progress)
        
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:] = self.background_color
        
        # Use the drawing utils for all text and UI elements
        self.drawing.draw_clue_counter(frame, current_phase)
        
        start_y = 100
        self.drawing.draw_row(frame, start_y, None, "Mystery Actor", 
                            current_phase, -1, phase_progress)
        
        for idx, (movie, descriptor) in enumerate(movies_with_descriptors):
            current_y = start_y + ((idx + 1) * self.config.vertical_spacing)
            
            # Handle title reveals and basic info
            self.drawing.draw_row(frame, current_y, movie, descriptor,
                                current_phase, idx, phase_progress)
            
            # Handle poster reveals
            if current_phase['type'] == 'poster':
                if current_phase['index'] == idx:
                    poster_x, poster_y, poster_w, poster_h = self.calculate_poster_animation(
                        phase_progress, 0, current_y
                    )
                    self.draw_poster(frame, movie, poster_x, poster_y, poster_w, poster_h)
                elif current_phase['index'] > idx:
                    self.draw_poster(frame, movie, 0, current_y,
                                   self.config.poster_width, self.config.row_height)
            elif current_phase['type'] in ['actor_reveal', 'final_frame']:
                self.draw_poster(frame, movie, 0, current_y,
                               self.config.poster_width, self.config.row_height)
        
        # Draw actor reveal if in that phase
        if current_phase['type'] in ['actor_reveal', 'final_frame']:
            self.drawing.draw_actor(frame, actor, phase_progress)
        
        return frame

    def generate_video(self, actor: Actor, movies_with_descriptors: List[Tuple[Movie, str]], 
                      output_path: str, progress_callback: Optional[Callable[[float], None]] = None):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, self.fps, (self.width, self.height))
        
        try:
            total_frames = int(self.duration * self.fps)
            for frame_num in range(total_frames):
                progress = frame_num / total_frames
                frame = self.create_frame(actor, movies_with_descriptors, progress)
                out.write(frame)
                
                if progress_callback:
                    progress_callback(progress)
        finally:
            out.release()

    def generate_video_helper(self, actor: Actor, movies: List[Movie] = None,
                            movies_with_descriptors: List[Tuple[Movie, str]] = None,
                            output_path: str = "",
                            progress_callback: Optional[Callable[[float], None]] = None):
        if movies_with_descriptors is None:
            if movies is None:
                print("No movies provided")
                return
            movies_with_descriptors = [
                (movies[0], "Critics Least Favorite"),
                (movies[1], "Audience Least Favorite"),
                (movies[2], "Most Successful"),
                (movies[3], "Audience Favorite"),
                (movies[4], "Critics Favorite")
            ]
        
        if output_path == "":
            output_path = f"{actor.name} quiz.mp4"
        
        self.generate_video(actor, movies_with_descriptors, output_path, progress_callback)

if __name__ == "__main__":
    movie1 = Movie("role models", "2024", "$100M", "85%", "90%","")
    movie2 = Movie("Prestige", "2023", "$150M", "75%", "30%","")
    movie3 = Movie("Alien", "2022", "$200M", "95%", "100%","")
    movie4 = Movie("Red", "2021", "$120M", "41%", "85%","")
    movie5 = Movie("Moana", "2020", "$180M", "90%", "95%","")
    movies = [movie1, movie2, movie3, movie4, movie5]
    actor = Actor("Dwayne Johnson", movies, "Dwayne_Johnson.jpg")
    
    def update_progress(progress):
        sys.stdout.write(f"\rProgress: {progress*100:.1f}%")
        sys.stdout.flush()

    generator = OpenCVShortsGenerator(duration=20, title_phase_percentage=30)
    generator.generate_video_helper(actor, movies=movies, progress_callback=update_progress)
