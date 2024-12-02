import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from datetime import datetime
import json
import os
from PIL import Image, ImageTk
import threading
from moviepy.editor import VideoFileClip
from typing import List, Dict
import requests
from dataclasses import dataclass
from operator import attrgetter

from Movie import Movie
from RT import RottenTomatoes

@dataclass
class MovieData:
    title: str
    year: int
    role: str
    critics_score: float
    audience_score: float
    box_office: str
    poster_path: str

    def get_display_tomatometer(self):
        return f"{self.critics_score}%"

    def get_display_popcornmeter(self):
        return f"{self.audience_score}%"

class MovieDataService:
    def __init__(self):
        self.actor = None
        # In a real app, this would connect to your movie database/API
        self.cache = {}
    
    def get_actor_filmography(self, actor_name: str) -> List[MovieData]:
        """Fetch all movies for an actor with their scores and data"""
        try:
            print(f"Fetching filmography for {actor_name}")
            movies = RottenTomatoes().scrape_actor_data(actor_name)
            
            # Convert RT data to MovieData objects
            movie_data = []
            for movie in movies:
                try:
                    # Clean box office string - remove $, B, M, K and commas
                    box_office_str = movie['box_office'] if movie['box_office'] else "0"
                    for char in ['$', 'B', 'M', 'K', ',']:
                        box_office_str = box_office_str.replace(char, '')
                    
                    movie_data.append(MovieData(
                        title=movie['title'],
                        year=int(movie['year']) if movie['year'] and movie['year'] != '-' else 0,
                        role=movie['role'],
                        critics_score=float(movie['critics_score']) if movie['critics_score'] and movie['critics_score'] != '-' else 0.0,
                        audience_score=float(movie['audience_score']) if movie['audience_score'] and movie['audience_score'] != '-' else 0.0,
                        box_office=int(box_office_str) if box_office_str.strip() else 0,
                        poster_path=movie['poster_path'] if movie['poster_path'] else ""
                    ))
                except (ValueError, KeyError) as e:
                    print(f"Error processing movie {movie.get('title', 'unknown')}: {e}")
                    continue
            
            return movie_data
            
        except Exception as e:
            print(f"Error in get_actor_filmography: {str(e)}")
            raise Exception(f"Failed to fetch actor data: {str(e)}")

    def get_critics_least_favorite(self, movies: List[MovieData]) -> MovieData:
        """Get movie with lowest critics score"""
        if self.actor:
            return self.actor.get_worst_tomatometer()
        else:
            return Movie("where is the movie?", 0, "", 0, 0, 0, "")
        # valid_movies = [m for m in movies if m.movie_released() and m.tomatometer != -1]
        # return min(valid_movies, key=lambda x: x.get_tomatometer_int()) if valid_movies else None
        # return min(valid_movies, key=attrgetter('tomatometer')) if valid_movies else None

    def get_audience_least_favorite(self, movies: List[MovieData]) -> MovieData:
        """Get movie with lowest audience score"""
        if self.actor:
            return self.actor.get_worst_popcornmeter()
        else:
            return Movie("where is the movie?", 0, "", 0, 0, 0, "")     
        # valid_movies = [m for m in movies if m.movie_released() and m.popcornmeter != -1]
        # return min(valid_movies, key=lambda x: x.get_popcornmeter_int()) if valid_movies else None
        # return min(valid_movies, key=attrgetter('popcornmeter')) if valid_movies else None

    def get_most_successful(self, movies: List[MovieData]) -> MovieData:
        """Get movie with highest box office"""
        if self.actor:
            return self.actor.get_most_successful()
        else:
            return Movie("where is the movie?", 0, "", 0, 0, 0, "")
        # valid_movies = [m for m in movies if m.movie_released() and m.box_office != -1]
        # return max(valid_movies, key=attrgetter('box_office')) if valid_movies else None

    def get_audience_favorite(self, movies: List[MovieData]) -> MovieData:
        """Get movie with highest audience score"""
        if self.actor:
            return self.actor.get_best_popcornmeter()
        else:
            return Movie("where is the movie?", 0, "", 0, 0, 0, "")
        # valid_movies = [m for m in movies if m.movie_released() and m.popcornmeter != -1]
        # return max(valid_movies, key=attrgetter('popcornmeter')) if valid_movies else None

    def get_critics_favorite(self, movies: List[MovieData]) -> MovieData:
        """Get movie with highest critics score"""        
        if self.actor:
            return self.actor.get_best_tomatometer()
        # valid_movies = [m for m in movies if m.movie_released() and m.tomatometer != -1]
        # return max(valid_movies, key=attrgetter('tomatometer')) if valid_movies else None

class PublishDialog:
    def __init__(self, parent):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Schedule YouTube Upload")
        self.dialog.geometry("300x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Calendar
        self.cal = Calendar(self.dialog, selectmode='day', 
                          mindate=datetime.now())
        self.cal.pack(pady=20)
        
        # Time selection
        time_frame = ttk.Frame(self.dialog)
        time_frame.pack(pady=10)
        
        ttk.Label(time_frame, text="Time:").pack(side=tk.LEFT)
        self.hour = ttk.Spinbox(time_frame, from_=0, to=23, width=3)
        self.hour.pack(side=tk.LEFT, padx=2)
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        self.minute = ttk.Spinbox(time_frame, from_=0, to=59, width=3)
        self.minute.pack(side=tk.LEFT, padx=2)
        
        # Buttons
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="Schedule", 
                  command=self.on_schedule).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", 
                  command=self.on_cancel).pack(side=tk.LEFT, padx=5)

    def on_schedule(self):
        date = self.cal.selection_get()
        time = f"{self.hour.get()}:{self.minute.get()}"
        self.result = f"{date} {time}"
        self.dialog.destroy()

    def on_cancel(self):
        self.dialog.destroy()

class MovieShortsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Movie Shorts Generator")
        self.root.geometry("800x900")
        
        self.movie_service = MovieDataService()
        self.category_functions = {
            "Critics Least Favorite": self.movie_service.get_critics_least_favorite,
            "Audience Least Favorite": self.movie_service.get_audience_least_favorite,
            "Most Successful": self.movie_service.get_most_successful,
            "Audience Favorite": self.movie_service.get_audience_favorite,
            "Critics Favorite": self.movie_service.get_critics_favorite
        }
        
        self.categories = list(self.category_functions.keys())
        self.actor_filmography = []
        self.selected_categories = {}
        self.video_path = None
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Actor name input
        actor_frame = ttk.Frame(main_frame)
        actor_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(actor_frame, text="Input Actor Name:").pack(side=tk.LEFT)
        self.actor_name = ttk.Entry(actor_frame)
        self.actor_name.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.actor_name.bind('<Return>', lambda e: self.search_actor())
        ttk.Button(actor_frame, text="Search", 
                  command=self.search_actor).pack(side=tk.LEFT)
        
        # Category selection
        ttk.Label(main_frame, text="Select Categories (Drag to Reorder):").pack(fill=tk.X, pady=(0, 5))
        
        # Create listbox for drag and drop
        self.category_listbox = tk.Listbox(main_frame, selectmode=tk.SINGLE, height=len(self.categories))
        self.category_listbox.pack(fill=tk.X, pady=(0, 10))
        
        # Populate listbox
        for category in self.categories:
            self.category_listbox.insert(tk.END, category)
            
        # Bind drag and drop events
        self.category_listbox.bind('<Button-1>', self.on_drag_start)
        self.category_listbox.bind('<B1-Motion>', self.on_drag_motion)
        
        # Labels to show selected movies
        self.movie_labels = {}
        for category in self.categories:
            label = ttk.Label(main_frame, text="")
            label.pack(fill=tk.X, pady=2)
            self.movie_labels[category] = label
        
        # Progress bar
        self.progress = ttk.Progressbar(
            main_frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill=tk.X, pady=10)
        
        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        # Generate button
        self.generate_btn = ttk.Button(
            btn_frame, 
            text="Generate Video", 
            command=self.generate_video,
            state=tk.DISABLED
        )
        self.generate_btn.pack(side=tk.LEFT, padx=5)
        
        # Publish button
        self.publish_btn = ttk.Button(
            btn_frame, 
            text="Publish to YouTube", 
            command=self.show_publish_dialog,
            state=tk.DISABLED
        )
        self.publish_btn.pack(side=tk.LEFT, padx=5)
        
        # Video preview label
        self.preview_label = ttk.Label(main_frame, text="Video Preview")
        self.preview_label.pack(pady=10)
        
        # Video preview frame
        self.preview_frame = ttk.Frame(main_frame, relief="solid", borderwidth=1)
        self.preview_frame.pack(fill=tk.BOTH, expand=True)

    def on_drag_start(self, event):
        # Record the item and its index
        self.drag_start_index = self.category_listbox.nearest(event.y)
        
    def on_drag_motion(self, event):
        # Get the current mouse position
        drag_end_index = self.category_listbox.nearest(event.y)
        
        if drag_end_index != self.drag_start_index:
            # Get the dragged item
            item = self.category_listbox.get(self.drag_start_index)
            
            # Delete from old position and insert at new position
            self.category_listbox.delete(self.drag_start_index)
            self.category_listbox.insert(drag_end_index, item)
            
            # Update the start index
            self.drag_start_index = drag_end_index
            
            # Update selected categories order
            self.update_category_selection()
            
    def search_actor(self):
        actor_name = self.actor_name.get().strip()
        if not actor_name:
            messagebox.showerror("Error", "Please enter an actor name")
            return
        try:
            rt = RottenTomatoes()
            
            print(f"Fetching filmography for {actor_name}")
            actor = rt.scrape_actor_data(actor_name)
            
            if actor is None:
                messagebox.showerror("Error", f"Could not find actor: {actor_name}")
                return
                
            print(f"actor name: {actor.name} movies: {len(actor.movies)}")
            
            # Assign the actor to movie_service
            self.movie_service.actor = actor
            
            # Enable generate button
            self.generate_btn.configure(state=tk.NORMAL)
            
            # Update the movie labels
            self.update_category_selection()
            
            messagebox.showinfo("Success", f"Found {len(actor.movies)} movies for {actor_name}")
            
        except Exception as e:
            print(f"Error in search_actor: {str(e)}")
            messagebox.showerror("Error", f"Failed to fetch actor data: {str(e)}")
    def update_category_selection(self):
        # Clear previous selections
        self.selected_categories.clear()
        
        # Get current order of categories
        ordered_categories = list(self.category_listbox.get(0, tk.END))
        
        # Update movies for each selected category
        for category in ordered_categories:
            movie = self.category_functions[category](self.actor_filmography)
            if movie:
                self.movie_labels[category].configure(
                    text=f"→ {movie.title} ({movie.year}) - Critics: {movie.get_display_tomatometer()}, Audience: {movie.get_display_popcornmeter()}"
                )
                self.selected_categories[category] = movie
            else:
                self.movie_labels[category].configure(text="No movie found")
            
    def generate_video(self):
        if len(self.selected_categories) < 3:
            messagebox.showerror("Error", "Please select at least 3 categories")
            return
            
        # Get ordered movies based on listbox order
        ordered_categories = list(self.category_listbox.get(0, tk.END))
        ordered_movies = [self.selected_categories[cat] for cat in ordered_categories 
                         if cat in self.selected_categories]
            
        # Disable controls during generation
        self.generate_btn.configure(state=tk.DISABLED)
        self.progress["value"] = 0
        
        # Start generation in a separate thread
        thread = threading.Thread(
            target=self.generate_video_thread,
            args=(ordered_movies,)
        )
        thread.start()
        
    def generate_video_thread(self, selected_movies):
        try:
            # Initialize video generator
            from animated_shorts_generator import ShortsGenerator
            generator = ShortsGenerator(duration=20)
            
            # Update progress callback
            def update_progress(value):
                self.root.after(0, lambda: self.progress.configure(value=value))
            
            # Generate video
            output_path = "generated_video.mp4"
            generator.generate_video(selected_movies, output_path, 
                                  progress_callback=update_progress)
            
            # Enable publish button and show preview
            self.root.after(0, lambda: self.on_generation_complete(output_path))
            
        except Exception as e:
            error_message = str(e)  # Capture the error message
            self.root.after(0, lambda: messagebox.showerror("Error", error_message))
        finally:
            self.root.after(0, lambda: self.generate_btn.configure(state=tk.NORMAL))
            
    def on_generation_complete(self, video_path):
        self.video_path = video_path
        self.publish_btn.configure(state=tk.NORMAL)
        
        # Create video preview
        try:
            clip = VideoFileClip(video_path)
            frame = clip.get_frame(0)
            image = Image.fromarray(frame)
            image.thumbnail((1080, 1920))
            photo = ImageTk.PhotoImage(image)
            
            if hasattr(self, 'preview_image_label'):
                self.preview_image_label.configure(image=photo)
                self.preview_image_label.image = photo
            else:
                self.preview_image_label = ttk.Label(
                    self.preview_frame, image=photo)
                self.preview_image_label.image = photo
                self.preview_image_label.pack()
                
            clip.close()
            
        except Exception as e:
            messagebox.showwarning("Preview Error", 
                                 "Could not load video preview")
            
    def show_publish_dialog(self):
        dialog = PublishDialog(self.root)
        self.root.wait_window(dialog.dialog)
        if dialog.result:
            self.publish_to_youtube(dialog.result)
            
    def publish_to_youtube(self, schedule_time):
        messagebox.showinfo(
            "Success", 
            f"Video scheduled for upload at {schedule_time}"
        )

def main():
    root = tk.Tk()
    app = MovieShortsApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()