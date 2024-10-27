import pygame
import sys
import random
import json
import os

# Initialize constants
WIDTH, HEIGHT = 1000, 800
FPS = 60

# Initialize Pygame modules
pygame.init()
pygame.font.init()
pygame.mixer.init()

# Create the game window
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Dodge")
CLOCK = pygame.time.Clock()

# Load assets
BACKGROUND_IMAGE = pygame.image.load("assets/bg.png").convert()
BACKGROUND_IMAGE = pygame.transform.scale(BACKGROUND_IMAGE, (WIDTH, HEIGHT))
START_BG_IMAGE = pygame.image.load("assets/start_bg.png").convert()
START_BG_IMAGE = pygame.transform.scale(START_BG_IMAGE, (WIDTH, HEIGHT))
PLAYER_IMAGE = pygame.image.load("assets/player.png").convert_alpha()
ASTEROID_IMAGE = pygame.image.load("assets/asteroid.png").convert_alpha()

# Load sounds
pygame.mixer.music.load("assets/start_music.mp3")
GAME_MUSIC = "assets/game_music.mp3"
CRASH_SOUND = pygame.mixer.Sound("assets/crash.mp3")
EASTER_EGG_SOUND = pygame.mixer.Sound("assets/easter_egg.mp3")  # Easter egg sound

# Fonts
TITLE_FONT = pygame.font.SysFont("Arial", 72)
BUTTON_FONT = pygame.font.SysFont("Arial", 48)
INSTRUCTION_FONT = pygame.font.SysFont("Arial", 36)
CREDIT_FONT = pygame.font.SysFont("Arial", 24)

# Colors
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)

# Volume settings (default values)
MUSIC_VOLUME = 0.5
SFX_VOLUME = 0.5

def load_settings():
    global MUSIC_VOLUME, SFX_VOLUME
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
            MUSIC_VOLUME = settings.get('music_volume', 0.5)
            SFX_VOLUME = settings.get('sfx_volume', 0.5)
    except FileNotFoundError:
        MUSIC_VOLUME = 0.5
        SFX_VOLUME = 0.5

def save_settings():
    settings = {
        'music_volume': MUSIC_VOLUME,
        'sfx_volume': SFX_VOLUME,
    }
    with open('settings.json', 'w') as f:
        json.dump(settings, f)

load_settings()
pygame.mixer.music.set_volume(MUSIC_VOLUME)
CRASH_SOUND.set_volume(SFX_VOLUME)
EASTER_EGG_SOUND.set_volume(SFX_VOLUME)

# Classes
class Player:
    def __init__(self, x, y, speed, lives=3, score=0):
        self.image = pygame.transform.scale(PLAYER_IMAGE, (50, 50))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed
        self.lives = lives
        self.score = score

    def draw(self, window):
        window.blit(self.image, self.rect)

    def move(self):
        keys_pressed = pygame.key.get_pressed()
        if (keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]) and self.rect.left > 0:
            self.rect.x -= self.speed
        if (keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]) and self.rect.right < WIDTH:
            self.rect.x += self.speed
        if (keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]) and self.rect.top > 0:
            self.rect.y -= self.speed
        if (keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]) and self.rect.bottom < HEIGHT:
            self.rect.y += self.speed

class Obstacle:
    def __init__(self):
        self.image = pygame.transform.scale(ASTEROID_IMAGE, (50, 50))
        self.rect = self.image.get_rect(
            center=(random.randint(50, WIDTH - 50), -50)
        )
        self.speed = random.randint(3, 7)

    def move(self):
        self.rect.y += self.speed

    def draw(self, window):
        window.blit(self.image, self.rect)

# Functions
def draw_text(text, font, color, surface, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect(center=(x, y))
    surface.blit(textobj, textrect)

def get_text_input(prompt):
    input_active = True
    user_text = ''
    input_box = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2, 300, 50)
    color_active = pygame.Color('dodgerblue2')

    while input_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                input_active = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if user_text != '':
                        return user_text
                elif event.key == pygame.K_BACKSPACE:
                    user_text = user_text[:-1]
                else:
                    user_text += event.unicode
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not input_box.collidepoint(event.pos):
                    input_active = False
                    return None

        WIN.fill((30, 30, 30))
        draw_text(prompt, INSTRUCTION_FONT, WHITE, WIN, WIDTH // 2, HEIGHT // 2 - 50)

        # Render the current text.
        txt_surface = INSTRUCTION_FONT.render(user_text, True, color_active)

        # Resize the box if the text is too long.
        width = max(300, txt_surface.get_width() + 10)
        input_box.w = width

        # Blit the text.
        WIN.blit(txt_surface, (input_box.x + 5, input_box.y + 10))
        # Blit the input_box rect.
        pygame.draw.rect(WIN, color_active, input_box, 2)

        pygame.display.flip()
        CLOCK.tick(FPS)

def save_game_state(player, obstacles, obstacle_timer):
    save_name = get_text_input("Enter a name for your save game:")
    if save_name is None:
        return  # User canceled save

    # Replace spaces and illegal characters in filename
    filename = f'saves/{save_name.replace(" ", "_")}.json'

    game_state = {
        'player': {
            'x': player.rect.centerx,
            'y': player.rect.centery,
            'lives': player.lives,
            'score': player.score
        },
        'obstacles': [
            {
                'x': obs.rect.centerx,
                'y': obs.rect.centery,
                'speed': obs.speed
            } for obs in obstacles
        ],
        'obstacle_timer': obstacle_timer
    }

    if not os.path.exists('saves'):
        os.makedirs('saves')

    with open(filename, 'w') as f:
        json.dump(game_state, f)

    show_message(f"Game saved as '{save_name}'")

def load_game_menu():
    # Get list of saved games
    if not os.path.exists('saves'):
        show_message("No saved games found.")
        return None

    saved_games = [f for f in os.listdir('saves') if f.endswith('.json')]
    if not saved_games:
        show_message("No saved games found.")
        return None

    selected = 0
    menu_running = True
    while menu_running:
        WIN.fill((0, 0, 0))
        draw_text("Load Game", TITLE_FONT, YELLOW, WIN, WIDTH // 2, HEIGHT // 2 - 200)

        # Display saved games
        for idx, save_file in enumerate(saved_games):
            y_position = HEIGHT // 2 - 100 + idx * 50
            if idx == selected:
                color = YELLOW
            else:
                color = WHITE
            save_name = os.path.splitext(save_file)[0].replace("_", " ")
            draw_text(save_name, BUTTON_FONT, color, WIN, WIDTH // 2, y_position)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                menu_running = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(saved_games)
                if event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(saved_games)
                if event.key == pygame.K_RETURN:
                    filename = f'saves/{saved_games[selected]}'
                    with open(filename, 'r') as f:
                        game_state = json.load(f)
                    return game_state
                if event.key == pygame.K_ESCAPE:
                    menu_running = False
                    return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    for idx, save_file in enumerate(saved_games):
                        y_position = HEIGHT // 2 - 100 + idx * 50
                        text_rect = pygame.Rect(WIDTH // 2 - 100, y_position - 25, 200, 50)
                        if text_rect.collidepoint(event.pos):
                            filename = f'saves/{saved_games[idx]}'
                            with open(filename, 'r') as f:
                                game_state = json.load(f)
                            return game_state

        CLOCK.tick(FPS)

def start_screen():
    # Start background music
    pygame.mixer.music.play(-1)

    # Create stars for animated background
    stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT)] for _ in range(100)]
    star_speed = 1

    # Buttons
    button_width = 200
    button_height = 50
    start_button = pygame.Rect((WIDTH // 2 - button_width // 2, HEIGHT // 2 - 100), (button_width, button_height))
    load_button = pygame.Rect((WIDTH // 2 - button_width // 2, HEIGHT // 2 - 30), (button_width, button_height))
    quit_button = pygame.Rect((WIDTH // 2 - button_width // 2, HEIGHT // 2 + 40), (button_width, button_height))

    # Easter egg variables
    secret_code = []
    easter_egg_activated = False

    # Main loop for the start screen
    while True:
        WIN.blit(START_BG_IMAGE, (0, 0))

        # Animate stars
        for star in stars:
            pygame.draw.circle(WIN, WHITE, star, 2)
            star[1] += star_speed
            if star[1] > HEIGHT:
                star[0] = random.randint(0, WIDTH)
                star[1] = 0

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                # Easter egg code: Up, Up, Down, Down, Left, Right, Left, Right, B, A
                key_sequence = [
                    pygame.K_UP, pygame.K_UP, pygame.K_DOWN, pygame.K_DOWN,
                    pygame.K_LEFT, pygame.K_RIGHT, pygame.K_LEFT, pygame.K_RIGHT,
                    pygame.K_b, pygame.K_a
                ]
                secret_code.append(event.key)
                if secret_code == key_sequence[:len(secret_code)]:
                    if len(secret_code) == len(key_sequence):
                        easter_egg_activated = True
                        EASTER_EGG_SOUND.play()
                        show_message("Easter Egg Activated!")
                        secret_code = []
                else:
                    secret_code = []

            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos):
                    pygame.mixer.music.stop()
                    main(easter_egg_activated=easter_egg_activated)
                    return  # Start the game
                if load_button.collidepoint(event.pos):
                    pygame.mixer.music.stop()
                    game_state = load_game_menu()
                    if game_state:
                        main(game_state=game_state, easter_egg_activated=easter_egg_activated)
                    else:
                        pygame.mixer.music.play(-1)
                if quit_button.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

        # Draw title and buttons
        draw_text("Space Dodge", TITLE_FONT, YELLOW, WIN, WIDTH // 2, HEIGHT // 3 - 100)
        pygame.draw.rect(WIN, WHITE, start_button)
        pygame.draw.rect(WIN, WHITE, load_button)
        pygame.draw.rect(WIN, WHITE, quit_button)
        draw_text("Start Game", BUTTON_FONT, (0, 0, 0), WIN, WIDTH // 2, start_button.y + 25)
        draw_text("Load Game", BUTTON_FONT, (0, 0, 0), WIN, WIDTH // 2, load_button.y + 25)
        draw_text("Quit", BUTTON_FONT, (0, 0, 0), WIN, WIDTH // 2, quit_button.y + 25)
        draw_text("Developed by Your Name", CREDIT_FONT, WHITE, WIN, WIDTH // 2, HEIGHT - 30)

        pygame.display.flip()
        CLOCK.tick(FPS)

def pause_menu(player, obstacles, obstacle_timer):
    pygame.mixer.music.pause()  # Pause the game music

    # Create semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)  # Transparency level
    overlay.fill((0, 0, 0))  # Black overlay

    # Define buttons
    button_width = 200
    button_height = 50
    unpause_button = pygame.Rect((WIDTH // 2 - button_width // 2, HEIGHT // 2 - 120), (button_width, button_height))
    settings_button = pygame.Rect((WIDTH // 2 - button_width // 2, HEIGHT // 2 - 50), (button_width, button_height))
    save_button = pygame.Rect((WIDTH // 2 - button_width // 2, HEIGHT // 2 + 20), (button_width, button_height))
    quit_button = pygame.Rect((WIDTH // 2 - button_width // 2, HEIGHT // 2 + 90), (button_width, button_height))

    paused = True
    while paused:
        WIN.blit(overlay, (0, 0))
        draw_text("Game Paused", TITLE_FONT, YELLOW, WIN, WIDTH // 2, HEIGHT // 2 - 200)

        # Draw buttons
        pygame.draw.rect(WIN, WHITE, unpause_button)
        pygame.draw.rect(WIN, WHITE, settings_button)
        pygame.draw.rect(WIN, WHITE, save_button)
        pygame.draw.rect(WIN, WHITE, quit_button)

        draw_text("Resume", BUTTON_FONT, (0, 0, 0), WIN, WIDTH // 2, unpause_button.y + 25)
        draw_text("Settings", BUTTON_FONT, (0, 0, 0), WIN, WIDTH // 2, settings_button.y + 25)
        draw_text("Save Game", BUTTON_FONT, (0, 0, 0), WIN, WIDTH // 2, save_button.y + 25)
        draw_text("Quit", BUTTON_FONT, (0, 0, 0), WIN, WIDTH // 2, quit_button.y + 25)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                paused = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = False  # Unpause the game
            if event.type == pygame.MOUSEBUTTONDOWN:
                if unpause_button.collidepoint(event.pos):
                    paused = False
                elif settings_button.collidepoint(event.pos):
                    settings_menu()
                elif save_button.collidepoint(event.pos):
                    save_game_state(player, obstacles, obstacle_timer)
                elif quit_button.collidepoint(event.pos):
                    confirm_quit = confirmation_dialog("Are you sure you want to quit?")
                    if confirm_quit:
                        pygame.quit()
                        sys.exit()

        CLOCK.tick(FPS)

    pygame.mixer.music.unpause()  # Resume the game music

def settings_menu():
    # Create overlay
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))

    # Volume sliders
    global MUSIC_VOLUME, SFX_VOLUME
    slider_width = 300
    slider_height = 20
    music_slider = pygame.Rect((WIDTH // 2 - slider_width // 2, HEIGHT // 2 - 100), (slider_width, slider_height))
    sfx_slider = pygame.Rect((WIDTH // 2 - slider_width // 2, HEIGHT // 2), (slider_width, slider_height))

    adjusting_music = False
    adjusting_sfx = False

    settings_running = True
    while settings_running:
        WIN.blit(overlay, (0, 0))
        draw_text("Settings", TITLE_FONT, YELLOW, WIN, WIDTH // 2, HEIGHT // 2 - 200)

        # Draw sliders
        # Music Volume
        pygame.draw.rect(WIN, WHITE, music_slider)
        music_handle_x = music_slider.x + int(MUSIC_VOLUME * slider_width)
        pygame.draw.circle(WIN, YELLOW, (music_handle_x, music_slider.y + slider_height // 2), 10)
        draw_text("Music Volume", INSTRUCTION_FONT, WHITE, WIN, WIDTH // 2, music_slider.y - 30)

        # SFX Volume
        pygame.draw.rect(WIN, WHITE, sfx_slider)
        sfx_handle_x = sfx_slider.x + int(SFX_VOLUME * slider_width)
        pygame.draw.circle(WIN, YELLOW, (sfx_handle_x, sfx_slider.y + slider_height // 2), 10)
        draw_text("SFX Volume", INSTRUCTION_FONT, WHITE, WIN, WIDTH // 2, sfx_slider.y - 30)

        # Back Button
        back_button = pygame.Rect((WIDTH // 2 - 100, HEIGHT // 2 + 150), (200, 50))
        pygame.draw.rect(WIN, WHITE, back_button)
        draw_text("Back", BUTTON_FONT, (0, 0, 0), WIN, WIDTH // 2, back_button.y + 25)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                settings_running = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    save_settings()
                    settings_running = False
                elif music_slider.collidepoint(event.pos):
                    adjusting_music = True
                elif sfx_slider.collidepoint(event.pos):
                    adjusting_sfx = True
            if event.type == pygame.MOUSEBUTTONUP:
                adjusting_music = False
                adjusting_sfx = False
            if event.type == pygame.MOUSEMOTION:
                if adjusting_music:
                    mouse_x = event.pos[0]
                    music_volume = (mouse_x - music_slider.x) / slider_width
                    MUSIC_VOLUME = max(0.0, min(1.0, music_volume))
                    pygame.mixer.music.set_volume(MUSIC_VOLUME)
                if adjusting_sfx:
                    mouse_x = event.pos[0]
                    sfx_volume = (mouse_x - sfx_slider.x) / slider_width
                    SFX_VOLUME = max(0.0, min(1.0, sfx_volume))
                    CRASH_SOUND.set_volume(SFX_VOLUME)
                    EASTER_EGG_SOUND.set_volume(SFX_VOLUME)

        CLOCK.tick(FPS)

def confirmation_dialog(message):
    # Create overlay
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))

    # Buttons
    button_width = 150
    button_height = 50
    yes_button = pygame.Rect((WIDTH // 2 - button_width - 10, HEIGHT // 2 + 50), (button_width, button_height))
    no_button = pygame.Rect((WIDTH // 2 + 10, HEIGHT // 2 + 50), (button_width, button_height))

    confirming = True
    while confirming:
        WIN.blit(overlay, (0, 0))
        draw_text(message, INSTRUCTION_FONT, WHITE, WIN, WIDTH // 2, HEIGHT // 2 - 50)

        # Draw buttons
        pygame.draw.rect(WIN, WHITE, yes_button)
        pygame.draw.rect(WIN, WHITE, no_button)
        draw_text("Yes", BUTTON_FONT, (0, 0, 0), WIN, yes_button.centerx, yes_button.centery)
        draw_text("No", BUTTON_FONT, (0, 0, 0), WIN, no_button.centerx, no_button.centery)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                confirming = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if yes_button.collidepoint(event.pos):
                    return True
                elif no_button.collidepoint(event.pos):
                    return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

        CLOCK.tick(FPS)

def show_message(message):
    message_displayed = True
    display_time = 2  # seconds
    start_time = pygame.time.get_ticks()

    while message_displayed:
        elapsed_time = (pygame.time.get_ticks() - start_time) / 1000
        if elapsed_time > display_time:
            message_displayed = False

        WIN.blit(BACKGROUND_IMAGE, (0, 0))
        draw_text(message, INSTRUCTION_FONT, WHITE, WIN, WIDTH // 2, HEIGHT // 2)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                message_displayed = False
                pygame.quit()
                sys.exit()

        CLOCK.tick(FPS)

def countdown():
    for i in range(3, 0, -1):
        WIN.blit(BACKGROUND_IMAGE, (0, 0))
        draw_text(str(i), TITLE_FONT, YELLOW, WIN, WIDTH // 2, HEIGHT // 2)
        pygame.display.flip()
        pygame.time.delay(1000)  # Wait 1 second

def game_over_screen(player):
    pygame.mixer.music.stop()
    draw_text("Game Over", TITLE_FONT, YELLOW, WIN, WIDTH // 2, HEIGHT // 2 - 50)
    draw_text(f"Score: {player.score}", INSTRUCTION_FONT, WHITE, WIN, WIDTH // 2, HEIGHT // 2 + 20)
    draw_text("Press 'R' to restart or 'Q' to quit", INSTRUCTION_FONT, WHITE, WIN, WIDTH // 2, HEIGHT // 2 + 60)
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                waiting = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    waiting = False
                    main()
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
        CLOCK.tick(FPS)

def main(game_state=None, easter_egg_activated=False):
    # Start the game background music
    pygame.mixer.music.load(GAME_MUSIC)
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(MUSIC_VOLUME)
    CRASH_SOUND.set_volume(SFX_VOLUME)
    EASTER_EGG_SOUND.set_volume(SFX_VOLUME)

    if game_state:
        # Load player data
        player_data = game_state['player']
        player = Player(
            x=player_data['x'],
            y=player_data['y'],
            speed=5,
            lives=player_data['lives'],
            score=player_data['score']
        )

        # Load obstacles data
        obstacles = []
        for obs_data in game_state['obstacles']:
            obs = Obstacle()
            obs.rect.centerx = obs_data['x']
            obs.rect.centery = obs_data['y']
            obs.speed = obs_data['speed']
            obstacles.append(obs)

        # Load obstacle_timer
        obstacle_timer = game_state.get('obstacle_timer', 0)

        # Display a message before resuming
        show_message("Resuming saved game...")
        countdown()
    else:
        # Initialize new game
        player = Player(WIDTH // 2, HEIGHT - 60, speed=5)
        obstacles = []
        obstacle_timer = 0
        if easter_egg_activated:
            player.lives = 99  # Easter egg effect: give the player 99 lives

    running = True
    while running:
        CLOCK.tick(FPS)
        obstacle_timer += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pause_menu(player, obstacles, obstacle_timer)

        # Spawn a new obstacle every 60 frames (1 second at 60 FPS)
        if obstacle_timer >= FPS:
            obstacles.append(Obstacle())
            obstacle_timer = 0

        # Move and draw obstacles
        for obstacle in obstacles[:]:
            obstacle.move()
            if obstacle.rect.top > HEIGHT:
                obstacles.remove(obstacle)
                player.score += 1  # Increase score when an obstacle passes by
            elif obstacle.rect.colliderect(player.rect):
                player.lives -= 1
                CRASH_SOUND.play()
                obstacles.remove(obstacle)
                if player.lives == 0:
                    game_over_screen(player)
                    return

        # Move the player
        player.move()

        # Draw everything
        WIN.blit(BACKGROUND_IMAGE, (0, 0))
        player.draw(WIN)
        for obstacle in obstacles:
            obstacle.draw(WIN)

        # Draw the score and lives
        draw_text(f"Score: {player.score}", INSTRUCTION_FONT, WHITE, WIN, 80, 30)
        draw_text(f"Lives: {player.lives}", INSTRUCTION_FONT, WHITE, WIN, WIDTH - 80, 30)

        pygame.display.flip()

# Start the game
start_screen()
