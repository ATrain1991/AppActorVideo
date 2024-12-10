import cv2
import numpy as np
from typing import Optional, Tuple, Dict
import os
from Actor import Actor
from Movie import Movie
from layout_config import LayoutConfig
from opencv_font_handler import OpenCVFontHandler

class DrawingUtils:
    def __init__(self, config, font_handler):
        self.config = config
        self.font_handler = font_handler

    def load_image_from_url_or_path(self, url_or_path: str) -> Optional[np.ndarray]:
        """Load an image from either a URL or local path using OpenCV"""
        try:
            if url_or_path.startswith(('http://', 'https://')):
                import requests
                response = requests.get(url_or_path)
                img_array = np.frombuffer(response.content, np.uint8)
                return cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)  # Changed to IMREAD_UNCHANGED
            else:
                return cv2.imread(url_or_path, cv2.IMREAD_UNCHANGED)  # Changed to IMREAD_UNCHANGED
        except Exception as e:
            print(f"Error loading image: {e}")
            return None
    def draw_mystery_poster(self, frame: np.ndarray, x: int, y: int, width: int, height: int):
        """Draw placeholder for unrevealed movie posters"""
        # Draw background rectangle
        cv2.rectangle(frame, (x, y), (x + width, y + height),
                    (40, 40, 40), -1)  # Filled rectangle
        
        # Draw outline
        cv2.rectangle(frame, (x, y), (x + width, y + height),
                    (100, 100, 100), 1)  # Outline
        
        # Draw question mark
        font_size = min(width, height) // 2
        text = "?"
        text_width, text_height = self.font_handler.get_text_size(text, font_size)
        text_x = x + (width - text_width) // 2
        text_y = y + (height + text_height) // 2
        
        self.font_handler.put_text(frame, text, (text_x, text_y),
                                font_size, (150, 150, 150))

    def draw_clue_counter(self, frame: np.ndarray, current_phase: dict):
        """Draw the clue counter with enhanced styling"""
        # Get the clue count from the phase
        clues = self.count_revealed_clues(current_phase)
        counter_text = f"{clues}"
        
        # Get text size using the configured clue counter size
        text_width, text_height = self.font_handler.get_text_size(
            counter_text, self.config.clue_counter_size)
        
        # Calculate position (top right corner)
        x = self.config.width - text_width - 30
        y = 30
        
        # Draw counter background
        padding = self.config.padding
        cv2.rectangle(frame,
                    (x - padding, y - padding),
                    (x + text_width + padding, y + text_height + padding),
                    self.config.text_colors['dark_gray'], -1)  # Filled rectangle
        
        cv2.rectangle(frame,
                    (x - padding, y - padding),
                    (x + text_width + padding, y + text_height + padding),
                    self.config.text_colors['gray'], 1)  # Border
        
        # Draw counter text with outline
        self.font_handler.put_text(
            frame,
            counter_text,
            (x, y + text_height),
            self.config.clue_counter_size,
            self.config.text_colors['white'],
            outline_color=self.config.text_colors['outline'],
            outline_thickness=2
        )
    def count_revealed_clues(self, current_phase: dict) -> int:
        """Count number of revealed clues based on current phase"""
        clues = 0
        if current_phase['type'] == 'title_reveal':
            clues = current_phase['index'] + 1
        elif current_phase['type'] == 'poster':
            clues = 5 + current_phase['index'] + 1
        elif current_phase['type'] in ['actor_reveal', 'final_frame']:
            clues = 11
        return clues
    def draw_movie_info(self, frame: np.ndarray, movie: Movie, y_pos: int):
        """Draw movie information including title, scores, and box office"""
        title_y = y_pos + (self.config.row_height // 2) + 15
        current_x = self.config.width - self.config.margin
        
        # Draw box office
        box_office_text = movie.get_display_box_office()
        box_office_width, _ = self.font_handler.get_text_size(box_office_text, self.config.box_office_size)
        current_x -= box_office_width
        self.font_handler.put_text(frame, box_office_text,
                                (current_x, title_y),
                                self.config.box_office_size,
                                self.config.text_colors['yellow'])
        
        current_x -= self.config.margin * 2
        
        # Draw scores
        for score_type in ['popcornmeter', 'tomatometer']:
            score = (movie.get_display_popcornmeter() if score_type == 'popcornmeter' 
                    else movie.get_display_tomatometer())
            score_value = (movie.get_popcornmeter_int() if score_type == 'popcornmeter'
                         else movie.get_tomatometer_int())
            
            score_width, _ = self.font_handler.get_text_size(score, self.config.score_size)
            current_x -= (score_width + self.config.icon_size + self.config.margin)
            
            self.font_handler.put_text(frame, score,
                                    (current_x, title_y),
                                    self.config.score_size,
                                    self.config.text_colors['white'])
            
            self.draw_score(frame,
                          current_x + score_width + self.config.margin,
                          title_y - self.config.icon_size//2,
                          score_value,
                          "",
                          f"icons/Fresh{score_type.capitalize()}.png",
                          f"icons/Rotten{score_type.capitalize()}.png")
            
            current_x -= self.config.margin * 2
        
        # Draw title
        self.font_handler.put_text(frame, movie.get_title(),
                                (self.config.poster_width + self.config.margin * 2, title_y),
                                self.config.movie_title_size,
                                self.config.text_colors['white'])

    def draw_score(self, frame: np.ndarray, x: int, y: int,
                  score: int, display_score: str, fresh_icon: str, rotten_icon: str):
        """Draw score icons with proper blending"""
        icon_path = fresh_icon if score > 60 else rotten_icon
        icon = self.load_image_from_url_or_path(icon_path)
        
        if icon is not None:
            icon = cv2.resize(icon, (self.config.icon_size, self.config.icon_size))
            
            # Handle transparency for both 3 and 4 channel images
            if len(icon.shape) == 2:  # Grayscale
                alpha = np.ones((self.config.icon_size, self.config.icon_size))
                icon = cv2.cvtColor(icon, cv2.COLOR_GRAY2BGR)
            elif icon.shape[2] == 4:  # RGBA
                alpha = icon[:, :, 3] / 255.0
                icon = icon[:, :, :3]
            else:  # BGR
                alpha = np.ones((self.config.icon_size, self.config.icon_size))
            
            y1, y2 = y, y + self.config.icon_size
            x1, x2 = x, x + self.config.icon_size
            
            # Ensure coordinates are within frame bounds
            y1 = max(0, min(y1, frame.shape[0]))
            y2 = max(0, min(y2, frame.shape[0]))
            x1 = max(0, min(x1, frame.shape[1]))
            x2 = max(0, min(x2, frame.shape[1]))
            
            # Adjust alpha and icon dimensions to match ROI size
            alpha = alpha[:(y2-y1), :(x2-x1)]
            icon = icon[:(y2-y1), :(x2-x1)]
            
            # Blend icon
            for c in range(3):
                frame[y1:y2, x1:x2, c] = (
                    frame[y1:y2, x1:x2, c] * (1 - alpha) +
                    icon[:, :, c] * alpha
                )

    def draw_actor_text(self, frame: np.ndarray, actor: Actor, y_position: int):
        """Draw engaging text for actor reveal"""
        # Draw actor name
        name_text = actor.name.upper()
        name_width, name_height = self.font_handler.get_text_size(
            name_text, self.config.actor_name_size)
        name_x = (self.config.width - name_width) // 2
        name_y = y_position
        
        self.font_handler.put_text(
            frame, name_text, (name_x, name_y),
            self.config.actor_name_size,
            self.config.text_colors['white'],
            outline_color=self.config.text_colors['outline'],
            outline_thickness=3
        )
        
        # Draw call to action
        comment_text = "Comment your score!"
        comment_width, comment_height = self.font_handler.get_text_size(
            comment_text, self.config.actor_comment_size)
        comment_x = (self.config.width - comment_width) // 2
        comment_y = name_y + comment_height + 30
        
        self.font_handler.put_text(
            frame, comment_text, (comment_x, comment_y),
            self.config.actor_comment_size,
            self.config.text_colors['yellow'],
            outline_color=self.config.text_colors['outline'],
            outline_thickness=2
        )
        
        # Draw scoring levels
        current_y = comment_y + comment_height + 40
        for level_text, (min_clues, max_clues) in self.config.level_ranges:
            level_width, level_height = self.font_handler.get_text_size(
                level_text, self.config.actor_comment_size - 5)
            level_x = (self.config.width - level_width) // 2
            
            self.font_handler.put_text(
                frame, level_text, (level_x, current_y),
                self.config.actor_comment_size - 5,
                self.config.text_colors['white'],
                outline_color=self.config.text_colors['outline'],
                outline_thickness=2
            )
            current_y += level_height + 20

    def draw_actor(self, frame: np.ndarray, actor: Actor, progress: float):
            """Draw the actor reveal animation with enhanced text"""
            if actor.url and os.path.exists(actor.url):
                actor_image = self.load_image_from_url_or_path(actor.url)
                if actor_image is not None:
                    # Animation progress
                    t = progress
                    ease_progress = 1 - (1 - t) * (1 - t) * (1 - t)
                    
                    # Calculate size and position
                    target_size = min(self.config.width, self.config.height)
                    current_size = int(self.config.actor_start_size + 
                                    (target_size - self.config.actor_start_size) * ease_progress)
                    
                    # Resize maintaining aspect ratio
                    img_h, img_w = actor_image.shape[:2]
                    aspect_ratio = img_w / img_h
                    
                    if aspect_ratio > 1:
                        width = current_size
                        height = int(current_size / aspect_ratio)
                    else:
                        height = current_size
                        width = int(current_size * aspect_ratio)
                    
                    # Resize actor image
                    actor_image = cv2.resize(actor_image, (width, height), interpolation=cv2.INTER_LANCZOS4)
                    
                    # Calculate position
                    x = (self.config.width - width) // 2
                    y = (self.config.height - height) // 2
                    
                    # Create alpha mask for smooth blending
                    alpha = np.full((height, width, 1), progress, dtype=np.float32)
                    
                    # Blend actor image with frame
                    roi = frame[y:y+height, x:x+width]
                    blended = cv2.addWeighted(roi, 1 - progress, actor_image, progress, 0)
                    frame[y:y+height, x:x+width] = blended
                    
                    # Draw text overlay
                    if progress > 0.8:  # Only show text near end of animation
                        text_alpha = min(1.0, (progress - 0.8) * 5)  # Fade in text
                        temp_frame = frame.copy()
                        self.draw_actor_text(temp_frame, actor, 50)  # Adjust Y position as needed
                        cv2.addWeighted(temp_frame, text_alpha, frame, 1 - text_alpha, 0, frame)
    def draw_row(self, frame: np.ndarray, y_pos: int, movie: Optional[Movie],
                descriptor: str, current_phase: dict, poster_index: Optional[int],
                phase_progress: float):
        """Draw a single row including descriptor, poster, and movie info"""
        # Always draw descriptor
        text_y = y_pos + 30  # Small padding from top of poster
        self.font_handler.put_text(
            frame,
            descriptor,
            (self.config.poster_width + 40, text_y),
            self.config.descriptor_size,
            self.config.text_colors['light_gray']
        )

        # Always draw the mystery poster rectangle
        self.draw_mystery_poster(frame, 0, y_pos, self.config.poster_width, self.config.row_height)
        
        # Show movie info if provided
        if movie is not None:
            self.draw_movie_info(frame, movie, y_pos)