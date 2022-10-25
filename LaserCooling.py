# Laser cooling applet
# By Matthew Houtput (matthew.houtput@uantwerpen.be)
# Original idea and implementation: Physics-2000, JILA (University of Colorado, Boulder)

# Requires the NumPy and Pygame packages to be installed on your system

import os
import sys

import pygame
from pygame.locals import *

import numpy as np
from random import uniform
import colorsys

# These two lines are necessary to package the .py file into an executable using PyInstaller,
# but can be ignored if the script is simply run as Python code
# If the code runs as an executable ('frozen'), change directory to the temporary MEIPASS folder
# where all external files are stored
# On Windows, the MEIPASS folder is located at C:\Users\xxxxxx\AppData\Local\Temp\_MEIxxxxxx
if getattr(sys, 'frozen', False):
    # noinspection PyProtectedMember
    os.chdir(sys._MEIPASS)

# ===== INITIALIZE SOME USEFUL CONSTANTS =====
# Dimensions of the screen
PLAY_WIDTH = 608
PLAY_HEIGHT = 256
LEFT_BORDER = 96
RIGHT_BORDER = 96
TOP_BORDER = 48
BOTTOM_BORDER = 160
WINDOW_WIDTH = LEFT_BORDER + PLAY_WIDTH + RIGHT_BORDER
WINDOW_HEIGHT = TOP_BORDER + PLAY_HEIGHT + BOTTOM_BORDER


# Colors
WHITE = (255, 255, 255)
LIGHT_GRAY = (192, 192, 192)
LIGHTISH_GRAY = (159, 159, 159)
GRAY = (127, 127, 127)
DARK_GRAY = (79, 79, 79)
BLACK = (0, 0, 0)

# Gameplay attributes
FPS = 30  # Framerate
ATOM_RADIUS = 16
SPEED_OF_LIGHT = 8  # Speed of the photons, in pixels/frame
ATOM_COLLISION_SPEED_GAIN = 0.175  # The speed an atom gains when a photon collides with it, in pixels/frame
HUE_MIN = 0.  # Hue of the lowest color on the slider (red)
HUE_MAX = 282.  # Hue of the highest color on the slider (purple)
HUE_ABSORPTION_RANGE = 25  # The photon is absorbed by an atom if the difference in hues is at most HUE_ABSORPTION_RANGE
TIMES_BETWEEN_ATOMS_INITIAL = (300, 300, 300)  # For level (1, 2, 3); measured in frames, not in seconds
TIMES_BETWEEN_ATOMS_FINAL = (150, 210, 120)

# Parameters related to the Doppler effect implementation
SPEED_OF_LIGHT_DOPPLER = 16  # Speed of light used for the Doppler effect, in pixels/frame
FREQ_MIN = SPEED_OF_LIGHT_DOPPLER/700  # Frequency of the lowest color, in arbitrary units
FREQ_MAX = SPEED_OF_LIGHT_DOPPLER/400  # Frequency of the highest color, in arbitrary units


# ===== MAIN FUNCTION =====
def main():
    # Set up pygame and the display
    pygame.init()
    fps_clock = pygame.time.Clock()
    display_surf = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption('Laser cooling')

    # Initialize fonts
    font_normal = pygame.font.SysFont('verdana', 18)
    font_large = pygame.font.SysFont('verdana', 24)

    # Initialize some mouse variables
    mouse_xy = (0, 0)
    mouse_is_down = False

    # Create the slider bars, and the buttons to change level
    slider_intensity = Slider(display_surf, (LEFT_BORDER + 192, WINDOW_HEIGHT-BOTTOM_BORDER + 32,
                                             WINDOW_WIDTH - RIGHT_BORDER - 192 - (LEFT_BORDER + 192), 12),
                              'horizontal', (0.5, 2.), None, (16, 24), 'Intensity', font_normal, LIGHT_GRAY)
    slider_hue = HueSlider(display_surf, (LEFT_BORDER + 192, WINDOW_HEIGHT-BOTTOM_BORDER + 96,
                                          WINDOW_WIDTH - RIGHT_BORDER - 192 - (LEFT_BORDER + 192), 12),
                           'horizontal', (HUE_MIN, HUE_MAX), 141., (16, 24), 'Frequency', font_normal, LIGHT_GRAY)
    button_nextlevel = ImageButton(display_surf, (WINDOW_WIDTH - 80, WINDOW_HEIGHT-80, 64, 64),
                                   'images/Next_idle.png', 'images/Next_hover.png')
    button_prevlevel = ImageButton(display_surf, (16, WINDOW_HEIGHT-80, 64, 64),
                                   'images/Prev_idle.png', 'images/Prev_hover.png')

    # Create the laser
    laser = Laser(display_surf, (WINDOW_WIDTH - RIGHT_BORDER, TOP_BORDER, 64, PLAY_HEIGHT))

    # Initialize the atom and photon lists
    atoms = []
    photons = []

    # Initialize the atom timer
    atom_timer = (int(max(TIMES_BETWEEN_ATOMS_INITIAL[0]-150, 1)), TIMES_BETWEEN_ATOMS_INITIAL[0])

    # Initialize some other variables
    current_level = 1
    hsv_color = None
    flag_restart = False

    # Main game loop:
    while True:
        # Get the user input from the mouse
        mouse_is_clicked = False
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            elif event.type == MOUSEMOTION:
                mouse_xy = event.pos
            elif event.type == MOUSEBUTTONDOWN and event.button == 1:  # "and" is short-circuited
                mouse_xy = event.pos
                mouse_is_down = True
                mouse_is_clicked = True
            elif event.type == MOUSEBUTTONUP and event.button == 1:
                mouse_xy = event.pos
                mouse_is_clicked = False
                mouse_is_down = False
        mouse_state = (mouse_xy, mouse_is_clicked, mouse_is_down)

        # Create new atoms with a delay between them
        atom_timer = run_atom_timer(atoms, atom_timer, current_level, hsv_color)

        # Draw and control everything, first the bottom layers and then the top layers
        # Draw the gray background:
        pygame.draw.rect(display_surf, LIGHTISH_GRAY, (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
        # Draw, move, and collide all atoms and photons:
        for particle in photons+atoms:
            particle.move()
            particle.draw(display_surf)
        for atom in atoms:
            atom.collide(photons)
        remove_outside_atoms(atoms)
        # Draw the gray borders on the edges of the screen:
        draw_borders(display_surf)
        # Draw the text on top of the borders:
        draw_text(display_surf, atoms, font_large, font_normal, current_level)

        # Draw and control the buttons, the slider bars, and the laser
        # The 'control' function draws the button, and return True if the button is clicked
        if current_level < 3 and button_nextlevel.control(mouse_state):
            # "and" is short-circuited, so the button isn't drawn if current_level = 3
            current_level = min(current_level+1, 3)
            flag_restart = True
        if current_level > 1 and button_prevlevel.control(mouse_state):
            current_level = max(current_level-1, 1)
            flag_restart = True
        if current_level > 1:
            # The 'control' function draws the slider, and returns the value it is currently on
            color_hue = slider_hue.control(mouse_state)
        else:
            color_hue = 140
        laser.set_fire_rate(slider_intensity.control(mouse_state))
        laser.control_shoot(mouse_state, color_hue, photons)

        if flag_restart:
            # Re-setup the room by clearing all particles, and resetting the atom timer
            atoms = []
            photons = []
            atom_timer = (int(max(TIMES_BETWEEN_ATOMS_INITIAL[0]-100, 1)),
                          TIMES_BETWEEN_ATOMS_INITIAL[0])
            if current_level == 3:
                hsv_color = (int(uniform(80, 240)), 100, 100)
            else:
                hsv_color = None
            flag_restart = False

        # Update the screen and wait until the next step:
        pygame.display.update()
        fps_clock.tick(FPS)


# ===== CLASSES =====
class Atom:
    # An object that represents one atom

    # position and velocity are stored as 2x1 NumPy arrays, but the input can also be in the form of a tuple or a list
    # Atoms will only absorb a photon if the hue of the atom and the photon are within hue_range of each other
    # If doppler is set to True, the hue of the atom is corrected for the Doppler effect

    def __init__(self, position=np.array([0, 0]), velocity=np.array([0, 0]), hsv_color=(180, 100, 100), doppler=False,
                 hue_range=HUE_ABSORPTION_RANGE, image_path='images/Sphere.png', radius=ATOM_RADIUS):

        self.position = np.asarray(position)  # Convert input to an array
        self.velocity = np.asarray(velocity)  # Convert input to an array
        self.hsv_color = hsv_color
        self.rgb_color = hsv_to_rgb_norm(self.hsv_color)
        self.hue_bare = hsv_color[0]
        self.hue = self.hue_bare
        self.hue_range = hue_range
        self.doppler = doppler
        self.radius = radius
        self.image_path = image_path
        self.image = pygame.transform.scale(pygame.image.load(self.image_path), (2*self.radius, 2*self.radius))
        self.set_hue(self.hue_bare, self.doppler)

    def set_color(self, color, color_type='hsv'):
        if color_type.lower() == 'hsv':
            rgb_color = hsv_to_rgb_norm(color)
            hsv_color = color
        else:
            # We assume the color type is rgb
            rgb_color = color
            hsv_color = rgb_to_hsv_norm(color)

        self.hsv_color = hsv_color
        self.rgb_color = rgb_color
        color_image = pygame.Surface(self.image.get_size()).convert_alpha()
        color_image.fill(self.rgb_color)
        self.image = pygame.transform.scale(pygame.image.load(self.image_path), (2*self.radius, 2*self.radius))
        self.image.blit(color_image, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    def set_hue(self, hue, include_doppler=False):
        # We use this function to change the color of the atom, since we also have to change the variable self.hue
        # The Doppler effect can also be taken into account through this function
        if include_doppler:
            self.hue = hue - \
                       (1-np.sqrt((1-self.velocity[0]/SPEED_OF_LIGHT_DOPPLER) /
                                  (1+self.velocity[0]/SPEED_OF_LIGHT_DOPPLER))) * \
                       (FREQ_MIN/(FREQ_MAX-FREQ_MIN)*(HUE_MAX-HUE_MIN) + hue - HUE_MIN)
        else:
            self.hue = hue
        saturation = self.hsv_color[1]
        value = self.hsv_color[2]
        self.set_color((self.hue, saturation, value))

    def move(self):
        self.position += self.velocity

    def collide(self, photons):
        # Check for collisions with all photons, and absorb it if the collision goes through
        for photon in photons:
            relative_position = self.position - photon.position
            if relative_position @ relative_position < (self.radius + photon.hit_radius)**2\
                    and abs(self.hue - photon.hue) < self.hue_range:
                photons.remove(photon)
                self.velocity += ATOM_COLLISION_SPEED_GAIN*photon.velocity/np.linalg.norm(photon.velocity)
                self.set_hue(self.hue_bare, self.doppler)

    def draw(self, surface):
        # The atom is drawn with its xy-position in the center
        surface.blit(self.image, tuple(self.position - self.radius))


class Photon:
    # Represents a photon, which comes out of the laser and can collide with atoms

    def __init__(self, position=np.array([0., 0.]), velocity=np.array([0., 0.]), hsv_color=(180, 100, 100),
                 width=12, height=8):
        self.position = np.array(position)
        self.velocity = np.array(velocity)
        self.hsv_color = hsv_color
        self.width = width
        self.height = height
        self.hit_radius = min(self.width, self.height)/2  # We use a circular hitbox
        self.hue = hsv_color[0]

    def move(self):
        self.position += self.velocity

    def get_bounding_rectangle(self):
        return self.position[0] - self.width/2, self.position[1] - self.height/2, self.width, self.height

    def draw(self, surface):
        fill_color_hsv = self.hsv_color
        border_color_hsv = (self.hsv_color[0], self.hsv_color[1], self.hsv_color[2]/2)
        pygame.draw.ellipse(surface, hsv_to_rgb_norm(fill_color_hsv), self.get_bounding_rectangle())
        pygame.draw.ellipse(surface, hsv_to_rgb_norm(border_color_hsv), self.get_bounding_rectangle(), 1)


# ===== ATOM CONTROL FUNCTIONS =====
def create_random_atom(atoms, level=1, hsv_color=None):
    # Creates an atom on the left side of the screen, with a random y-coordinate and velocity
    # The type of atom depends on the current 'level':
    # - Level 1: Grey atoms that absorb any color of light
    # - Level 2: Randomly colored atoms that only absorb one color
    # - Level 3: Same-colored atoms with the Doppler effect implemented

    x = LEFT_BORDER - ATOM_RADIUS
    y = uniform(TOP_BORDER + ATOM_RADIUS, TOP_BORDER + PLAY_HEIGHT - ATOM_RADIUS)
    velocity = uniform(0.8, 1.2)
    if level == 1:
        hsv_color = (180, 0, 50)
        hue_range = 360
        with_doppler = False
    elif level == 2:
        hsv_color = (uniform(HUE_MIN, HUE_MAX), 100, 100)
        hue_range = HUE_ABSORPTION_RANGE
        with_doppler = False
    elif level == 3:
        if hsv_color is None:
            hsv_color = (110, 100, 100)
        hue_range = HUE_ABSORPTION_RANGE
        with_doppler = True
    else:
        # We shouldn't ever end up here
        hsv_color = (180, 0, 50)
        hue_range = 180
        with_doppler = False

    new_atom = Atom(np.array((x, y)), np.array((velocity, 0.)), hsv_color, with_doppler, hue_range)
    atoms.append(new_atom)


def run_atom_timer(atoms, atom_timer, level=1, hsv_color=None):
    # This function handles the delay between the atoms.
    # atom_timer is of the form (timer, max_time); an atom is created everytime timer reaches max_time,
    # then the timer is reset to 0
    # Every time an atom is created, the time between atoms is decreased
    timer = atom_timer[0]
    max_time = atom_timer[1]
    timer = (timer + 1) % max_time
    if timer == 0:
        create_random_atom(atoms, level, hsv_color)
        max_time = int(TIMES_BETWEEN_ATOMS_FINAL[level-1] + (max_time - TIMES_BETWEEN_ATOMS_FINAL[level-1])*0.85)
    return timer, max_time


def remove_outside_atoms(atoms):
    # This function removes any atom that goes outside the screen
    for atom in atoms:
        if not (LEFT_BORDER - ATOM_RADIUS - 1 < atom.position[0] < WINDOW_WIDTH - RIGHT_BORDER + ATOM_RADIUS + 1
                and TOP_BORDER - ATOM_RADIUS - 1 < atom.position[1] < WINDOW_HEIGHT - BOTTOM_BORDER + ATOM_RADIUS + 1):
            atoms.remove(atom)


# ===== COLOR FUNCTIONS =====


def rgb_to_hsv_norm(hsv_color):
    # This function transforms a (255, 255, 255) rgb color to a (360, 100, 100) hsv color
    norm_hsv_color = colorsys.rgb_to_hsv(hsv_color[0] / 255.0, hsv_color[1] / 255.0, hsv_color[2] / 255.0)
    return int(norm_hsv_color[0] * 360), int(norm_hsv_color[0] * 100), int(norm_hsv_color[0] * 100)


def hsv_to_rgb_norm(rgb_color):
    # This function transforms a (360, 100, 100) hsv color to a (255, 255, 255) rgb color
    norm_rgb_color = colorsys.hsv_to_rgb(rgb_color[0] / 360.0, rgb_color[1] / 100.0, rgb_color[2] / 100.0)
    return int(norm_rgb_color[0] * 255), int(norm_rgb_color[1] * 255), int(norm_rgb_color[2] * 255)


# ===== DRAW FUNCTIONS =====


def draw_borders(surface):
    # Draw the dark gray borders on the edges of the screen
    pygame.draw.rect(surface, DARK_GRAY, (0, 0, LEFT_BORDER, WINDOW_HEIGHT))
    pygame.draw.rect(surface, DARK_GRAY, (0, 0, WINDOW_WIDTH, TOP_BORDER))
    pygame.draw.rect(surface, DARK_GRAY, (WINDOW_WIDTH - RIGHT_BORDER, 0, RIGHT_BORDER, WINDOW_HEIGHT))
    pygame.draw.rect(surface, DARK_GRAY, (0, WINDOW_HEIGHT - BOTTOM_BORDER, WINDOW_WIDTH, BOTTOM_BORDER))
    pygame.draw.rect(surface, BLACK, (LEFT_BORDER, TOP_BORDER, PLAY_WIDTH, PLAY_HEIGHT), 1)


def draw_text(surface, atoms, title_font, score_font, level):
    # Draw all the necessary text on the screen

    # Title
    if level == 1:
        title_string = 'Laser cooling'
    elif level == 2:
        title_string = 'Laser cooling with different atoms'
    elif level == 3:
        title_string = 'Laser cooling with the Doppler effect'
    else:
        title_string = 'Laser cooling with a person who broke the applet'
    title_text = title_font.render(title_string, True, LIGHT_GRAY)
    title_text_size = title_font.size(title_string)
    title_text_xy = ((WINDOW_WIDTH - title_text_size[0]) / 2,
                     (TOP_BORDER - title_text_size[1]) / 2)
    surface.blit(title_text, title_text_xy)

    # Number of atoms
    score_string = 'Atoms: '+str(len(atoms))
    score_text = score_font.render(score_string, True, LIGHT_GRAY)
    score_text_xy = (LEFT_BORDER + 6, TOP_BORDER + PLAY_HEIGHT + 6)
    surface.blit(score_text, score_text_xy)


# ===== BUTTONS AND SLIDERS ===== #
class Button:  # Bare-bones button, we are likely not going to make any of these

    def __init__(self, surface, bounding_rectangle):
        self.surface = surface
        self.bounding_rectangle = bounding_rectangle
        self.x = bounding_rectangle[0]
        self.y = bounding_rectangle[1]
        self.width = bounding_rectangle[2]
        self.height = bounding_rectangle[3]

    def action(self):  # This function is what happens when the button is clicked
        return True

    def idle(self):  # This function is what happens while the button is not clicked
        return False

    def is_active(self, mouse_state):
        # A function that determines whether the effect of the button should activate
        # mouse_state is a tuple of the form (mouse_xy, mouse_is_clicked, mouse_is_down)
        # Current implementation: Activates only on the exact frame the button is clicked
        if self.check_mouse(mouse_state[0]) and mouse_state[1]:
            return True
        else:
            return False

    def check_mouse(self, mouse_xy):
        # Checks if the mouse is inside the button
        # Current implementation: Rectangular hitbox
        mouse_x = mouse_xy[0]
        mouse_y = mouse_xy[1]
        if self.x <= mouse_x <= self.x + self.width and self.y <= mouse_y <= self.y + self.height:
            mouse_inside = True
        else:
            mouse_inside = False
        return mouse_inside

    def draw(self, mouse_state):
        pygame.draw.rect(self.surface, BLACK, self.bounding_rectangle)

    def control(self, mouse_state):
        # This function can be called in the main game loop to handle the entire button
        self.draw(mouse_state)
        if self.is_active(mouse_state):
            return self.action()
        else:
            return self.idle()


class ImageButton(Button):
    # This is a button with an image. There are three images: one for the idle state, one when the mouse hovers over,
    # and one when the button is clicked.
    # Action inputs: None
    # Action outputs: is_pressed

    def __init__(self, surface, bounding_rectangle, idle_image_path, hover_image_path=None, down_image_path=None):
        if hover_image_path is None:
            hover_image_path = idle_image_path
        if down_image_path is None:
            down_image_path = hover_image_path
        super().__init__(surface, bounding_rectangle)
        self.idle_image_path = idle_image_path
        self.hover_image_path = hover_image_path
        self.down_image_path = down_image_path
        self.idle_image = pygame.transform.scale(pygame.image.load(idle_image_path), (self.width, self.height))
        self.hover_image = pygame.transform.scale(pygame.image.load(hover_image_path), (self.width, self.height))
        self.down_image = pygame.transform.scale(pygame.image.load(down_image_path), (self.width, self.height))

    def draw(self, mouse_state):
        mouse_xy = mouse_state[0]
        mouse_is_clicked = mouse_state[1]
        if self.check_mouse(mouse_xy):
            if mouse_is_clicked:
                image = self.down_image
            else:
                image = self.hover_image
        else:
            image = self.idle_image

        self.surface.blit(image, (self.x, self.y))


class Slider:  # A slider bar

    def __init__(self, surface, bounding_rectangle, slider_direction='horizontal', minmax=(0., 1.), starting_value=None,
                 slider_size=(16, 16), text_string='', text_font=None, text_color=(0, 0, 0)):
        self.surface = surface
        self.bounding_rectangle = bounding_rectangle
        self.x = bounding_rectangle[0]
        self.y = bounding_rectangle[1]
        self.width = bounding_rectangle[2]
        self.height = bounding_rectangle[3]
        self.minmax = minmax
        self.min_value = minmax[0]
        self.max_value = minmax[1]
        if starting_value is None:
            self.activation = 0.5
        else:
            self.activation = min(max((starting_value - self.min_value)/(self.max_value - self.min_value), 0), 1)
        self.slider_half_width = slider_size[0]/2
        self.slider_half_height = slider_size[1]/2
        self.direction = slider_direction.lower()
        if self.direction not in ['horizontal', 'vertical']:
            self.direction = 'horizontal'  # We default to a horizontal slider in case of an unknown direction
        self.sliding = False
        self.text_string = text_string
        if text_font is None:
            self.text_font = pygame.font.SysFont('arial', 11)
        else:
            self.text_font = text_font
        self.text_color = text_color

    def get_slider_activation(self, slider_xy):
        if self.direction == 'vertical':
            return 1-min(max((slider_xy[1] - self.y)/self.height, 0), 1)
        else:
            return min(max((slider_xy[0] - self.x) / self.width, 0), 1)

    def get_slider_xy(self, activation=None):
        if activation is None:
            activation = self.activation
        if self.direction == 'vertical':
            return self.x + 0.5*self.width, self.y + (1-activation)*self.height
        else:
            return self.x + activation*self.width, self.y + 0.5*self.height

    def get_slider_value(self, activation=None):
        if activation is None:
            activation = self.activation
        return (1-activation)*self.min_value + activation*self.max_value

    def set_slider_value(self, value):
        self.activation = min(max((value - self.min_value)/(self.max_value - self.min_value), 0), 1)
        return self.get_slider_value()

    def check_mouse(self, mouse_xy):
        # Checks if the mouse is on the slider
        # The hitbox is a rectangle, as wide as the slider bar and as high as the slider button
        # (or reversed if the direction is vertical)
        mouse_x = mouse_xy[0]
        mouse_y = mouse_xy[1]
        if (0 <= mouse_x - self.x <= self.width and 0 <= mouse_y - self.y <= 2*self.slider_half_height) \
                or (self.direction == 'vertical' and 0 <= mouse_x - self.x <= 2*self.slider_half_width and
                    0 <= mouse_y - self.y <= self.height):
            mouse_inside = True
        else:
            mouse_inside = False
        return mouse_inside

    def is_sliding(self, mouse_state):
        # A function that determines whether the slider is sliding or not
        # mouse_state is a tuple of the form (mouse_xy, mouse_is_clicked, mouse_is_down)
        if mouse_state[2]:
            if mouse_state[1] and self.check_mouse(mouse_state[0]):
                self.sliding = True
        else:
            self.sliding = False
        return self.sliding

    def draw(self):
        pygame.draw.rect(self.surface, WHITE, self.bounding_rectangle)
        pygame.draw.rect(self.surface, BLACK, self.bounding_rectangle, 1)
        if self.slider_half_width == self.slider_half_height:
            pygame.draw.circle(self.surface, GRAY, self.get_slider_xy(), self.slider_half_width)
            pygame.draw.circle(self.surface, BLACK, self.get_slider_xy(), self.slider_half_height, 1)
        else:
            x, y = self.get_slider_xy()
            slider_rect = (x - self.slider_half_width, y - self.slider_half_height,
                           2*self.slider_half_width, 2*self.slider_half_height)
            pygame.draw.rect(self.surface, GRAY, slider_rect)
            pygame.draw.rect(self.surface, BLACK, slider_rect, 1)

        # Draw the text
        text_surf = self.text_font.render(self.text_string, True, self.text_color)
        text_size = self.text_font.size(self.text_string)
        text_xy = (self.x + (self.width - text_size[0]) / 2,
                   self.y + self.height/2 + self.slider_half_height)
        self.surface.blit(text_surf, text_xy)

    def control(self, mouse_state):
        # This function can be called in the main game loop to handle the entire slider
        # mouse_state is a tuple of the form (mouse_xy, mouse_is_down)
        mouse_xy = mouse_state[0]
        self.draw()
        if self.is_sliding(mouse_state):
            self.activation = self.get_slider_activation(mouse_xy)
        return self.get_slider_value()


class HueSlider(Slider):  # Exactly the same slider bar, but the background is colored

    def __init__(self, *args):
        super().__init__(*args)
        min_hue = max(int(self.min_value), 0)
        max_hue = min(int(self.max_value), 360)
        rainbow_surface = pygame.Surface((max_hue-min_hue, self.height))
        for hue in range(min_hue, max_hue + 1):
            pygame.draw.line(rainbow_surface, hsv_to_rgb_norm((hue, 75, 75)),
                             (hue-min_hue, 0), (hue-min_hue, self.height))
        self.rainbow_surface = pygame.transform.scale(rainbow_surface, (self.width, self.height))

    def draw(self):
        self.surface.blit(self.rainbow_surface, (self.x, self.y))
        pygame.draw.rect(self.surface, BLACK, self.bounding_rectangle, 1)
        if self.slider_half_width == self.slider_half_height:
            pygame.draw.circle(self.surface, GRAY, self.get_slider_xy(), self.slider_half_width)
            pygame.draw.circle(self.surface, BLACK, self.get_slider_xy(), self.slider_half_height, 1)
        else:
            x, y = self.get_slider_xy()
            slider_rect = (x - self.slider_half_width, y - self.slider_half_height,
                           2 * self.slider_half_width, 2 * self.slider_half_height)
            pygame.draw.rect(self.surface, GRAY, slider_rect)
            pygame.draw.rect(self.surface, BLACK, slider_rect, 1)

        # Draw the text
        text_surf = self.text_font.render(self.text_string, True, self.text_color)
        text_size = self.text_font.size(self.text_string)
        text_xy = (self.x + (self.width - text_size[0]) / 2,
                   self.y + self.height / 2 + self.slider_half_height)
        self.surface.blit(text_surf, text_xy)


class Laser(Slider):  # The laser is technically a slider

    def __init__(self, surface, bounding_rectangle, firing_delay=30, image_path='images/Laser.png'):
        x, y, width, height = bounding_rectangle
        temp_image = pygame.image.load(image_path)
        image_width = width
        image_height = int(temp_image.get_height()*image_width/temp_image.get_width())  # Uniformly scale image
        self.image = pygame.transform.scale(temp_image, (image_width, image_height))
        new_bounding_rectangle = (x, y + image_height/2, width, height - image_height)  # Cut off top and bottom
        super().__init__(surface, new_bounding_rectangle, 'vertical', (0., 1.), None, (image_width, image_height))
        self.firing_delay = int(firing_delay)
        self.timer = 0

    def set_fire_rate(self, fire_rate):
        self.firing_delay = int(FPS/fire_rate)

    def draw(self):
        self.surface.blit(self.image, (self.get_slider_xy()[0] - self.slider_half_width,
                                       self.get_slider_xy()[1] - self.slider_half_height))

    def control_shoot(self, mouse_state, photon_hue, photons):
        self.timer = (self.timer + 1) % self.firing_delay
        if self.timer == 0:
            photon_xy = (self.get_slider_xy()[0] - self.slider_half_width, self.get_slider_xy()[1])
            new_photon = Photon(np.array(photon_xy), np.array((-SPEED_OF_LIGHT, 0)), (photon_hue, 100, 100))
            photons.append(new_photon)
        super().control(mouse_state)


if __name__ == '__main__':
    main()
