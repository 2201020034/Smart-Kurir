import pygame
import sys
import random
from PIL import Image
import numpy as np
from tkinter import filedialog, Tk
from collections import deque

pygame.init()

SCALE = 0.7
WIDTH, HEIGHT = 0, 0
SCALED_WIDTH, SCALED_HEIGHT = 0, 0

WHITE = (255, 255, 255)
GRAY = (120, 120, 120)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)

map_img = None
original_img = None
SCREEN = None

kurir_pos = [100, 100]
kurir_angle = 0
source_pos = [200, 200]
dest_pos = [800, 600]
kurir_speed = 0.5
is_moving = False
sudah_ambil = False
paket_diterima = False
use_manual_control = True
kurir_visible = True
tugas_selesai = False
status_text = ""

def scale_pos(pos):
    return [int(pos[0] * SCALE), int(pos[1] * SCALE)]

def load_map(file_path):
    global map_img, original_img, WIDTH, HEIGHT, SCALED_WIDTH, SCALED_HEIGHT, SCREEN
    pil_img = Image.open(file_path).convert("RGB")
    original_img = pil_img.copy()
    WIDTH, HEIGHT = pil_img.size
    SCALED_WIDTH, SCALED_HEIGHT = int(WIDTH * SCALE), int(HEIGHT * SCALE)
    map_img = pygame.image.fromstring(pil_img.tobytes(), pil_img.size, pil_img.mode)
    SCREEN = pygame.display.set_mode((SCALED_WIDTH, SCALED_HEIGHT))

def is_road(color):
    r, g, b = color
    return 90 <= r <= 150 and 90 <= g <= 150 and 90 <= b <= 150

def get_pixel_color(pos):
    x, y = round(pos[0]), round(pos[1])
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        return original_img.getpixel((x, y))
    return (0, 0, 0)

def random_road_position():
    while True:
        x = random.randint(0, WIDTH - 1)
        y = random.randint(0, HEIGHT - 1)
        if is_road(get_pixel_color((x, y))):
            return [x, y]

def randomize_positions():
    global kurir_pos, source_pos, dest_pos, sudah_ambil, paket_diterima, tugas_selesai, status_text
    source_pos = random_road_position()
    dest_pos = random_road_position()
    kurir_pos = source_pos.copy()
    sudah_ambil = False
    paket_diterima = False
    tugas_selesai = False
    status_text = "Ambil Paket"
    print(f"Source: {source_pos}, Destination: {dest_pos}")

def draw_kurir(surface, pos, angle):
    if not kurir_visible:
        return
    x, y = scale_pos(pos)
    size = 4
    points = [
        (x + size * np.cos(np.radians(angle)), y - size * np.sin(np.radians(angle))),
        (x + size * np.cos(np.radians(angle + 135)), y - size * np.sin(np.radians(angle + 135))),
        (x + size * np.cos(np.radians(angle - 135)), y - size * np.sin(np.radians(angle - 135)))
    ]
    pygame.draw.polygon(surface, BLACK, points)

def load_image():
    root = Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png")])
    if file_path:
        load_map(file_path)
        randomize_positions()
        print(f"Map dimuat dari: {file_path}")
        print(f"Source: {source_pos}, Destination: {dest_pos}")

def bfs(start, goal):
    queue = deque([(start, [])])
    visited = set()
    visited.add(tuple(start))
    while queue:
        current_pos, path = queue.popleft()
        if current_pos == goal:
            return path
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            next_pos = [current_pos[0]+dx, current_pos[1]+dy]
            if is_road(get_pixel_color(next_pos)) and tuple(next_pos) not in visited:
                visited.add(tuple(next_pos))
                queue.append((next_pos, path + [next_pos]))
    return []

def is_facing_toward(kurir_pos, target_pos, kurir_angle):
    dx = target_pos[0] - kurir_pos[0]
    dy = target_pos[1] - kurir_pos[1]
    angle_to_target = np.degrees(np.arctan2(-dy, dx)) % 360
    return abs((kurir_angle - angle_to_target + 180) % 360 - 180) < 45

def update_kurir_angle(kurir_pos, target_pos):
    dx = target_pos[0] - kurir_pos[0]
    dy = target_pos[1] - kurir_pos[1]
    return np.degrees(np.arctan2(-dy, dx)) % 360

def move_kurir(kurir_pos, kurir_angle, speed):
    dx = speed * np.cos(np.radians(kurir_angle))
    dy = -speed * np.sin(np.radians(kurir_angle))
    new_pos = [kurir_pos[0] + dx, kurir_pos[1] + dy]
    if is_road(get_pixel_color(new_pos)):
        return new_pos
    return kurir_pos

def draw_button(surface, rect, text, font):
    pygame.draw.rect(surface, GRAY, rect)
    text_surf = font.render(text, True, BLACK)
    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)

def draw_path(surface, path):
    if len(path) >= 2:
        for i in range(len(path) - 1):
            pygame.draw.line(surface, GRAY, scale_pos(path[i]), scale_pos(path[i+1]), 1)

def main():
    global kurir_pos, kurir_angle, is_moving, sudah_ambil, use_manual_control, kurir_visible
    global kurir_speed, paket_diterima, status_text, tugas_selesai

    kurir_speed = 0.5

    try:
        load_map("assets/map.jpg")
    except:
        print("File 'assets/map.jpg' tidak ditemukan.")
        sys.exit()

    font = pygame.font.SysFont(None, 30)
    btn_reset = pygame.Rect(20, 20, 160, 40)
    btn_load_map = pygame.Rect(200, 20, 160, 40)
    btn_start = pygame.Rect(380, 20, 160, 40)

    randomize_positions()
    clock = pygame.time.Clock()
    path = []
    path_index = 0
    running = True

    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_reset.collidepoint(event.pos):
                    randomize_positions()
                    path = []
                    paket_diterima = False
                elif btn_load_map.collidepoint(event.pos):
                    load_image()
                    path = []
                    paket_diterima = False
                elif btn_start.collidepoint(event.pos):
                    if is_road(get_pixel_color(kurir_pos)) and is_road(get_pixel_color(dest_pos)):
                        path = bfs(kurir_pos, dest_pos)
                        path_index = 0
                        if not path:
                            status_text = "Jalur tidak ditemukan!"
                        else:
                            use_manual_control = False
                            status_text = "Menuju Tujuan"

        if path and path_index < len(path):
            next_pos = path[path_index]
            if np.linalg.norm(np.array(kurir_pos) - np.array(next_pos)) >= 1:
                kurir_angle = update_kurir_angle(kurir_pos, next_pos)
                kurir_pos = move_kurir(kurir_pos, kurir_angle, kurir_speed)
            if np.linalg.norm(np.array(kurir_pos) - np.array(next_pos)) < 2:
                kurir_pos = next_pos
                path_index += 1
            is_moving = True
        else:
            is_moving = False

        if not sudah_ambil and np.linalg.norm(np.array(kurir_pos) - np.array(source_pos)) < 5:
            if is_facing_toward(kurir_pos, source_pos, kurir_angle):
                sudah_ambil = True
                status_text = "Mengantar Paket"
                print("Paket berhasil diambil.")
            else:
                status_text = "Dekat Source - Hadapkan Kurir!"

        if sudah_ambil and np.linalg.norm(np.array(kurir_pos) - np.array(dest_pos)) < 5:
            if is_facing_toward(kurir_pos, dest_pos, kurir_angle) and not paket_diterima:
                paket_diterima = True
                tugas_selesai = True
                status_text = "Tugas Selesai!"
                print("Paket berhasil diterima.")
            else:
                status_text = "Dekat Tujuan - Hadapkan Kurir!"

        if not is_moving and sudah_ambil and not use_manual_control and not paket_diterima:
            path = bfs(kurir_pos, dest_pos)
            path_index = 0

        SCREEN.fill(WHITE)
        SCREEN.blit(pygame.transform.scale(map_img, (SCALED_WIDTH, SCALED_HEIGHT)), (0, 0))
        pygame.draw.circle(SCREEN, YELLOW, scale_pos(source_pos), 6)
        pygame.draw.circle(SCREEN, RED, scale_pos(dest_pos), 6)

        if path:
            draw_path(SCREEN, path)
        draw_kurir(SCREEN, kurir_pos, kurir_angle)

        draw_button(SCREEN, btn_reset, "Reset Posisi", font)
        draw_button(SCREEN, btn_load_map, "Load Peta", font)
        draw_button(SCREEN, btn_start, "Mulai", font)

        # Status teks
        status_surface = font.render(status_text, True, BLUE)
        SCREEN.blit(status_surface, (600, 30))

        if tugas_selesai:
            selesai_text = font.render("Tugas Selesai!", True, (0, 128, 0))
            SCREEN.blit(selesai_text, (600, 60))

        pygame.display.update()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
