from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class MoviePoster:
    y_start: int
    y_end: int
    x_start: int = 0
    x_end: int = 200  # Approximate width for movie poster area

@dataclass
class ScoreLocation:
    x: int
    y: int
    width: int = 60  # Approximate width for score display
    height: int = 40  # Approximate height for score display

class MovieTemplateCoordinates:
    def __init__(self, template_width: int = 800, template_height: int = 1400):
        self.width = template_width
        self.height = template_height
        
        # Header section coordinates
        self.header_height = 200
        self.title_position = (220, 50)  # x, y for "Averages" text
        self.header_icons = {
            "profile": (50, 50),
            "calendar": (150, 50),
            "number": (250, 50)
        }
        
        # Column headers
        self.column_headers = {
            "critics": (500, 50),
            "audience": (650, 50)
        }
        
        # Initialize movie poster slots
        self.poster_slots = self._generate_poster_slots()
        
        # Score positions (critics and audience columns)
        self.critics_scores = self._generate_score_positions(x=500)
        self.audience_scores = self._generate_score_positions(x=650)

    def _generate_poster_slots(self) -> List[MoviePoster]:
        """Generate coordinates for movie poster positions"""
        poster_height = 200
        slots = []
        for i in range(6):  # 6 poster slots
            y_start = self.header_height + (i * poster_height)
            slots.append(MoviePoster(
                y_start=y_start,
                y_end=y_start + poster_height
            ))
        return slots

    def _generate_score_positions(self, x: int) -> List[ScoreLocation]:
        """Generate coordinates for score positions in a column"""
        score_positions = []
        for i in range(6):
            y = self.header_height + (i * 200) + 100  # Center in poster slot
            score_positions.append(ScoreLocation(x=x, y=y))
        return score_positions

    def get_poster_coordinates(self, index: int) -> Tuple[int, int, int, int]:
        """Get coordinates for a specific poster slot"""
        if 0 <= index < len(self.poster_slots):
            slot = self.poster_slots[index]
            return (slot.x_start, slot.y_start, slot.x_end, slot.y_end)
        raise IndexError("Poster index out of range")

    def get_score_coordinates(self, index: int, is_critic: bool = True) -> Tuple[int, int]:
        """Get coordinates for a specific score position"""
        scores = self.critics_scores if is_critic else self.audience_scores
        if 0 <= index < len(scores):
            score = scores[index]
            return (score.x, score.y)
        raise IndexError("Score index out of range")

# Example usage
def main():
    template = MovieTemplateCoordinates()
    
    # Example: Get coordinates for the first movie poster
    poster_coords = template.get_poster_coordinates(1)
    print(f"First poster coordinates: {poster_coords}")
    
    # Example: Get coordinates for the first critic score
    critic_score = template.get_score_coordinates(0, is_critic=True)
    print(f"First critic score position: {critic_score}")
    
    # Example: Get coordinates for the first audience score
    audience_score = template.get_score_coordinates(0, is_critic=False)
    print(f"First audience score position: {audience_score}")

if __name__ == "__main__":
    main()
