
from dataclasses import dataclass
from typing import Tuple

@dataclass
class LayoutConfig:
    def __init__(self, width=1080, height=1920):
        # Base dimensions
        self.width = width
        self.height = height
        
        # Layout measurements
        self.row_height = 320
        self.poster_width = 180
        self.margin = 40
        self.padding = 15
        self.icon_size = 40
        self.vertical_spacing = (self.height - 100) // 6
        self.actor_start_size = 400
        
        # Font sizes
        self.clue_counter_size = 60
        self.movie_title_size = 40
        self.score_size = 30
        self.box_office_size = 30
        self.descriptor_size = 30
        self.actor_name_size = 60
        self.actor_comment_size = 40
        
        # Text colors
        self.text_colors = {
            'white': (255, 255, 255),
            'yellow': (255, 255, 0),
            'gray': (100, 100, 100),
            'dark_gray': (40, 40, 40),
            'light_gray': (200, 200, 200),
            'outline': (0, 0, 0)
        }
        
        # Scoring levels
        self.level_ranges = [
            ("MOVIE BUFF (1-3 Clues)", (1, 3)),
            ("FILM FAN (4-6 Clues)", (4, 6)),
            ("CASUAL VIEWER (7-9 Clues)", (7, 9)),
            ("MOVIE NOVICE (10+ Clues)", (10, 11))
        ]