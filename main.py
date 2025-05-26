import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import random
import math
import threading
from collections import deque
import time

class SmartCourierSimulator:
    def __init__(self, master):
        self.master = master
        self.master.title("Smart Courier - BFS Navigation")
        self.master.geometry("1000x800")

        self.ROAD_RGB = 90
        self.SOURCE_COLOR = "#FFD700"
        self.DESTINATION_COLOR = "#FF0000"
        self.COURIER_COLOR = "#2196F3"

        self.COURIER_SIZE = 8
        self.FLAG_SIZE = 6

        self.setup_ui()
        self.reset_state()
        self.gui_queue = deque()
        self.last_frame_time = time.time()
        self.frame_count = 0
        self.fps = 0
        self.map_size_text = ""
        self.stop_thread = False
        self.check_queue()

    def setup_ui(self):
        self.control_frame = tk.Frame(self.master, bg="#f0f0f0", padx=10, pady=10)
        self.control_frame.pack(fill=tk.X)

        tk.Button(self.control_frame, text="Load Map", command=self.load_map, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(self.control_frame, text="Random Positions", command=self.place_flags_threaded, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(self.control_frame, text="Start Delivery", command=self.start_delivery_threaded, bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(self.control_frame, text="Reset", command=self.reset_map, bg="#F44336", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Label(self.control_frame, text="Speed:").pack(side=tk.LEFT, padx=(20, 5))
        self.speed_scale = tk.Scale(self.control_frame, from_=1, to=30, orient=tk.HORIZONTAL)
        self.speed_scale.set(20)
        self.speed_scale.pack(side=tk.LEFT)

        self.status_frame = tk.Frame(self.master, bg="#333", height=30)
        self.status_frame.pack(fill=tk.X)
        self.status_label = tk.Label(self.status_frame, text="", fg="white", bg="#333")
        self.status_label.pack(side=tk.LEFT, padx=10)
        self.size_label = tk.Label(self.status_frame, text="", fg="white", bg="#333")
        self.size_label.pack(side=tk.RIGHT, padx=10)

        self.canvas = tk.Canvas(self.master, width=900, height=700, bg="#333")
        self.canvas.pack(pady=(0, 10))

    def reset_state(self):
        self.image = None
        self.image_tk = None
        self.map_array = None
        self.original_size = None
        self.source = None
        self.destination = None
        self.courier = None
        self.courier_angle = 0
        self.delivery_in_progress = False
        self.road_set = set()
        self.has_package = False
        self.stop_thread = False

    def reset_map(self):
        self.stop_thread = True
        self.delivery_in_progress = False
        time.sleep(0.1)

        if self.image:
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_tk)
            self.place_flags_threaded()
            self.update_status(self.map_size_text)

    def check_queue(self):
        while self.gui_queue:
            func = self.gui_queue.popleft()
            func()
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_frame_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_frame_time = current_time
        self.master.after(10, self.check_queue)

    def update_status(self, text):
        self.status_label.config(text=text)

    def load_map(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if not path:
            return
        img = Image.open(path).convert("RGB")
        width, height = img.size

        if not (1000 <= width <= 1500) or not (700 <= height <= 1000):
            messagebox.showerror("Ukuran Peta Tidak Valid", f"Peta harus 1000-1500px lebar dan 700-1000px tinggi. Saat ini: {width}x{height}.")
            return

        self.map_size_text = f"Ukuran Peta: {width}x{height}px"
        self.update_status(self.map_size_text)
        self.size_label.config(text=f"{width}x{height}px")

        self.map_array = np.array(img)
        self.original_size = img.size
        img.thumbnail((900, 700), Image.LANCZOS)
        self.image = img
        self.image_tk = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.config(width=self.image.width, height=self.image.height)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_tk)

        r, g, b = self.map_array[:, :, 0], self.map_array[:, :, 1], self.map_array[:, :, 2]
        mask = (r == self.ROAD_RGB) & (g == self.ROAD_RGB) & (b == self.ROAD_RGB)
        self.road_set = set(zip(*np.where(mask)))

    def place_flags_threaded(self):
        if not self.road_set:
            return
        self.stop_thread = True
        time.sleep(0.1)

        self.source = random.choice(list(self.road_set))
        remaining = self.road_set - {self.source}
        self.destination = random.choice(list(remaining))
        remaining -= {self.destination}
        self.courier = random.choice(list(remaining))

        self.courier_angle = 0
        self.has_package = False
        self.delivery_in_progress = False
        self.stop_thread = False

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_tk)
        self.draw_flag(self.source, self.SOURCE_COLOR)
        self.draw_flag(self.destination, self.DESTINATION_COLOR)
        self.draw_courier()
        self.update_status(self.map_size_text)

    def draw_flag(self, pos, color):
        y, x = pos
        sx, sy = self.get_scale()
        cx, cy = x * sx, y * sy
        self.canvas.create_oval(cx - self.FLAG_SIZE, cy - self.FLAG_SIZE, cx + self.FLAG_SIZE, cy + self.FLAG_SIZE, fill=color, outline="black")

    def draw_courier(self):
        y, x = self.courier
        sx, sy = self.get_scale()
        cx, cy = x * sx, y * sy
        size = self.COURIER_SIZE
        angle_rad = math.radians(self.courier_angle)
        points = [
            cx + size * math.cos(angle_rad), cy - size * math.sin(angle_rad),
            cx + size * 0.7 * math.cos(angle_rad + math.pi * 0.8), cy - size * 0.7 * math.sin(angle_rad + math.pi * 0.8),
            cx + size * 0.7 * math.cos(angle_rad - math.pi * 0.8), cy - size * 0.7 * math.sin(angle_rad - math.pi * 0.8)
        ]
        self.canvas.delete("courier")
        self.canvas.create_polygon(points, fill=self.COURIER_COLOR, outline="white", tags="courier")

    def get_scale(self):
        sx = self.image.width / self.original_size[0]
        sy = self.image.height / self.original_size[1]
        return sx, sy

    def start_delivery_threaded(self):
        if self.delivery_in_progress or not self.courier or not self.source or not self.destination:
            return
        self.delivery_in_progress = True
        self.stop_thread = False
        threading.Thread(target=self.run_delivery, daemon=True).start()

    def run_delivery(self):
        path_to_source = self.bfs(self.courier, self.source)
        if not path_to_source:
            self.gui_queue.append(lambda: messagebox.showerror("Error", "Tidak ada jalur ke sumber paket!"))
            self.delivery_in_progress = False
            return
        self.follow_path(path_to_source)
        if self.stop_thread:
            self.delivery_in_progress = False
            return
        self.courier = self.source
        self.has_package = True
        self.update_flags_after_pickup()
        time.sleep(0.3)
        if self.stop_thread:
            self.delivery_in_progress = False
            return

        path_to_dest = self.bfs(self.source, self.destination)
        if not path_to_dest:
            self.gui_queue.append(lambda: messagebox.showerror("Error", "Tidak ada jalur ke tujuan paket!"))
            self.delivery_in_progress = False
            return
        self.follow_path(path_to_dest)
        if self.stop_thread:
            self.delivery_in_progress = False
            return
        self.courier = self.destination
        self.has_package = False
        self.update_flags_after_delivery()
        self.gui_queue.append(lambda: [
            self.update_status(self.map_size_text),
            messagebox.showinfo("Selesai", "Paket berhasil diantarkan!")
        ])
        self.delivery_in_progress = False

    def update_flags_after_pickup(self):
        self.gui_queue.append(lambda: self.reset_canvas_with_flags(show_source=False))

    def update_flags_after_delivery(self):
        self.gui_queue.append(lambda: self.reset_canvas_with_flags(show_destination=False))

    def reset_canvas_with_flags(self, show_source=True, show_destination=True):
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_tk)
        if show_source:
            self.draw_flag(self.source, self.SOURCE_COLOR)
        if show_destination:
            self.draw_flag(self.destination, self.DESTINATION_COLOR)
        self.draw_courier()

    def bfs(self, start, goal):
        if start == goal:
            return []
        queue = deque([start])
        came_from = {}
        visited = {start}
        h, w = self.map_array.shape[:2]
        while queue:
            if self.stop_thread:
                return []
            current = queue.popleft()
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]
            for dy, dx in [(-1,0), (1,0), (0,-1), (0,1)]:
                ny, nx = current[0]+dy, current[1]+dx
                neighbor = (ny, nx)
                if 0 <= ny < h and 0 <= nx < w and neighbor in self.road_set and neighbor not in visited:
                    visited.add(neighbor)
                    came_from[neighbor] = current
                    queue.append(neighbor)
        return []

    def follow_path(self, path):
        for next_pos in path[1:]:
            if self.stop_thread:
                break
            dy, dx = next_pos[0] - self.courier[0], next_pos[1] - self.courier[1]
            if dy == -1:
                target_angle = 90
            elif dy == 1:
                target_angle = 270
            elif dx == -1:
                target_angle = 180
            elif dx == 1:
                target_angle = 0
            else:
                continue
            while abs((self.courier_angle - target_angle + 180) % 360 - 180) > 1:
                if self.stop_thread:
                    return
                delta = (target_angle - self.courier_angle + 360) % 360
                if delta <= 180:
                    self.courier_angle = (self.courier_angle + 10) % 360
                else:
                    self.courier_angle = (self.courier_angle - 10) % 360
                self.gui_queue.append(self.draw_courier)
                time.sleep(0.005)
            self.courier_angle = target_angle
            self.courier = next_pos
            self.gui_queue.append(self.draw_courier)
            time.sleep(1.0 / self.speed_scale.get())

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartCourierSimulator(root)
    root.mainloop()
