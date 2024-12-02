import sqlite3
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple, Union
from datetime import datetime
import logging
from pathlib import Path

@dataclass
class MovieData:
    title: str
    descriptor: str
    critics_score: int
    audience_score: int
    year: int
    top_actors: List[str]
    actor_role: Optional[str] = None
    url: str = ""

@dataclass
class ActorData:
    name: str
    image: str
    birth_date: str
    oscar_wins: int
    oscar_nominations: int
    url: str
    roles: List[Dict[str, Union[str, int]]]

class DatabaseManager:
    def __init__(self, db_path: str = "movies.db"):
        self.db_path = db_path
        self.setup_logging()

    def setup_logging(self):
        """Configure logging for database operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('db_manager.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _connect(self):
        """Create database connection with error handling"""
        try:
            return sqlite3.connect(self.db_path)
        except sqlite3.Error as e:
            self.logger.error(f"Database connection error: {e}")
            raise

    def _parse_score(self, score: str) -> int:
        """Convert score string to integer"""
        try:
            return int(score.strip('%'))
        except (ValueError, AttributeError):
            return 0

    def _get_actor_url(self, cursor, actor_name: str) -> Optional[str]:
        """Get actor's URL from their name with fuzzy matching"""
        cursor.execute("""
            SELECT url FROM actors
            WHERE LOWER(name) LIKE LOWER(?)
        """, (f"%{actor_name}%",))
        result = cursor.fetchone()
        return result[0] if result else None

    def _get_top_actors(self, cursor, movie_url: str, max_billing: int) -> List[str]:
        """Get top-billed actors for a movie"""
        cursor.execute("""
            SELECT a.name
            FROM actors a
            JOIN movie_actors ma ON a.url = ma.actor_url
            WHERE ma.movie_url = ? AND ma.billing_order <= ?
            ORDER BY ma.billing_order
        """, (movie_url, max_billing))
        return [row[0] for row in cursor.fetchall()]

    # Actor-specific queries
    def get_actor_info(self, actor_name: str) -> Optional[ActorData]:
        """Get complete actor information including roles"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        a.url,
                        a.name,
                        a.image,
                        a.birth_date,
                        a.oscar_wins,
                        a.oscar_nominations,
                        a.last_scraped
                    FROM actors a
                    WHERE LOWER(a.name) LIKE LOWER(?)
                """, (f"%{actor_name}%",))
                
                actor_row = cursor.fetchone()
                if not actor_row:
                    return None

                # Get all roles
                cursor.execute("""
                    SELECT 
                        m.title,
                        ma.role,
                        ma.billing_order,
                        m.year
                    FROM movie_actors ma
                    JOIN movies m ON ma.movie_url = m.url
                    WHERE ma.actor_url = ?
                    ORDER BY m.year DESC, ma.billing_order
                """, (actor_row[0],))
                
                roles = [
                    {
                        "movie": row[0],
                        "role": row[1],
                        "billing_order": row[2],
                        "year": row[3]
                    }
                    for row in cursor.fetchall()
                ]

                return ActorData(
                    url=actor_row[0],
                    name=actor_row[1],
                    image=actor_row[2],
                    birth_date=actor_row[3],
                    oscar_wins=actor_row[4],
                    oscar_nominations=actor_row[5],
                    roles=roles
                )
        except sqlite3.Error as e:
            self.logger.error(f"Error getting actor info: {e}")
            return None

    # Movie ranking queries
    def get_actor_movie_by_criteria(
        self,
        actor_name: str,
        sort_by: str,
        ascending: bool = False,
        max_billing_order: int = 3,
        year_range: Optional[Tuple[int, int]] = None
    ) -> Optional[MovieData]:
        """
        Get actor's movie based on various criteria
        
        sort_by options: 'critics', 'audience', 'year'
        """
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                actor_url = self._get_actor_url(cursor, actor_name)
                if not actor_url:
                    return None

                # Build query based on criteria
                query = """
                    SELECT DISTINCT
                        m.url,
                        m.title,
                        m.year,
                        m.tomato_score,
                        m.popcorn_score,
                        ma.role,
                        ma.billing_order
                    FROM movies m
                    JOIN movie_actors ma ON m.url = ma.movie_url
                    WHERE ma.actor_url = ?
                    AND ma.billing_order <= ?
                """
                params = [actor_url, max_billing_order]

                if year_range:
                    query += " AND m.year BETWEEN ? AND ?"
                    params.extend(year_range)

                # Add sorting
                sort_column = {
                    'critics': 'CAST(REPLACE(m.tomato_score, "%", "") AS INTEGER)',
                    'audience': 'CAST(REPLACE(m.popcorn_score, "%", "") AS INTEGER)',
                    'year': 'm.year'
                }.get(sort_by, 'CAST(REPLACE(m.tomato_score, "%", "") AS INTEGER)')

                query += f" ORDER BY {sort_column} {'ASC' if ascending else 'DESC'} LIMIT 1"

                cursor.execute(query, params)
                row = cursor.fetchone()
                
                if row:
                    top_actors = self._get_top_actors(cursor, row[0], max_billing_order)
                    descriptor = self._generate_descriptor(sort_by, ascending, row[5])
                    
                    return MovieData(
                        url=row[0],
                        title=row[1],
                        year=row[2],
                        critics_score=self._parse_score(row[3]),
                        audience_score=self._parse_score(row[4]),
                        descriptor=descriptor,
                        top_actors=top_actors,
                        actor_role=row[5]
                    )
                return None
        except sqlite3.Error as e:
            self.logger.error(f"Database error in movie criteria search: {e}")
            return None

    def _generate_descriptor(self, sort_by: str, ascending: bool, role: str) -> str:
        """Generate appropriate descriptor based on search criteria"""
        if sort_by == 'critics':
            return f"{'Worst' if ascending else 'Best'} Reviewed - {role}"
        elif sort_by == 'audience':
            return f"{'Least' if ascending else 'Most'} Popular - {role}"
        elif sort_by == 'year':
            return f"{'Earliest' if ascending else 'Latest'} Role - {role}"
        return role

    # Utility functions
    def get_actor_statistics(self, actor_name: str) -> Dict[str, Union[int, float, str]]:
        """Get comprehensive statistics for an actor"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                actor_url = self._get_actor_url(cursor, actor_name)
                if not actor_url:
                    return {}

                # Get various statistics
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT m.url) as total_movies,
                        AVG(CAST(REPLACE(m.tomato_score, '%', '') AS FLOAT)) as avg_critics,
                        AVG(CAST(REPLACE(m.popcorn_score, '%', '') AS FLOAT)) as avg_audience,
                        MIN(m.year) as earliest_movie,
                        MAX(m.year) as latest_movie,
                        AVG(ma.billing_order) as avg_billing
                    FROM movies m
                    JOIN movie_actors ma ON m.url = ma.movie_url
                    WHERE ma.actor_url = ?
                    AND m.tomato_score IS NOT NULL
                    AND m.popcorn_score IS NOT NULL
                """, (actor_url,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'total_movies': row[0],
                        'average_critics_score': round(row[1], 1) if row[1] else 0,
                        'average_audience_score': round(row[2], 1) if row[2] else 0,
                        'career_span': f"{row[3]}-{row[4]}",
                        'average_billing': round(row[5], 1) if row[5] else 0
                    }
                return {}
        except sqlite3.Error as e:
            self.logger.error(f"Error getting actor statistics: {e}")
            return {}

def get_complete_actor_analysis(actor_name: str, max_billing_order: int = 3) -> Dict:
    """Get complete analysis of an actor's career"""
    db = DatabaseManager()
    
    # Get basic info
    actor_info = db.get_actor_info(actor_name)
    if not actor_info:
        return {}
    
    # Get statistics
    stats = db.get_actor_statistics(actor_name)
    
    # Get various rankings
    movies = {
        'best_critics': db.get_actor_movie_by_criteria(actor_name, 'critics', False, max_billing_order),
        'worst_critics': db.get_actor_movie_by_criteria(actor_name, 'critics', True, max_billing_order),
        'best_audience': db.get_actor_movie_by_criteria(actor_name, 'audience', False, max_billing_order),
        'worst_audience': db.get_actor_movie_by_criteria(actor_name, 'audience', True, max_billing_order),
        'most_recent': db.get_actor_movie_by_criteria(actor_name, 'year', False, max_billing_order),
        'earliest': db.get_actor_movie_by_criteria(actor_name, 'year', True, max_billing_order)
    }
    
    return {
        'actor': actor_info,
        'statistics': stats,
        'movies': movies
    }
