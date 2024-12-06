import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from datetime import datetime
from PIL import Image, ImageTk
import threading
from moviepy.editor import VideoFileClip
from typing import Optional
from RT import RottenTomatoes
from Movie import Movie

class PublishDialog:
    def __init__(self, parent):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Schedule YouTube Upload")
        self.dialog.geometry("300x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.cal = Calendar(self.dialog, selectmode='day', mindate=datetime.now())
        self.cal.pack(pady=20)
        
        time_frame = ttk.Frame(self.dialog)
        time_frame.pack(pady=10)
        
        ttk.Label(time_frame, text="Time:").pack(side=tk.LEFT)
        self.hour = ttk.Spinbox(time_frame, from_=0, to=23, width=3)
        self.hour.pack(side=tk.LEFT, padx=2)
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        self.minute = ttk.Spinbox(time_frame, from_=0, to=59, width=3)
        self.minute.pack(side=tk.LEFT, padx=2)
        
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="Schedule", command=self.on_schedule).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.on_cancel).pack(side=tk.LEFT, padx=5)

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
        
        self.actor: Optional[Movie] = None
        self.video_path: Optional[str] = None
        self.drag_start_index: Optional[int] = None
        
        self.categories = [
            "Critics Least Favorite",
            "Audience Least Favorite",
            "Most Successful",
            "Audience Favorite",
            "Critics Favorite"
        ]
        
        self.category_functions = {
            "Critics Least Favorite": lambda x: x.get_worst_tomatometer() if x else None,
            "Audience Least Favorite": lambda x: x.get_worst_popcornmeter() if x else None,
            "Most Successful": lambda x: x.get_most_successful() if x else None,
            "Audience Favorite": lambda x: x.get_best_popcornmeter() if x else None,
            "Critics Favorite": lambda x: x.get_best_tomatometer() if x else None
        }
        
        self.selected_categories = {}
        self.create_widgets()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Actor input frame
        actor_frame = ttk.Frame(main_frame)
        actor_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(actor_frame, text="Input Actor Name:").pack(side=tk.LEFT)
        self.actor_name = ttk.Entry(actor_frame)
        self.actor_name.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.actor_name.bind('<Return>', lambda e: self.search_actor())
        
        self.search_btn = ttk.Button(actor_frame, text="Search", command=self.search_actor)
        self.search_btn.pack(side=tk.LEFT)
        
        # Category selection frame with movie details
        category_frame = ttk.LabelFrame(main_frame, text="Select Categories (Drag to Reorder):", padding="5")
        category_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.category_listbox = tk.Listbox(category_frame, selectmode=tk.SINGLE, height=len(self.categories))
        self.category_listbox.pack(fill=tk.X)
        
        for category in self.categories:
            self.category_listbox.insert(tk.END, f"{category}: No movie selected")
            
        self.category_listbox.bind('<Button-1>', self.on_drag_start)
        self.category_listbox.bind('<B1-Motion>', self.on_drag_motion)
        
        # Progress and buttons
        self.progress = ttk.Progressbar(main_frame, orient="horizontal", mode="determinate", length=300)
        self.progress.pack(fill=tk.X, pady=10)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.generate_btn = ttk.Button(btn_frame, text="Generate Video", command=self.generate_video_helper, state=tk.DISABLED)
        self.generate_btn.pack(side=tk.LEFT, padx=5)
        
        self.publish_btn = ttk.Button(btn_frame, text="Publish to YouTube", command=self.show_publish_dialog, state=tk.DISABLED)
        self.publish_btn.pack(side=tk.LEFT, padx=5)
        
        # Video preview
        self.preview_label = ttk.Label(main_frame, text="Video Preview")
        self.preview_label.pack(pady=10)
        
        self.preview_frame = ttk.Frame(main_frame, relief="solid", borderwidth=1)
        self.preview_frame.pack(fill=tk.BOTH, expand=True)
        
        self.video_canvas = tk.Canvas(self.preview_frame, bg='black')
        self.video_canvas.pack(fill=tk.BOTH, expand=True)
        
        self.preview_frame.bind('<Configure>', self.resize_preview)

    def resize_preview(self, event):
        width = event.width
        height = int(width * 16/9)
        self.video_canvas.configure(width=width, height=height)
        if hasattr(self, 'preview_image_label'):
            self.preview_image_label.configure(width=width, height=height)

    def search_actor(self):
        actor_name = self.actor_name.get().strip()
        if not actor_name:
            messagebox.showerror("Error", "Please enter an actor name")
            return
            
        try:
            rt = RottenTomatoes()
            self.actor = rt.scrape_actor_data(actor_name)
            
            if not self.actor:
                messagebox.showerror("Error", f"Could not find actor: {actor_name}")
                return
                
            self.category_listbox.configure(state=tk.NORMAL)
            self.generate_btn.configure(state=tk.NORMAL)
            
            self.update_category_selection()
            messagebox.showinfo("Success", f"Found {len(self.actor.movies)} movies for {actor_name}")
            
        except Exception as e:
            print(f"Error in search_actor: {str(e)}")
            messagebox.showerror("Error", f"Failed to fetch actor data: {str(e)}")

    def on_drag_start(self, event):
        self.drag_start_index = self.category_listbox.nearest(event.y)
        
    def on_drag_motion(self, event):
        if self.category_listbox.cget('state') == tk.DISABLED:
            return
            
        drag_end_index = self.category_listbox.nearest(event.y)
        
        if drag_end_index != self.drag_start_index:
            item = self.category_listbox.get(self.drag_start_index)
            self.category_listbox.delete(self.drag_start_index)
            self.category_listbox.insert(drag_end_index, item)
            self.drag_start_index = drag_end_index
            
            # Update movie labels after drag
            ordered_categories = [item.split(":")[0].strip() for item in list(self.category_listbox.get(0, tk.END))]
            for i, category in enumerate(ordered_categories):
                movie = self.category_functions[category](self.actor)
                if movie:
                    self.category_listbox.delete(i)
                    self.category_listbox.insert(i, f"{category}: {movie.title} ({movie.year}) - Critics: {movie.get_display_tomatometer()}, Audience: {movie.get_display_popcornmeter()}")
                    self.selected_categories[category] = movie

    def update_category_selection(self):
        self.selected_categories.clear()
        self.category_listbox.delete(0, tk.END)
        
        for category in self.categories:
            movie = self.category_functions[category](self.actor)
            if movie:
                self.category_listbox.insert(tk.END, f"{category}: {movie.title} ({movie.year}) - Critics: {movie.get_display_tomatometer()}, Audience: {movie.get_display_popcornmeter()}")
                self.selected_categories[category] = movie
            else:
                self.category_listbox.insert(tk.END, f"{category}: No movie found")

    def generate_video(self):
        if len(self.selected_categories) < 3:
            messagebox.showerror("Error", "Please select at least 3 categories")
            return
            
        ordered_categories = [item.split(":")[0].strip() for item in list(self.category_listbox.get(0, tk.END))]
        ordered_movies = [(self.selected_categories[cat], cat) for cat in ordered_categories 
                         if cat in self.selected_categories]
            
        self.generate_btn.configure(state=tk.DISABLED)
        self.progress["value"] = 0
        
        thread = threading.Thread(
            target=self.generate_video_thread,
            args=(ordered_movies,)
        )
        thread.start()

    def generate_video_thread(self, selected_movies):
        try:
            from animated_shorts_generator import ShortsGenerator
            generator = ShortsGenerator(duration=20)
            
            def update_progress(value):
                self.root.after(0, lambda: self.progress.configure(value=value))
            
            output_path = "generated_video.mp4"
            generator.generate_video_helper(self.actor, movies_with_descriptors=selected_movies, output_path = output_path, progress_callback=update_progress)
            
            self.root.after(0, lambda: self.on_generation_complete(output_path))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.root.after(0, lambda: self.generate_btn.configure(state=tk.NORMAL))

    def on_generation_complete(self, video_path):
        self.video_path = video_path
        self.publish_btn.configure(state=tk.NORMAL)
        
        try:
            clip = VideoFileClip(video_path)
            frame = clip.get_frame(0)
            image = Image.fromarray(frame)
            image.thumbnail((1080, 1920))  # Maintain aspect ratio
            photo = ImageTk.PhotoImage(image)
            
            if hasattr(self, 'preview_image_label'):
                self.preview_image_label.configure(image=photo)
                self.preview_image_label.image = photo
            else:
                self.preview_image_label = ttk.Label(self.preview_frame, image=photo)
                self.preview_image_label.image = photo
                self.preview_image_label.pack(fill=tk.BOTH, expand=True)
                
            clip.close()
            
        except Exception as e:
            messagebox.showwarning("Preview Error", "Could not load video preview")

    def show_publish_dialog(self):
        dialog = PublishDialog(self.root)
        self.root.wait_window(dialog.dialog)
        if dialog.result:
            self.publish_to_youtube(dialog.result)

    def publish_to_youtube(self, schedule_time):
        messagebox.showinfo("Success", f"Video scheduled for upload at {schedule_time}")

def main():
    root = tk.Tk()
    app = MovieShortsApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()