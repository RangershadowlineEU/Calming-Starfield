import pygame
import random
import sys
import math
import json

# Constants (will be updated from config)
WIDTH = 800
HEIGHT = 600
FPS = 60
ATTRACTION_STRENGTH = 0.01
REPULSION_THRESHOLD = 50
REPULSION_STRENGTH = 0.02
FADE_DURATION = 3  # seconds
NUM_PARTICLES = 200
PARTICLE_SIZE = 1
PULSE_AMPLITUDE = 1.0
PULSE_SPEED = 0.05

# Resolutions for dropdown
resolutions = ["1280x720", "1920x1080", "2560x1440", "3440x1440", "3840x2160"]

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Calming color palette for stars
CALMING_COLORS = [
    (173, 216, 230),  # light blue
    (230, 230, 250),  # lavender
    (152, 251, 152),  # mint green
    (255, 218, 185),  # peach
    (135, 206, 235),  # sky blue
    (255, 255, 224),  # pale yellow
]

# Function to create default gradient background
def create_gradient_background(width, height):
    surface = pygame.Surface((width, height))
    for y in range(height):
        # Gradient from black to dark blue
        blue_value = int(50 * (1 - y / height))
        color = (0, 0, blue_value)
        pygame.draw.line(surface, color, (0, y), (width, y))
    return surface

# Slider class for menu
class Slider:
    def __init__(self, x, y, width, min_val, max_val, initial_val):
        self.x = x
        self.y = y
        self.width = width
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.dragging = False

    def draw(self, screen, font):
        # Draw bar
        pygame.draw.rect(screen, (200, 200, 200), (self.x, self.y, self.width, 10))
        # Draw knob
        knob_x = self.x + (self.value - self.min_val) / (self.max_val - self.min_val) * self.width
        pygame.draw.circle(screen, (255, 255, 255), (int(knob_x), self.y + 5), 8)
        # Draw value
        value_text = font.render(f"{self.value:.2f}", True, (255, 255, 255))
        screen.blit(value_text, (self.x + self.width + 10, self.y - 5))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.x <= event.pos[0] <= self.x + self.width and self.y <= event.pos[1] <= self.y + 10:
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            knob_x = max(self.x, min(self.x + self.width, event.pos[0]))
            self.value = self.min_val + (knob_x - self.x) / self.width * (self.max_val - self.min_val)

    def get_value(self):
        return self.value

# Dropdown class for menu
class Dropdown:
    def __init__(self, x, y, width, options, initial_index):
        self.x = x
        self.y = y
        self.width = width
        self.height = 30  # Height of selected item
        self.options = options
        self.selected = initial_index
        self.expanded = False

    def draw(self, screen, font):
        # Draw selected
        pygame.draw.rect(screen, (200, 200, 200), (self.x, self.y, self.width, 30))
        text = font.render(self.options[self.selected], True, (0, 0, 0))
        screen.blit(text, (self.x + 5, self.y + 5))
        # Draw arrow
        pygame.draw.polygon(screen, (0, 0, 0), [(self.x + self.width - 20, self.y + 10), (self.x + self.width - 10, self.y + 10), (self.x + self.width - 15, self.y + 20)])
        if self.expanded:
            for i, option in enumerate(self.options):
                pygame.draw.rect(screen, (220, 220, 220), (self.x, self.y + 30 + i * 30, self.width, 30))
                text = font.render(option, True, (0, 0, 0))
                screen.blit(text, (self.x + 5, self.y + 35 + i * 30))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.x <= event.pos[0] <= self.x + self.width and self.y <= event.pos[1] <= self.y + 30:
                self.expanded = not self.expanded
            elif self.expanded:
                for i in range(len(self.options)):
                    if self.x <= event.pos[0] <= self.x + self.width and self.y + 30 + i * 30 <= event.pos[1] <= self.y + 60 + i * 30:
                        self.selected = i
                        self.expanded = False
                        break

    def get_value(self):
        w, h = self.options[self.selected].split('x')
        return int(w), int(h)

# Button class for menu
class Button:
    def __init__(self, x, y, width, height, text):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text

    def draw(self, screen, font):
        pygame.draw.rect(screen, (200, 200, 200), (self.x, self.y, self.width, self.height))
        text_surf = font.render(self.text, True, (0, 0, 0))
        screen.blit(text_surf, (self.x + (self.width - text_surf.get_width()) // 2, self.y + (self.height - text_surf.get_height()) // 2))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.x <= event.pos[0] <= self.x + self.width and self.y <= event.pos[1] <= self.y + self.height:
                return True
        return False

# OptionsMenu class for organized menu management
class OptionsMenu:
    def __init__(self, resolutions, initial_res_index, fps, num_particles, fade_duration, attraction_strength, repulsion_threshold, repulsion_strength, particle_size, pulse_amplitude, pulse_speed):
        self.alpha = 0

        # Labels positions (local) - Resolution dropdown positioned above all sliders
        self.fullscreen_label_pos = (20, 20)
        self.resolution_label_pos = (20, 60)
        self.slider_label_positions = {
            'fps': (20, 115),
            'num_particles': (20, 155),
            'fade_duration': (20, 195),
            'attraction_strength': (20, 235),
            'repulsion_threshold': (20, 275),
            'repulsion_strength': (20, 315),
            'particle_size': (20, 355),
            'pulse_amplitude': (20, 395),
            'pulse_speed': (20, 435)
        }
        self.instr_pos = (20, 520)
        self.revert_pos = (20, 550)

        # Elements - Resolution dropdown positioned above all sliders
        self.fullscreen_button = Button(200, 15, 200, 30, "Toggle Fullscreen")
        self.resolution_dropdown = Dropdown(200, 55, 200, resolutions, initial_res_index)
        self.sliders = {
            'fps': Slider(20, 140, 300, 30, 120, fps),
            'num_particles': Slider(20, 180, 300, 50, 500, num_particles),
            'fade_duration': Slider(20, 220, 300, 1, 10, fade_duration),
            'attraction_strength': Slider(20, 260, 300, 0.005, 0.05, attraction_strength),
            'repulsion_threshold': Slider(20, 300, 300, 20, 100, repulsion_threshold),
            'repulsion_strength': Slider(20, 340, 300, 0.01, 0.1, repulsion_strength),
            'particle_size': Slider(20, 380, 300, 1, 10, particle_size),
            'pulse_amplitude': Slider(20, 420, 300, 0.5, 2.0, pulse_amplitude),
            'pulse_speed': Slider(20, 460, 300, 0.01, 0.1, pulse_speed)
        }

    def get_width(self):
        # Max right edge
        max_x = max(
            self.fullscreen_button.x + self.fullscreen_button.width,
            self.resolution_dropdown.x + self.resolution_dropdown.width,
            max(slider.x + slider.width + 60 for slider in self.sliders.values()),  # +60 for value text
            max(pos[0] + 150 for pos in self.slider_label_positions.values()),  # label width
            self.instr_pos[0] + 200,  # instruction width
            self.revert_pos[0] + 200
        )
        return max_x + 20  # padding

    def get_height(self):
        # Max bottom edge
        max_y = max(
            self.fullscreen_button.y + self.fullscreen_button.height,
            self.resolution_dropdown.y + self.resolution_dropdown.height + 30 * len(self.resolution_dropdown.options),  # expanded
            max(slider.y + 10 for slider in self.sliders.values()),
            self.revert_pos[1] + 20
        )
        return max_y + 20  # padding

    def update_alpha(self, target):
        if self.alpha < target:
            self.alpha = min(self.alpha + 10, target)
        elif self.alpha > target:
            self.alpha = max(self.alpha - 10, target)

    def draw(self, screen, font, offset_x, offset_y):
        # Adjust element positions
        self.fullscreen_button.x += offset_x
        self.fullscreen_button.y += offset_y
        self.resolution_dropdown.x += offset_x
        self.resolution_dropdown.y += offset_y
        for slider in self.sliders.values():
            slider.x += offset_x
            slider.y += offset_y

        # Draw labels
        labels = ["Fullscreen", "Resolution", "FPS", "Num Particles", "Fade Duration", "Attraction Strength",
                  "Repulsion Threshold", "Repulsion Strength", "Particle Size", "Pulse Amplitude", "Pulse Speed"]
        for i, label in enumerate(labels):
            text = font.render(label, True, (255, 255, 255))
            if i == 0:
                screen.blit(text, (self.fullscreen_label_pos[0] + offset_x, self.fullscreen_label_pos[1] + offset_y))
            elif i == 1:
                screen.blit(text, (self.resolution_label_pos[0] + offset_x, self.resolution_label_pos[1] + offset_y))
            else:
                key = list(self.slider_label_positions.keys())[i-2]
                screen.blit(text, (self.slider_label_positions[key][0] + offset_x, self.slider_label_positions[key][1] + offset_y))

        # Draw elements
        self.resolution_dropdown.draw(screen, font)
        self.fullscreen_button.draw(screen, font)
        for slider in self.sliders.values():
            slider.draw(screen, font)

        # Instructions
        instr = font.render("Press O to toggle menu", True, (255, 255, 255))
        screen.blit(instr, (self.instr_pos[0] + offset_x, self.instr_pos[1] + offset_y))
        revert = font.render("Press R to Revert to Defaults", True, (255, 255, 255))
        screen.blit(revert, (self.revert_pos[0] + offset_x, self.revert_pos[1] + offset_y))

        # Restore positions
        self.fullscreen_button.x -= offset_x
        self.fullscreen_button.y -= offset_y
        self.resolution_dropdown.x -= offset_x
        self.resolution_dropdown.y -= offset_y
        for slider in self.sliders.values():
            slider.x -= offset_x
            slider.y -= offset_y

    def handle_event(self, event, offset_x, offset_y):
        # Adjust element positions for event handling
        self.fullscreen_button.x += offset_x
        self.fullscreen_button.y += offset_y
        self.resolution_dropdown.x += offset_x
        self.resolution_dropdown.y += offset_y
        for slider in self.sliders.values():
            slider.x += offset_x
            slider.y += offset_y

        # Handle events
        result = self.fullscreen_button.handle_event(event)
        self.resolution_dropdown.handle_event(event)
        for slider in self.sliders.values():
            slider.handle_event(event)

        # Restore positions
        self.fullscreen_button.x -= offset_x
        self.fullscreen_button.y -= offset_y
        self.resolution_dropdown.x -= offset_x
        self.resolution_dropdown.y -= offset_y
        for slider in self.sliders.values():
            slider.x -= offset_x
            slider.y -= offset_y

        return result  # for fullscreen toggle

# Load config
def load_config():
    global WIDTH, HEIGHT, FPS, ATTRACTION_STRENGTH, REPULSION_THRESHOLD, REPULSION_STRENGTH, FADE_DURATION, NUM_PARTICLES, PARTICLE_SIZE, PULSE_AMPLITUDE, PULSE_SPEED
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        WIDTH = config.get('width', 800)
        HEIGHT = config.get('height', 600)
        FPS = config.get('fps', 60)
        ATTRACTION_STRENGTH = config.get('attraction_strength', 0.01)
        REPULSION_THRESHOLD = config.get('repulsion_threshold', 50)
        REPULSION_STRENGTH = config.get('repulsion_strength', 0.02)
        FADE_DURATION = config.get('fade_duration', 3)
        NUM_PARTICLES = config.get('num_particles', 200)
        PARTICLE_SIZE = config.get('particle_size', 1)
        PULSE_AMPLITUDE = config.get('pulse_amplitude', 1.0)
        PULSE_SPEED = config.get('pulse_speed', 0.05)
    except:
        pass

# Save config
def save_config():
    config = {
        'width': WIDTH,
        'height': HEIGHT,
        'fps': FPS,
        'attraction_strength': ATTRACTION_STRENGTH,
        'repulsion_threshold': REPULSION_THRESHOLD,
        'repulsion_strength': REPULSION_STRENGTH,
        'fade_duration': FADE_DURATION,
        'num_particles': NUM_PARTICLES,
        'particle_size': PARTICLE_SIZE,
        'pulse_amplitude': PULSE_AMPLITUDE,
        'pulse_speed': PULSE_SPEED
    }
    with open('config.json', 'w') as f:
        json.dump(config, f)

# Revert to default settings
def revert_to_defaults(menu):
    global WIDTH, HEIGHT, FPS, ATTRACTION_STRENGTH, REPULSION_THRESHOLD, REPULSION_STRENGTH, FADE_DURATION, NUM_PARTICLES, PARTICLE_SIZE, PULSE_AMPLITUDE, PULSE_SPEED
    WIDTH = 800
    HEIGHT = 600
    FPS = 60
    ATTRACTION_STRENGTH = 0.01
    REPULSION_THRESHOLD = 50
    REPULSION_STRENGTH = 0.02
    FADE_DURATION = 3
    NUM_PARTICLES = 200
    PARTICLE_SIZE = 1
    PULSE_AMPLITUDE = 1.0
    PULSE_SPEED = 0.05
    # Update sliders
    menu.sliders['fps'].value = FPS
    menu.sliders['num_particles'].value = NUM_PARTICLES
    menu.sliders['fade_duration'].value = FADE_DURATION
    menu.sliders['attraction_strength'].value = ATTRACTION_STRENGTH
    menu.sliders['repulsion_threshold'].value = REPULSION_THRESHOLD
    menu.sliders['repulsion_strength'].value = REPULSION_STRENGTH
    menu.sliders['particle_size'].value = PARTICLE_SIZE
    menu.sliders['pulse_amplitude'].value = PULSE_AMPLITUDE
    menu.sliders['pulse_speed'].value = PULSE_SPEED
    # Update dropdown
    for i, res in enumerate(resolutions):
        w, h = res.split('x')
        if int(w) == WIDTH and int(h) == HEIGHT:
            menu.resolution_dropdown.selected = i
            break

# Star class
class Star:
    def __init__(self, x, y, size, speed):
        self.x = x
        self.y = y
        self.base_size = size
        self.size = size
        self.speed = speed
        self.color = random.choice(CALMING_COLORS)
        self.pulse_amplitude = random.uniform(0.5, 1.5)
        self.pulse_speed = random.uniform(0.01, 0.05)
        self.state = 'fading_in'
        self.alpha = 0
        self.fade_in_rate = 255 / (random.uniform(FADE_DURATION - 0.5, FADE_DURATION + 0.5) * FPS)
        self.active_timer = 0
        self.active_duration = random.uniform(2, 5) * FPS
        self.fade_out_rate = 255 / (random.uniform(FADE_DURATION - 0.5, FADE_DURATION + 0.5) * FPS)

    def respawn(self, screen_width, screen_height):
        self.x = random.randint(0, screen_width)
        self.y = random.randint(0, screen_height)
        self.color = random.choice(CALMING_COLORS)
        self.base_size = random.randint(1, 3)
        self.size = self.base_size
        self.pulse_amplitude = random.uniform(0.5, 1.5)
        self.pulse_speed = random.uniform(0.01, 0.05)
        self.state = 'fading_in'
        self.alpha = 0
        self.fade_in_rate = 255 / (random.uniform(FADE_DURATION - 0.5, FADE_DURATION + 0.5) * FPS)
        self.active_timer = 0
        self.active_duration = random.uniform(2, 5) * FPS
        self.fade_out_rate = 255 / (random.uniform(FADE_DURATION - 0.5, FADE_DURATION + 0.5) * FPS)

    def update(self, mouse_x, mouse_y, screen_width, screen_height):
        # Pulsing size effect
        self.size = self.base_size + self.pulse_amplitude * math.sin(pygame.time.get_ticks() * 0.001 * self.pulse_speed)
        self.size = max(1, self.size)

        # State-based fading
        if self.state == 'fading_in':
            self.alpha += self.fade_in_rate
            if self.alpha >= 255:
                self.alpha = 255
                self.state = 'active'
                self.active_timer = 0
        elif self.state == 'active':
            self.active_timer += 1
            if self.active_timer >= self.active_duration:
                self.state = 'fading_out'
        elif self.state == 'fading_out':
            self.alpha -= self.fade_out_rate
            if self.alpha <= 0:
                self.respawn(screen_width, screen_height)
                return

        # Proximity-based movement (only if visible)
        if self.alpha > 0:
            dx = mouse_x - self.x
            dy = mouse_y - self.y
            distance = math.sqrt(dx**2 + dy**2)

            if distance > 0:
                if distance < REPULSION_THRESHOLD:
                    # Repulsion for close particles
                    force = REPULSION_STRENGTH / distance
                    dx = -dx / distance * force
                    dy = -dy / distance * force
                    # Add randomness for swirling effect
                    self.x += random.uniform(-0.1, 0.1)
                    self.y += random.uniform(-0.1, 0.1)
                else:
                    # Attraction for distant particles
                    force = ATTRACTION_STRENGTH * (distance / 100)
                    dx = dx / distance * force
                    dy = dy / distance * force

                self.x += dx
                self.y += dy

        # Wrap around screen
        if self.x < 0:
            self.x = screen_width
        elif self.x > screen_width:
            self.x = 0
        if self.y < 0:
            self.y = screen_height
        elif self.y > screen_height:
            self.y = 0

    def draw(self, screen):
        if self.alpha > 0:
            surface = pygame.Surface((int(self.size*2) + 4, int(self.size*2) + 4), pygame.SRCALPHA)
            pygame.draw.circle(surface, (*self.color, int(self.alpha)), (int(self.size) + 2, int(self.size) + 2), int(self.size))
            screen.blit(surface, (int(self.x - self.size - 2), int(self.y - self.size - 2)))

# Main function
def main():
    load_config()
    global FPS, ATTRACTION_STRENGTH, REPULSION_THRESHOLD, REPULSION_STRENGTH, FADE_DURATION, NUM_PARTICLES, PARTICLE_SIZE, PULSE_AMPLITUDE, PULSE_SPEED, sliders
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Calming Starfield")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)
    startup = True

    # Load background
    try:
        background = pygame.image.load('background.png')
        background = pygame.transform.scale(background, (WIDTH, HEIGHT))
    except:
        background = create_gradient_background(WIDTH, HEIGHT)

    # Menu state
    in_menu = False
    is_fullscreen = False
    current_width = WIDTH
    current_height = HEIGHT
    initial_res_index = 0
    for i, res in enumerate(resolutions):
        w, h = res.split('x')
        if int(w) == WIDTH and int(h) == HEIGHT:
            initial_res_index = i
            break
    menu = OptionsMenu(resolutions, initial_res_index, FPS, NUM_PARTICLES, FADE_DURATION, ATTRACTION_STRENGTH, REPULSION_THRESHOLD, REPULSION_STRENGTH, PARTICLE_SIZE, PULSE_AMPLITUDE, PULSE_SPEED)

    # Initialize menu position variables
    bg_x = 0
    bg_y = 0

    def update_menu_position():
        nonlocal bg_x, bg_y
        menu_width = menu.get_width()
        menu_height = menu.get_height()
        bg_x = (screen.get_width() - menu_width) // 2
        bg_y = (screen.get_height() - menu_height) // 2

    # Calculate initial menu position (centered)
    update_menu_position()

    stars = []
    for _ in range(NUM_PARTICLES):
        star = Star(0, 0, PARTICLE_SIZE, 0.1)
        star.respawn(WIDTH, HEIGHT)
        stars.append(star)

    running = True
    while running:
        current_fps = int(menu.sliders['fps'].get_value())
        clock.tick(current_fps)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if startup:
                    startup = False
                if event.key == pygame.K_o:
                    in_menu = not in_menu
                elif event.key == pygame.K_r:
                    revert_to_defaults(menu)
                elif event.key == pygame.K_ESCAPE:
                    if is_fullscreen:
                        is_fullscreen = False
                        screen = pygame.display.set_mode((current_width, current_height))
                        # Reload background
                        try:
                            background = pygame.image.load('background.png')
                            background = pygame.transform.scale(background, (current_width, current_height))
                        except:
                            background = create_gradient_background(current_width, current_height)
                        # Update menu position for new screen size
                        update_menu_position()
                    else:
                        running = False
            if in_menu:
                if menu.handle_event(event, bg_x, bg_y):
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.NOFRAME)
                    else:
                        screen = pygame.display.set_mode((current_width, current_height))
                        # Reload background
                        try:
                            background = pygame.image.load('background.png')
                            background = pygame.transform.scale(background, (current_width, current_height))
                        except:
                            background = create_gradient_background(current_width, current_height)
                    # Update menu position for new screen size
                    update_menu_position()

        # Update settings from sliders and dropdown
        FPS = int(menu.sliders['fps'].get_value())
        new_width, new_height = menu.resolution_dropdown.get_value()
        ATTRACTION_STRENGTH = menu.sliders['attraction_strength'].get_value()
        REPULSION_THRESHOLD = menu.sliders['repulsion_threshold'].get_value()
        REPULSION_STRENGTH = menu.sliders['repulsion_strength'].get_value()
        FADE_DURATION = menu.sliders['fade_duration'].get_value()
        target_particles = int(menu.sliders['num_particles'].get_value())
        PARTICLE_SIZE = int(menu.sliders['particle_size'].get_value())
        PULSE_AMPLITUDE = menu.sliders['pulse_amplitude'].get_value()
        PULSE_SPEED = menu.sliders['pulse_speed'].get_value()

        # Update window size if changed
        if new_width != current_width or new_height != current_height:
            current_width = new_width
            current_height = new_height
            if not is_fullscreen:
                screen = pygame.display.set_mode((current_width, current_height))
                # Reload background
                try:
                    background = pygame.image.load('background.png')
                    background = pygame.transform.scale(background, (current_width, current_height))
                except:
                    background = create_gradient_background(current_width, current_height)
            # Update menu position for new screen size
            update_menu_position()

        # Adjust particle count
        if len(stars) < target_particles:
            for _ in range(target_particles - len(stars)):
                star = Star(0, 0, PARTICLE_SIZE, 0.1)
                star.respawn(screen.get_width(), screen.get_height())
                stars.append(star)
        elif len(stars) > target_particles:
            stars = stars[:target_particles]

        mouse_x, mouse_y = pygame.mouse.get_pos()

        if startup:
            screen.fill((0, 0, 0))
            screen_width = screen.get_width()
            screen_height = screen.get_height()
            title = font.render("Welcome to Calming Starfield", True, (255, 255, 255))
            screen.blit(title, (screen_width // 2 - title.get_width() // 2, screen_height // 2 - 120))
            author = font.render("Created by ShadowlineEU using Kilo Code", True, (200, 200, 200))
            screen.blit(author, (screen_width // 2 - author.get_width() // 2, screen_height // 2 - 80))
            options = font.render("Press 'O' to open Options Menu", True, (200, 200, 200))
            screen.blit(options, (screen_width // 2 - options.get_width() // 2, screen_height // 2 - 40))
            bg_info = font.render("Customize background.png to change the theme", True, (200, 200, 200))
            screen.blit(bg_info, (screen_width // 2 - bg_info.get_width() // 2, screen_height // 2))
            start = font.render("Press any key to start", True, (200, 200, 200))
            screen.blit(start, (screen_width // 2 - start.get_width() // 2, screen_height // 2 + 40))
        else:
            screen.blit(background, (0, 0))

            if in_menu:
                # Update menu alpha for fade
                menu.update_alpha(200)

                # Draw menu background
                current_menu_width = menu.get_width()
                current_menu_height = menu.get_height()
                menu_bg = pygame.Surface((current_menu_width, current_menu_height))
                menu_bg.set_alpha(menu.alpha)
                menu_bg.fill((0, 0, 0))
                screen.blit(menu_bg, (bg_x, bg_y))

                # Draw menu
                menu.draw(screen, font, bg_x, bg_y)
            else:
                # Fade out
                menu.update_alpha(0)
                for star in stars:
                    star.update(mouse_x, mouse_y, screen.get_width(), screen.get_height())
                    star.draw(screen)

        pygame.display.flip()

    save_config()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()