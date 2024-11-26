import pygame
import math
import sys
import random
import colorsys
import time
import numpy as np
import os

pygame.init()
pygame.font.init()
pygame.mixer.init()

background_song_path = os.path.join(os.path.dirname(__file__), "background_song.mp3")
try:
    pygame.mixer.music.load(background_song_path)
    pygame.mixer.music.play(-1)
except pygame.error as e:
    print(f"Melodijos neatitikmuo: {e}")

WIDTH, HEIGHT = 800, 600
HALF_HEIGHT = HEIGHT // 2
HALF_WIDTH = WIDTH // 2

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
RED = (200, 50, 50)
BLUE = (50, 50, 200)
YELLOW = (255, 255, 0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DoomMan:Psichoz3")

clock = pygame.time.Clock()

TILE_SIZE = 50
MAP = [
    "11111111111111111111111111111111",
    "1                              1",
    "1 1111 111111 1111 111111 1111 1",
    "1 1  1      1  1 1      1  1   1",
    "1 11 1 1111 1 11 1 1111 1 11   1",
    "1    1 1  1 1    1 1  1 1      1",
    "111111 1  1 111111 1  1   111111",
    "1      1  1        1  1        1",
    "1 111111  11111111 1  11111    1",
    "1                              1",
    "11111111111111111111111111111111"
]

player_x, player_y = 100, 100  # Pradine zaidejo padetis
player_angle = 0
FOV = math.pi / 3  # 60 degrees
RAY_COUNT = 120
MAX_DEPTH = 300

player_speed = 3
rotation_speed = 0.05

COIN_RADIUS = 20
coins = []
for _ in range(30):
    while True:
        coin_x = random.randint(1, len(MAP[0]) - 2) * TILE_SIZE + TILE_SIZE // 2
        coin_y = random.randint(1, len(MAP) - 2) * TILE_SIZE + TILE_SIZE // 2
        if MAP[coin_y // TILE_SIZE][coin_x // TILE_SIZE] != '1':
            coins.append((coin_x, coin_y))
            break

coins = [(x, y) for x, y in coins if MAP[y // TILE_SIZE][x // TILE_SIZE] != '1']
score = 0


def generate_tone(frequency, duration):
    t = np.linspace(0, duration / 1000, int(44100 * (duration / 1000)), endpoint=False)
    waveform = np.sign(np.sin(2 * np.pi * frequency * t))
    return pygame.mixer.Sound(np.array(waveform * 32767, dtype=np.int16).tobytes())


def play_random_note():
    note = random.choice([262, 294, 330, 349, 392, 440, 494, 523])
    duration = random.choice([250, 500, 750, 1000])
    generate_tone(note, duration).play()



def rainbow_color(t):
    """Random rainbow spalvos."""
    r, g, b = colorsys.hsv_to_rgb(t % 1.0, 1.0, 1.0)
    return int(r * 255), int(g * 255), int(b * 255)


def get_fading_color(t):
    """Random tarp juodos ir baltos fono."""
    intensity = (np.sin(t) + 1) / 2  # normalize to [0, 1]
    color_value = int(intensity * 20)
    return (color_value, color_value, color_value)


def cast_rays():
    """Spinduliu ilgis aplinkoje."""
    t = time.time() * 0.1
    ray_width = WIDTH / RAY_COUNT
    wall_depths = [MAX_DEPTH] * RAY_COUNT

    for ray in range(RAY_COUNT):
        # Spindulio laipsnis
        ray_angle = player_angle - FOV / 2 + FOV * ray / RAY_COUNT
        sin_a = math.sin(ray_angle)
        cos_a = math.cos(ray_angle)

        for depth in range(1, int(MAX_DEPTH)):
            target_x = player_x + depth * cos_a
            target_y = player_y + depth * sin_a
            col = int(target_x / TILE_SIZE)
            row = int(target_y / TILE_SIZE)

            if MAP[row][col] == '1':
                color = rainbow_color(t + depth * 0.01)
                wall_height = min(HEIGHT, int(TILE_SIZE / (depth * math.cos(ray_angle - player_angle)) * 500))
                pygame.draw.rect(screen, color, (
                    int(ray * ray_width), int(HALF_HEIGHT - wall_height // 2), int(ray_width), int(wall_height)))
                break

    # Renderina coinsus
    for coin_x, coin_y in coins:
        coin_angle = math.atan2(coin_y - player_y, coin_x - player_x)
        delta_angle = coin_angle - player_angle

        if delta_angle > math.pi:
            delta_angle -= 2 * math.pi
        if delta_angle < -math.pi:
            delta_angle += 2 * math.pi

        if -FOV / 2 < delta_angle < FOV / 2:
            coin_dist = math.hypot(coin_x - player_x, coin_y - player_y)

            if coin_dist < MAX_DEPTH:
                coin_proj_height = int(TILE_SIZE / coin_dist * 500)
                coin_screen_x = int((delta_angle + FOV / 2) / FOV * WIDTH)
                pygame.draw.circle(screen, YELLOW, (coin_screen_x, HALF_HEIGHT), coin_proj_height // 5)


def is_wall(x, y):
    """Checkina ar x ir y susiduria."""
    col = int(x / TILE_SIZE)
    row = int(y / TILE_SIZE)
    if 0 <= col < len(MAP[0]) and 0 <= row < len(MAP):
        return MAP[row][col] == '1'
    return False


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.radius = random.randint(1, 8)
        self.x_velocity = random.uniform(-1, 1)
        self.y_velocity = random.uniform(-1, 1)
        self.gravity = 0.01

    def update(self):
        self.x += self.x_velocity
        self.y += self.y_velocity
        self.y_velocity += self.gravity
        self.radius = max(0, self.radius - 0.05)  # Palaipsniui shrinkina spalvos

    def draw(self, surface, player_x, player_y):
        if self.radius > 0:
            relative_x = self.x - player_x + HALF_WIDTH
            relative_y = self.y - player_y + HALF_HEIGHT
            pygame.draw.circle(surface, self.color, (int(relative_x), int(relative_y)), int(self.radius))


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y):
        for _ in range(100):  # Daleliu efektas
            color = rainbow_color(random.random())
            self.particles.append(Particle(x, y, color))

    def update(self):
        for particle in self.particles[:]:
            particle.update()
            if particle.radius <= 0:
                self.particles.remove(particle)

    def draw(self, surface, player_x, player_y):
        for particle in self.particles:
            particle.draw(surface, player_x, player_y)


particle_system = ParticleSystem()


def check_coin_pickup():
    """Chekina ar zaidejas paiima coinsus."""
    global score, coins
    for coin in coins[:]:
        coin_dist = math.hypot(player_x - coin[0], player_y - coin[1])
        if coin_dist < TILE_SIZE / 2:
            print(
                f"Paimti coinsai ({coin[0]}, {coin[1]}) Zaidejo pozicijoje ({player_x}, {player_y}) Distancija {coin_dist}")
            coins.remove(coin)
            score += 1
            play_random_note()
            # Daleliu efektas esamoj zaidejo pozicijoj
            particle_system.emit(player_x, player_y)


def draw_rainbow_text(font, text, position, selected=False):
    text_surface = pygame.Surface(font.size(text), pygame.SRCALPHA)
    wave_y_offsets = [int(math.sin(time.time() * 7 + i * 0.3) * 10) for i in range(len(text))]
    for i, (letter, wave_y_offset) in enumerate(zip(text, wave_y_offsets)):
        letter_surface = font.render(letter, True, rainbow_color(time.time() + i * 0.1))
        text_surface.blit(letter_surface, (font.size(text[:i])[0], wave_y_offset))
    return text_surface, text_surface.get_rect(center=position)

def show_wavering_message(screen, font, message, position, duration):
    start_time = time.time()
    while time.time() - start_time < duration:
        current_time = time.time()
        background_color = get_fading_color(current_time)
        screen.fill(background_color)
        text_surface, text_rect = draw_rainbow_text(font, message, position)
        screen.blit(text_surface, text_rect)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
    menu()


def menu(play_rect=None, quit_rect=None):
    """Meniu display'us."""
    font = pygame.font.Font(None, 50)
    menu_running = True
    selected_option = 0

    def draw_background(screen):
        background_image = pygame.image.load("background.jpg")
        background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))
        screen.blit(background_image, (0, 0))

    def draw_option_text(text, y_offset, is_selected):
        text_surface, text_rect = draw_rainbow_text(font, text, (HALF_WIDTH, y_offset), is_selected)
        text_rect.center = (HALF_WIDTH, y_offset)
        return text_surface, text_rect

    while menu_running:
        draw_background(screen)
        rainbow_time = time.time() * 10

        play_text_surface, play_text_rect = draw_option_text('Play', HALF_HEIGHT - 50, selected_option == 0)
        quit_text_surface, quit_text_rect = draw_option_text('Quit', HALF_HEIGHT + 50, selected_option == 1)

        screen.blit(play_text_surface, play_text_rect.topleft)
        screen.blit(quit_text_surface, quit_text_rect.topleft)

        color = rainbow_color(rainbow_time)
        pygame.draw.rect(screen, color, (play_text_rect if selected_option == 0 else quit_text_rect), 3)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_rect and play_rect.collidepoint(event.pos):
                    menu_running = False
                elif quit_rect and quit_rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    selected_option = 0
                elif event.key == pygame.K_s:
                    selected_option = 1
                elif event.key == pygame.K_RETURN:
                    if selected_option == 0:
                        menu_running = False
                    elif selected_option == 1:
                        pygame.quit()
                        sys.exit()

        pygame.display.flip()


menu()

show_message = False
font = pygame.font.Font(None, 50)
collect_time = 0

# Zaidimo loop'as
running = True
all_coins_collected = False
start_time = time.time()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Backgroundo spalva
    current_time = time.time() - start_time
    bg_color = get_fading_color(current_time)

    # Mygtuko registras
    keys = pygame.key.get_pressed()
    new_x, new_y = player_x, player_y

    if keys[pygame.K_w]:
        new_x = player_x + player_speed * math.cos(player_angle)
        new_y = player_y + player_speed * math.sin(player_angle)

    if keys[pygame.K_s]:
        new_y = player_y - player_speed * math.sin(player_angle)

    if keys[pygame.K_a]:
        player_angle -= rotation_speed

    if keys[pygame.K_d]:
        player_angle += rotation_speed

    # Colisiono nuskaitymas
    if not is_wall(new_x, new_y):
        player_x, player_y = new_x, new_y

    # Chekina ar coinsas paimtas
    check_coin_pickup()

    rainbow_time = time.time() * 10

    # Checkina ar surinkti galimi coinsai
    if not coins and not all_coins_collected:
        all_coins_collected = True
        show_message = True
        collect_time = time.time()

    # Daleliu update'as
    particle_system.update()

    # Zaidimo renderis
    if show_message:
        if time.time() - collect_time < 3:
            background_color = get_fading_color(time.time())
            screen.fill(background_color)
            text_surface, text_rect = draw_rainbow_text(font, 'WOOOOOOOOOO!', (HALF_WIDTH, HALF_HEIGHT))
            screen.blit(text_surface, text_rect)
        else:
            show_message = False
            menu()
    else:
        screen.fill(bg_color)
        cast_rays()
        particle_system.draw(screen, player_x, player_y)

    score_color = rainbow_color(rainbow_time)
    score_text = font.render(f"Score: {score}", True, score_color)
    screen.blit(score_text, (WIDTH - 10 - score_text.get_width(), 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()