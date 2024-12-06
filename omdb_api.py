import requests
import os
Master_api_key = '66f234c0'
def download_movie_posters_omdb(movie_titles, output_folder,api_key=Master_api_key):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    base_url = "http://www.omdbapi.com/"

    # Check if movie_titles is a single string or a list
    if isinstance(movie_titles, str):
        movie_titles = [movie_titles]

    for title in movie_titles:
        # Make a request to the OMDB API
        params = {
            'apikey': api_key,
            't': title,
            'plot': 'short',
            'r': 'json'
        }
        response = requests.get(base_url, params=params)
        movie_data = response.json()

        # Check if the movie was found and has a poster
        if movie_data.get('Response') == 'True' and movie_data.get('Poster') != 'N/A':
            poster_url = movie_data['Poster']
            
            # Get the image file name
            img_name = f"{title.replace(' ', '_').replace('/', '_').replace('?', '').replace(':', '')}.jpg"
            
            # Download the image
            img_data = requests.get(poster_url).content
            
            # Save the image
            try:
                with open(os.path.join(output_folder, img_name), 'wb') as handler:
                    handler.write(img_data)
                
                print(f"Downloaded: {img_name}")
                return True
            except Exception as e:
                print(f"Error downloading poster for {title}: {str(e)}")
                return False
        else:
            print(f"No poster found for: {title}")
            return False
def download_single_poster_omdb(movie_title, api_key=Master_api_key):
    """
    Downloads a single movie poster from OMDB API.
    
    Args:
        movie_title (str): Title of the movie to get poster for
        api_key (str): OMDB API key (defaults to Master_api_key)
        
    Returns:
        bytes: Raw image data if poster was found and downloaded successfully
        None: If poster could not be found or downloaded
    """
    base_url = "http://www.omdbapi.com/"
    
    # Query OMDB API
    params = {
        'apikey': api_key,
        't': movie_title,
        'plot': 'short',
        'r': 'json'
    }
    response = requests.get(base_url, params=params)
    movie_data = response.json()

    # Check if movie found and has poster
    if movie_data.get('Response') == 'True' and movie_data.get('Poster') != 'N/A':
        poster_url = movie_data['Poster']
        
        try:
            # Download image
            img_data = requests.get(poster_url).content
            return img_data
            
        except Exception as e:
            print(f"Error downloading poster for {movie_title}: {str(e)}")
            return None
    else:
        print(f"No poster found for: {movie_title}")
        return None


def get_genre_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('Genre', None)

def get_director_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('Director', None)    
  
def get_title_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('Title', None)

def get_year_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('Year', None)

def get_rated_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('Rated', None)

def get_releaseDate_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('Released', None)

def get_runtime_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('Runtime', None)

def get_writer_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('Writer', None)

def get_actors_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('Actors', None)

def get_plot_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('Plot', None)

def get_language_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('Language', None)

def get_country_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('Country', None)

def get_awards_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('Awards', None)

def get_poster_url_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('Poster', None)

def get_ratings_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('Ratings', None)

def get_metascore_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('Metascore', None)

def get_imdb_rating_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('imdbRating', None)

def get_imdb_votes_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('imdbVotes', None)

def get_imdb_id_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('imdbID', None)

def get_type_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('Type', None)

def get_dvd_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('DVD', None)

def get_box_office_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('BoxOffice', None)

def get_production_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('Production', None)

def get_website_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('Website', None)

def get_movie_actors_from_omdb(api_key, movie_title):
    return get_movie_data(api_key, movie_title).get('Actors', None)


def get_movie_data(api_key, movie_title):
    base_url = "http://www.omdbapi.com/"
    params = {
        'apikey': Master_api_key,
        't': movie_title,
        'r': 'json'
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        box_office = data.get('BoxOffice', None)
        if box_office:
            try:
                # Remove '$' and ',' from the string and convert to float
                data['BoxOffice'] = float(box_office.replace('$', '').replace(',', ''))                
            except ValueError:
                print(f"Error converting box office value '{box_office}' to float")
                data['BoxOffice'] = -1
        else:
            data['BoxOffice'] = -1
        return data
    else:
        print(f"Error fetching data: {response.status_code} - {response.text}")
        return {}

def get_box_office_from_omdb(api_key, movie_title):
    box_office = get_movie_data(api_key, movie_title).get('BoxOffice', None)
    if box_office:
        try:
            # Remove '$' and ',' from the string and convert to float
            return float(box_office.replace('$', '').replace(',', ''))
        except ValueError:
            print(f"Error converting box office value '{box_office}' to float")
            return -1
    return -1

def download_movie_posters(api_key, movie_titles, output_folder):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    base_url = "http://www.omdbapi.com/"

    # Check if movie_titles is a single string or a list
    # if isinstance(movie_titles, str):
        # movie_titles = [movie_titles]

    for title in movie_titles:
        # Make a request to the OMDB API
        params = {
            'apikey': api_key,
            't': title,
            'plot': 'short',
            'r': 'json'
        }
        response = requests.get(base_url, params=params)

        # Check if the response is successful
        if response.status_code == 200:
            try:
                movie_data = response.json()
            except requests.exceptions.JSONDecodeError:
                print(f"Error decoding JSON for movie: {title}")
                continue
        else:
            print(f"Error fetching data for {title}: {response.status_code} - {response.text}")
            continue

        # Check if the movie was found and has a poster
        if movie_data.get('Response') == 'True' and movie_data.get('Poster') != 'N/A':
            poster_url = movie_data['Poster']
            
            # Get the image file name
            img_name = f"{title.replace(' ', '_').replace('/', '_').replace('?', '').replace(':', '')}.jpg"
            
            # Download the image
            img_data = requests.get(poster_url).content
            
            # Save the image
            try:
                with open(os.path.join(output_folder, img_name), 'wb') as handler:
                    handler.write(img_data)
                
                print(f"Downloaded: {img_name}")
                # return os.path.join(output_folder, img_name)
            except Exception as e:
                print(f"Error downloading poster for {title}: {str(e)}")
                return False
        else:
            print(f"No poster found for: {title}")
            return False
