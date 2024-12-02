


from dataclasses import dataclass
from typing import List
from db_manager import MovieData

@dataclass
class MovieData:
    title: str
    descriptor: str
    critics_score: int
    audience_score: int
    box_office: str
    poster_path: str
def generate_sample_data() -> List[MovieData]:
    """Generate sample movie data"""
    return [
        MovieData(
            title="Avengers: Endgame",
            descriptor="Epic Conclusion",
            critics_score=94,
            audience_score=90,
            box_office="2.799B",
            poster_path="Aquaman.jpg"
        ),
        MovieData(
            title="The Dark Knight",
            descriptor="Crime Thriller",
            critics_score=94,
            audience_score=94,
            box_office="1.005B",
            poster_path="Aquaman.jpg"
        ),
        MovieData(
            title="Inception",
            descriptor="Mind-Bending",
            critics_score=87,
            audience_score=91,
            box_office="836.8M",
            poster_path="Aquaman.jpg"
        ),
        MovieData(
            title="Interstellar",
            descriptor="Space Epic",
            critics_score=73,
            audience_score=86,
            box_office="701.7M",
            poster_path="Aquaman.jpg"
        ),
        MovieData(
            title="The Matrix",
            descriptor="Sci-Fi Classic",
            critics_score=88,
            audience_score=85,
            box_office="463.5M",
            poster_path="Aquaman.jpg"
        ),
    ]
