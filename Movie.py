from datetime import datetime
import HelperMethods


class Movie:
    def __init__(self, title, year, box_office, poster_path, tomatometer, popcornmeter, credit):
        self.title = title
        self.year = year
        self.box_office = box_office
        self.poster_path = poster_path
        self.tomatometer = tomatometer
        self.popcornmeter = popcornmeter
        self.credit = credit    
    def get_display_box_office(self):
        # if ['B', 'M', 'K'] in self.box_office:
            return self.box_office  
        # else:
        #     return HelperMethods.get_float_from_box_office(self.box_office)
    
    def get_display_tomatometer(self):
        if "%" in self.tomatometer:
            return self.tomatometer
        else:
            return f"{self.tomatometer}%"
    def get_numeric_box_office(self):
        return HelperMethods.get_float_from_box_office(self.box_office)
    def get_display_popcornmeter(self):
        if "%" in self.popcornmeter:
            return self.popcornmeter
        else:
            return f"{self.popcornmeter}%"
    
    def get_display_credit(self):
        return self.credit
    
    def get_display_year(self):
        return f"{self.year}"
    
    def get_poster(self):
        return self.poster_path
    
    def get_title(self):
        return self.title
    def movie_released(self):
        return int(self.year)<datetime.now().year
    def get_tomatometer_int(self):
        if 'No' in self.tomatometer:
            return -1
        return int(self.tomatometer.replace('%', '')) if self.tomatometer else -1
    def get_popcornmeter_int(self):
        if 'No' in self.popcornmeter:
            return -1
        return int(self.popcornmeter.replace('%', '')) if self.popcornmeter else -1
