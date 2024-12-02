from operator import attrgetter


class Actor:
    def __init__(self, name, movies, url="", birthdate=None, bio="", oscar_wins=0, oscar_nominations=0):
        self.name = name
        self.url = url
        self.birthdate = birthdate
        self.bio = bio
        self.oscar_wins = oscar_wins
        self.oscar_nominations = oscar_nominations
        self.movies = movies
        #add to database if all fields are present
        if all([name, url, birthdate, bio, oscar_wins, oscar_nominations, movies]):
            # self.add_to_database()
            pass

    def get_worst_tomatometer(self):
        valid_movies = [m for m in self.movies if m.get_tomatometer_int() > 0]
        movie = min(valid_movies, key=lambda x: int(x.get_tomatometer_int())) if valid_movies else None
        print(f"movie: {movie.title} tomatometer: {movie.get_display_tomatometer()}")
        return movie
    def get_worst_popcornmeter(self):
        valid_movies = [m for m in self.movies if m.get_popcornmeter_int() > 0]
        movie = min(valid_movies, key=lambda x: int(x.get_popcornmeter_int())) if valid_movies else None
        print(f"movie: {movie.title} popcornmeter: {movie.get_display_popcornmeter()}")
        return movie
    def get_most_successful(self):
        valid_movies = [m for m in self.movies if m.get_numeric_box_office() > 0]
        movie = max(valid_movies, key=lambda x: int(x.get_numeric_box_office())) if valid_movies else None
        print(f"movie: {movie.title} box_office: {movie.get_display_box_office()}")
        return movie
    def get_best_tomatometer(self):
        valid_movies = [m for m in self.movies if m.get_tomatometer_int() > 0]
        movie = max(valid_movies, key=lambda x: int(x.get_tomatometer_int())) if valid_movies else None
        print(f"movie: {movie.title} tomatometer: {movie.get_display_tomatometer()}")
        return movie
    def get_best_popcornmeter(self):
        valid_movies = [m for m in self.movies if m.get_popcornmeter_int() > 0]
        movie = max(valid_movies, key=lambda x: int(x.get_popcornmeter_int())) if valid_movies else None
        print(f"movie: {movie.title} popcornmeter: {movie.get_display_popcornmeter()}")
        return movie

