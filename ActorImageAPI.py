import requests
from bs4 import BeautifulSoup
from typing import Optional
import re
from io import BytesIO
import cv2
import numpy as np

def get_actor_headshot(actor_name: str) -> Optional[bytes]:
    """
    Retrieves an actor's headshot image by searching Wikipedia.
    
    Args:
        actor_name: Name of the actor to search for
        
    Returns:
        bytes of the image if found, None otherwise
    """
    try:
        # Format actor name for URL
        actor_name_formatted = actor_name.replace(" ", "_")
        
        # Search Wikipedia
        wiki_url = f"https://en.wikipedia.org/wiki/{actor_name_formatted}"
        response = requests.get(wiki_url)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find image in infobox
        infobox = soup.find('table', {'class': 'infobox'})
        if infobox:
            img_tag = infobox.find('img')
            if img_tag:
                # Get full resolution image URL
                img_url = "https:" + img_tag['src']
                if not img_url.startswith("https://upload.wikimedia.org"):
                    img_url = re.sub(r'/\d+px-', '/1000px-', img_url)
                
                # Download image
                img_response = requests.get(img_url)
                img_response.raise_for_status()
                return img_response.content
                
    except Exception as e:
        print(f"Error getting headshot for {actor_name}: {str(e)}")
        return None
        
    return None

if __name__ == "__main__":
    # Test with some example actors
    test_actors = [
        "Tom Hanks",
        "Meryl Streep",
        "Denzel Washington",
        "Morgan Freeman"
    ]
    
    for actor in test_actors:
        print(f"\nTesting with actor: {actor}")
        image_data = get_actor_headshot(actor)
        
        if image_data:
            # Convert bytes to numpy array for OpenCV
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is not None:
                # Display image dimensions
                print(f"Successfully retrieved image - Shape: {img.shape}")
                
                # Save image to file
                filename = f"{actor.replace(' ', '_')}_headshot.jpg"
                cv2.imwrite(filename, img)
                print(f"Saved image to {filename}")
            else:
                print("Failed to decode image data")
        else:
            print("Failed to retrieve image")

