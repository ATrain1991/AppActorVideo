import os
import cv2
import numpy as np
from typing import Optional, Tuple
from Actor import Actor
from Movie import Movie
from typing import List
import subprocess


class PreBuiltBackgroundVideo:
    def __init__(self, image1_path: str, image2_path: str, image3_path: str,
                 duration1: float, duration2: float, duration3: float,
                 movies: List[Movie],
                 width: int = 1080, height: int = 1920):
        self.width = width
        self.height = height
        self.duration = duration1 + duration2 + duration3
        
        # Load and resize images
        self.image1 = self._load_and_resize_image(image1_path)
        self.image2 = self._load_and_resize_image(image2_path) 
        self.image3 = self._load_and_resize_image(image3_path)
        
        # Store timing information
        self.breakpoints = [
            {
                'start': 0,
                'end': duration1,
                'type': 'image1'
            },
            {
                'start': duration1,
                'end': duration1 + duration2,
                'type': 'image2'
            },
            {
                'start': duration1 + duration2,
                'end': self.duration,
                'type': 'image3'
            }
        ]
        self.transition_masks = {
            '1to2': self._create_transition_mask(self.image1, self.image2),
            '2to3': self._create_transition_mask(self.image2, self.image3)
        }
        self.fade_duration = 0.5  # 1 second fade between images
         
        poster_reveal_percentage = 0.65
        # Store title and poster reveal timing info

        self.title_reveal_duration = duration2 * (1-poster_reveal_percentage) / 5  # First half for titles
        self.poster_reveal_duration = duration2 * poster_reveal_percentage / 6  # Second half for posters
        
        self.movies = movies[:5]  # Limit to 5 movies maximum
        self.cached_posters = {}
        for movie in self.movies:
            try:
                poster_data = movie.get_poster_from_omdb()
                if poster_data:
                    poster = cv2.imdecode(np.frombuffer(poster_data, np.uint8), cv2.IMREAD_UNCHANGED)
                    if poster is not None:
                        self.cached_posters[movie.get_title()] = cv2.resize(poster, (255, 384))
            except Exception as e:
                print(f"Could not cache poster for {movie.get_title()}: {str(e)}")
    def _create_transition_mask(self, img1: np.ndarray, img2: np.ndarray) -> np.ndarray:
            """Create a mask highlighting differences between two images."""
            # Convert to grayscale for difference detection
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
            # Calculate absolute difference
            diff = cv2.absdiff(gray1, gray2)
            
            # Apply threshold to get binary mask
            _, mask = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
            
            # Apply gaussian blur to smooth the mask
            mask = cv2.GaussianBlur(mask, (21, 21), 0)
            
            # Dilate the mask to include surrounding areas
            kernel = np.ones((5,5), np.uint8)
            mask = cv2.dilate(mask, kernel, iterations=2)
            
            # Convert back to 3 channel
            return cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0

    def get_frame(self, progress: float) -> np.ndarray:
        current_time = progress * self.duration
        
        # Find current phase
        current_phase = None
        for breakpoint in self.breakpoints:
            if breakpoint['start'] <= current_time <= breakpoint['end']:
                current_phase = breakpoint
                break
                
        if current_phase is None:
            return self.image3.copy()
            
        # Handle transitions
        frame = None
        
        # Transition from image1 to image2
        if current_phase['type'] == 'image1':
            frame = self.image1.copy()
            if current_time > (current_phase['end'] - self.fade_duration):
                fade_progress = (current_time - (current_phase['end'] - self.fade_duration)) / self.fade_duration
                frame = cv2.addWeighted(self.image1, 1 - fade_progress, self.image2, fade_progress, 0)
                
        # Image2 phase with transitions on both ends
        elif current_phase['type'] == 'image2':
            # Fade in from image1
            if current_time < (current_phase['start'] + self.fade_duration):
                fade_progress = (current_time - current_phase['start']) / self.fade_duration
                frame = cv2.addWeighted(self.image1, 1 - fade_progress, self.image2, fade_progress, 0)
            # Fade out to image3
            elif current_time > (current_phase['end'] - self.fade_duration):
                fade_progress = (current_time - (current_phase['end'] - self.fade_duration)) / self.fade_duration
                frame = cv2.addWeighted(self.image2, 1 - fade_progress, self.image3, fade_progress, 0)
            # Middle of image2 phase
            else:
                frame = self.image2.copy()
            
            # Add dynamic reveals during image2 phase
            if frame is not None:
                phase_progress = (current_time - current_phase['start']) / (current_phase['end'] - current_phase['start'])
                self._add_reveals(frame, phase_progress)
                
        # Transition from image2 to image3
        else:  # image3
            frame = self.image3.copy()
            if current_time < (current_phase['start'] + self.fade_duration):
                fade_progress = (current_time - current_phase['start']) / self.fade_duration
                frame = cv2.addWeighted(self.image2, 1 - fade_progress, self.image3, fade_progress, 0)
        
        return frame

    def _load_and_resize_image(self, image_path: str) -> np.ndarray:
        # Check if file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Failed to load image: {image_path}")
        
        # Resize image
        return cv2.resize(img, (self.width, self.height))
        
    def _add_reveals(self, frame: np.ndarray, progress: float):
        """Add title and poster reveals during image2 phase"""
        # Calculate how many items should be revealed based on progress
        if progress < 0.5:
            # During first half, reveal titles one at a time
            reveal_count = int(progress * 10)  # Scale for smooth title reveals
            title_index = min(len(self.movies), reveal_count)
        else:
            title_index = len(self.movies)

        # Add titles and metadata
        for i in range(title_index):
            self._add_movie_text(frame, self.movies[i], i)

        # Add posters if we're in the poster reveal phase
        if progress > 0.5:
            poster_progress = (progress - 0.5) * 2  # Scale 0.5-1.0 to 0-1.0
            
            # Calculate poster index based on actual number of movies
            base_index = int(poster_progress * len(self.movies))
            
            # Hold the final poster longer by requiring higher progress
            if base_index >= len(self.movies) - 1 and poster_progress < 0.85:
                poster_index = len(self.movies) - 1
            else:
                poster_index = min(len(self.movies), base_index)
                
            for i in range(poster_index):
                self._add_movie_poster(frame, self.movies[i], i)
    def _add_movie_text(self, frame: np.ndarray, movie: Movie, index: int):
        """Add title and metadata for a single movie in a horizontal layout"""
        # Constants for positioning
        base_y = 212
        poster_width = 255
        text_padding = 25
        icon_size = 100  # Smaller icons for the horizontal layout
        text_start_x = poster_width + text_padding
        
        # Calculate vertical position for this movie
        offset_y = base_y + int(384 * index)
        
        # Draw semi-transparent background behind all text and icons
        title_text = f"{movie.get_title()}  -  ({movie.get_display_year()})"
        text_size = cv2.getTextSize(title_text, cv2.FONT_HERSHEY_SIMPLEX, 1.1, 2)[0]
        
        # Calculate total height needed for title and metrics
        total_height = text_size[1] + icon_size + 20  # Title height + icon height + padding
        
        # Calculate total width needed
        total_width = 1000  # Approximate width needed for all elements
        
        bg_y_start = offset_y - text_size[1] - 5  # Position above baseline
        
        # Create and apply background overlay for entire content area
        bg_overlay = frame[bg_y_start:bg_y_start+total_height, 
                         text_start_x:text_start_x+total_width].copy()
        cv2.rectangle(bg_overlay, (0, 0), (total_width, total_height), (0, 0, 0), -1)
        frame[bg_y_start:bg_y_start+total_height, 
              text_start_x:text_start_x+total_width] = cv2.addWeighted(
            frame[bg_y_start:bg_y_start+total_height, text_start_x:text_start_x+total_width],
            0.3,
            bg_overlay,
            0.7,
            0
        )
        
        # Draw title
        cv2.putText(frame, title_text,
                    (text_start_x, offset_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2)
        
        # Start positions for horizontal layout
        metrics_y = offset_y + 50  # Space below title
        current_x = text_start_x
        
        # Add Tomatometer icon and score
        tomatometer_icon_path = "icons/FreshTomatometer.png" if movie.get_tomatometer_int() > 60 else "icons/RottenTomatometer.png"
        if os.path.exists(tomatometer_icon_path):
            self._add_icon(frame, tomatometer_icon_path, current_x, metrics_y, icon_size)
        current_x += icon_size + 10  # Space after icon
        
        # Add Tomatometer score
        tomatometer_text = f"{movie.get_display_tomatometer()}"
        cv2.putText(frame, tomatometer_text,
                    (current_x, metrics_y + icon_size//2),  # Vertically center with icon
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        text_size = cv2.getTextSize(tomatometer_text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
        current_x += text_size[0] + 30  # Space after text
        
        # Add Popcornmeter icon and score
        popcorn_icon_path = "icons/FreshPopcornmeter.png" if movie.get_popcornmeter_int() > 60 else "icons/RottenPopcornmeter.png"
        if os.path.exists(popcorn_icon_path):
            self._add_icon(frame, popcorn_icon_path, current_x, metrics_y, icon_size)
        current_x += icon_size + 10  # Space after icon
        
        # Add Popcornmeter score
        popcornmeter_text = f"{movie.get_display_popcornmeter()}"
        cv2.putText(frame, popcornmeter_text,
                    (current_x, metrics_y + icon_size//2),  # Vertically center with icon
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        text_size = cv2.getTextSize(popcornmeter_text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
        current_x += text_size[0] + 30  # Space after text
        
        # Add Box Office
        box_office_text = f"Box Office: {movie.get_display_box_office()}"
        cv2.putText(frame, box_office_text,
                    (current_x, metrics_y + icon_size//2),  # Vertically center with icons
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

    def _add_icon(self, frame: np.ndarray, icon_path: str, x: int, y: int, icon_size: int):
        """Helper function to add an icon to the frame with alpha channel support"""
        icon = cv2.imread(icon_path, cv2.IMREAD_UNCHANGED)
        if icon is not None:
            icon = cv2.resize(icon, (icon_size, icon_size))
            
            if icon.shape[2] == 4:  # If icon has alpha channel
                y1, y2 = y, y + icon_size
                x1, x2 = x, x + icon_size
                
                if y2 <= frame.shape[0] and x2 <= frame.shape[1]:  # Check bounds
                    alpha = icon[:,:,3]
                    alpha = alpha.astype(float)/255
                    alpha = np.stack([alpha]*3, axis=-1)
                    foreground = icon[:,:,:3]
                    background = frame[y1:y2, x1:x2]
                    blended = cv2.convertScaleAbs(foreground * alpha + background * (1 - alpha))
                    frame[y1:y2, x1:x2] = blended
                else:  # If icon doesn't have alpha channel
                    frame[y:y+icon_size, x:x+icon_size] = icon
    def _add_movie_poster(self, frame: np.ndarray, movie: Movie, index: int):
        """Add a movie poster to the frame"""
        poster_width = 255
        poster_height = 384
        poster_x = 0
        poster_y = int(384 * (index))
        
        # Use cached poster if available
        if hasattr(self, 'cached_posters') and movie.get_title() in self.cached_posters:
            frame[poster_y:poster_y+poster_height, 
                poster_x:poster_x+poster_width] = self.cached_posters[movie.get_title()]
            return
            
        try:
            poster_data = movie.get_poster_from_omdb()
            if poster_data:
                poster = cv2.imdecode(np.frombuffer(poster_data, np.uint8), cv2.IMREAD_UNCHANGED)
                if poster is not None:
                    poster = cv2.resize(poster, (poster_width, poster_height))
                    frame[poster_y:poster_y+poster_height, 
                        poster_x:poster_x+poster_width] = poster
                else:
                    raise ValueError("Could not decode poster image")
            else:
                raise ValueError("No poster data received")
        except Exception as e:
            print(f"No poster found for {movie.get_title()}: {str(e)}")
            # Fallback to rectangle with movie title
            cv2.rectangle(frame, 
                        (poster_x, poster_y),
                        (poster_x + poster_width, poster_y + poster_height),
                        (255, 255, 255), 2)
            cv2.putText(frame, movie.get_title(),
                    (poster_x + 20, poster_y + poster_height // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
def Create_reveal_image(actor:Actor):
    base_image = cv2.imread("backgrounds/reveal_page.jpg")
    # Calculate centered position for 750x1111 image
    # Dimensions for overlay image
    overlay_width = 750
    overlay_height = 1111
    top_margin = 200
    
    # Calculate centered position for overlay
    x_pos = (base_image.shape[1] - overlay_width) // 2
    y_pos = top_margin
    
    # Load and resize overlay image
    overlay_image = cv2.imread(f"{actor.name.replace(' ', '_')}.jpg") # Load overlay image
    if overlay_image is not None:
        overlay_image = cv2.resize(overlay_image, (overlay_width, overlay_height))
        
        # Place overlay image in centered position
        if y_pos + overlay_height <= base_image.shape[0] and x_pos + overlay_width <= base_image.shape[1]:
            base_image[y_pos:y_pos+overlay_height, x_pos:x_pos+overlay_width] = overlay_image
            
    # Save image to reveals folder with actor's name
    os.makedirs('reveals', exist_ok=True)
    output_path = os.path.join('reveals', f'{actor.name}.jpg')
    cv2.imwrite(output_path, base_image)
    return output_path

def example_usage():
        # Sample movie data
    movies = [
        Movie("role models", "2024", "100M", "85%", "90%",""),
        Movie("Prestige", "2023", "150M", "75%", "30%",""),
        Movie("Alien", "2022", "200M", "95%", "100%",""),
        Movie("Red", "2021", "120M", "41%", "85%",""),
        Movie("Red", "2021", "120M", "41%", "85%",""),
        Movie("Moana", "2020", "180M", "90%", "95%","") 
        # Add more movies as needed
    ]
    # Create background video with 3 images and specified durations
    # Make sure these images share some common elements for smooth transitions
    image1_path = os.path.join(os.path.dirname(__file__), "backgrounds", "movie_quiz_title_screen.jpg")
    image2_path = os.path.join(os.path.dirname(__file__), "backgrounds", "clue_page.jpg")
    image3_path = Create_reveal_image(Actor("Dwayne Johnson",movies))
    
    # Define durations for each phase (in seconds)
    image1_duration = 2
    image2_duration = 25.0  # Longer duration for dynamic elements
    image3_duration = 4
    total_duration = image1_duration + image2_duration + image3_duration
    

    
    # Create video instance
    video = PreBuiltBackgroundVideo(
        image1_path=image1_path,
        image2_path=image2_path, 
        image3_path=image3_path,
        duration1=image1_duration,
        duration2=image2_duration,
        duration3=image3_duration,
        movies=movies,
        width=1080,
        height=1920
    )
    
    # Set up video writer with higher quality settings
    fps = 30
    total_frames = int(total_duration * fps)
    
    # Use H.264 codec for better quality
    if os.name == 'nt':  # Windows
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
    else:  # Linux/Mac
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
    
    out = cv2.VideoWriter(
        'output_background.avi',
        fourcc,
        fps,
        (1080, 1920),
        isColor=True
    )
    
    # Generate and save frames
    for frame_num in range(total_frames):
        progress = frame_num / total_frames
        frame = video.get_frame(progress)
        
        # Ensure frame is in the correct format
        frame = cv2.convertScaleAbs(frame)
        
        # Write frame
        out.write(frame)
        
        # Preview while rendering (optional)
        preview_frame = cv2.resize(frame, (540, 960))  # Half size preview
        cv2.imshow("Preview", preview_frame)
        
        # Allow graceful exit with 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Clean up
    out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    example_usage()

