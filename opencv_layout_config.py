from dataclasses import dataclass
from typing import Dict, Tuple, List

@dataclass
class LayoutConfig:
    def __init__(self, width: int = 1080, height: int = 1920):
        # Video dimensions
        self.width = width
        self.height = height
        
        # Colors (BGR format)
        self.background_color = (20, 20, 20)
        self.text_colors = {
            'white': (255, 255, 255),
            'yellow': (0, 255, 255),
            'gray': (128, 128, 128),
            'light_gray': (200, 200, 200),
            'dark_gray': (40, 40, 40),
            'outline': (0, 0, 0)
        }
        
        # Layout dimensions
        self.icon_size = 120
        self.row_height = 320
        self.poster_width = 180
        self.actor_start_size = 400
        self.vertical_spacing = (self.height - 100) // 6
        
        # Text sizes
        self.clue_size = 10
        self.clue_counter_size = 45
        self.box_office_size = 15
        self.score_size = 15
        self.movie_title_size = 24
        self.descriptor_size = 17
        self.actor_name_size = 28
        self.actor_comment_size = 11
        
        # Scoring system
        self.level_ranges = [
            ("🏆 Movie Expert", (1, 3)),
            ("🎯 Film Buff", (4, 6)),
            ("🎬 Casual Fan", (7, 9)),
            ("🍿 Getting There!", (10, 11))
        ]
        
        # Layout spacing
        self.margin = 10
        self.padding = 10
        self.text_spacing = 20
