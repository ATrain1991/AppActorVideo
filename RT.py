import random
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from datetime import datetime, time

from Actor import Actor
import HelperMethods
from Movie import Movie
import omdb_api

class RottenTomatoes:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.base_url = "https://www.rottentomatoes.com"
        
    def get_actor_url_soup(self, actor_name):
        formatted_name = actor_name.lower().replace(' ', '_').replace('.', '').replace("'", "").replace('-','_')
        url = f'https://www.rottentomatoes.com/celebrity/{formatted_name}'
        
        # Fetch the page content
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch data for {actor_name}. Status code: {response.status_code}")
            return None  
        else:
            print(f"Successfully fetched data for {actor_name}")
            return BeautifulSoup(response.text, 'html.parser')
            
    def _get_soup(self, url):
            """Make request with error handling and rate limiting"""
            self.base_url = "https://www.rottentomatoes.com"
            try:
                time.sleep(random.uniform(1, 3))  # Rate limiting
                full_url = urljoin(self.base_url, url)
                response = requests.get(full_url, headers=self.headers)
                response.raise_for_status()
                return BeautifulSoup(response.text, 'html.parser')
            except Exception as e:
                print(f"Error fetching {url}: {str(e)}")
                return None

    def get_movie_poster_path(self, movie_path):
        soup = self._get_soup(movie_path)
        if not soup:
            return None
        poster_element = None
        try:
            if '/m/' in movie_path:
                poster_element = soup.find('rt-img', attrs={'slot': 'posterImage'})
            else:
                poster_element = soup.find('img', attrs={'data-qa': 'poster-image'})
        except Exception as e:
            print(f"Error finding poster element for {movie_path}: {str(e)}")
            return None
        return poster_element['src'] if poster_element else None
        
    def get_actor_portrait(self, actor_name):
        soup = self.get_actor_url_soup(actor_name)
        if not soup:
            return None

        import os
        images = soup.find_all('img')
        portrait_element = soup.find('img', alt=lambda alt: alt and 'portrait photo of' in alt.lower() and actor_name.lower() in alt.lower())
        if portrait_element:
            portrait_url = portrait_element['src']
            response = requests.get(portrait_url)
            if response.status_code == 200:
                output_folder = 'actor_portraits'
                if not os.path.exists(output_folder):
                    os.makedirs(output_folder)
                file_path = os.path.join(output_folder, f"{actor_name.replace(' ', '_').lower()}.jpg")
                with open(file_path, 'wb') as file:
                    file.write(response.content)
                return file_path
            else:
                print(f"Failed to download portrait for {actor_name}. Status code: {response.status_code}")
                return None
        else:
            print(f"Failed to find portrait for {actor_name}")
            return None

    def get_actor_birthdate(self, actor_name):
        # Update or add the birthdate to the actor in the database
            from datetime import datetime
            soup=self.get_actor_url_soup(actor_name)

            birthday_element = soup.find('p', class_='celebrity-bio__item', attrs={'data-qa': 'celebrity-bio-bday'})
            birthday_text = birthday_element.text.strip().split(':')[-1].strip()
            try:
                return datetime.strptime(birthday_text, '%b %d, %Y').date()
            except ValueError:
                print(f"Failed to parse birthday: {birthday_text}")

    def scrape_movie(self, movie_url):
        """Scrape movie details and associated actors"""

            
        if not self._should_update(movie_url, 'movies'):
            print(f"Skipping recently scraped movie: {movie_url}")
            return

        print(f"Scraping movie: {movie_url}")
        
        soup = self._get_soup(movie_url)
        if not soup:
            return

        try:
            movie_data = {
                'url': movie_url,
                'poster': soup.find('rt-img', attrs={'slot': 'posterImage'})['src'] if soup.find('rt-img', attrs={'slot': 'posterImage'}) else None,
                'title': soup.find('rt-text', {'slot': 'title'}).text.strip() if soup.find('rt-text', {'slot': 'title'}) else 'Unknown',
                'year': None,
                'tomato_score': None,
                'popcorn_score': None,
                'cast': []
            }

            # Extract year
            year_elem = soup.find('span', class_='year')
            if year_elem:
                try:
                    movie_data['year'] = int(year_elem.text.strip('()'))
                except ValueError:
                    pass

            # Extract rating
            tomato_score_elem = soup.find('rt-text', {'slot': 'criticsScore'})
            if tomato_score_elem:
                movie_data['tomato_score'] = tomato_score_elem.text.strip('%')
                
            popcorn_score_elem = soup.find('rt-text', {'slot': 'audienceScore'})
            if popcorn_score_elem:
                movie_data['popcorn_score'] = popcorn_score_elem.text.strip('%')
            return movie_data

        except Exception as e:
            print(f"Error parsing movie {movie_url}: {str(e)}")
            
    def scrape_actor_data(self, actor_name):
        # Format the actor name for the URL
        soup= self.get_actor_url_soup(actor_name)
        if not soup:
            return None
    #remove tv section
        tv_section = soup.find('rt-text', string=lambda text: text and text.strip() == 'TV')
        if tv_section:
            # Remove everything after the TV section
            for element in tv_section.find_all_next():
                element.decompose()

        # Scrape movies data
        movies_data = []
        for row in soup.select('tr[data-title]'):

            #skip if no score
            audience_score_elem = row.select_one('.celebrity-filmography__no-score[data-audiencescore="0"]')
            tomatometer_elem = row.select_one('.celebrity-filmography__no-score[data-tomatometer="0"]')
            if audience_score_elem or tomatometer_elem:
                continue


            title = row.select_one('.celebrity-filmography__title a')
            title = title.text.strip() if title else None

            year_elem = row.select_one('.celebrity-filmography__year')
            year = year_elem.text.strip() if year_elem else None

            
            tomatometer = row.select_one('.icon__tomatometer-score').text.strip()

            box_office_elem = row.select_one('.celebrity-filmography__box-office')
            if box_office_elem:
                if '$' not in box_office_elem.text.strip():
                    continue
                box_office = box_office_elem.text.strip()
                numeric_box_office = HelperMethods.get_float_from_box_office(box_office)
                if numeric_box_office and numeric_box_office < 1000:
                    box_office = omdb_api.get_box_office_from_omdb(title)
            else:
                box_office = None

            popcornmeter = row.select_one('[data-audiencescore] rt-text').text.strip()

            credit_elem = row.select_one('.celebrity-filmography__credits')
            credit = credit_elem.text.strip() if credit_elem else None

            # Create Movie object
            movie_obj = Movie(title, year, box_office, "", tomatometer, popcornmeter, credit)
            movies_data.append(movie_obj)
        return Actor(actor_name, movies_data)