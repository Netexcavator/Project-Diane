from time import sleep
from PIL import Image, ImageDraw, ImageText, ImageFont
import sys
import os
import argparse
import pygame  # Import pygame
import subprocess

from WhisPlay import WhisPlayBoard
board = WhisPlayBoard()
board.set_backlight(50)

# Initialize pygame mixer
pygame.mixer.init()
sound = None  # Global sound variable
playing = False  # Global variable to track if sound is playing

times_pressed = 0


def set_wm8960_volume_stable(volume_level: str):
    """
    Sets the 'Speaker' volume for the wm8960 sound card using the amixer command.

    Args:
        volume_level (str): The desired volume value, e.g., '90%' or '121'.
    """

    CARD_NAME = 'wm8960soundcard'
    CONTROL_NAME = 'Speaker'
    DEVICE_ARG = f'hw:{CARD_NAME}'

    command = [
        'amixer',
        '-D', DEVICE_ARG,
        'sset',
        CONTROL_NAME,
        volume_level
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)

        print(
            f"INFO: Successfully set '{CONTROL_NAME}' volume to {volume_level} on card '{CARD_NAME}'.")

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to execute amixer.", file=sys.stderr)
        print(f"Command: {' '.join(command)}", file=sys.stderr)
        print(f"Return Code: {e.returncode}", file=sys.stderr)
        print(f"Error Output:\n{e.stderr}", file=sys.stderr)
    except FileNotFoundError:
        print("ERROR: 'amixer' command not found. Ensure it is installed and in PATH.", file=sys.stderr)

def load_jpg_as_rgb565(filepath, screen_width, screen_height):
    img = filepath.convert('RGB')
    original_width, original_height = img.size

    aspect_ratio = original_width / original_height
    screen_aspect_ratio = screen_width / screen_height

    if aspect_ratio > screen_aspect_ratio:
        # Original image is wider, scale based on screen height
        new_height = screen_height
        new_width = int(new_height * aspect_ratio)
        resized_img = img.resize((new_width, new_height))
        # Calculate horizontal offset to center the image
        offset_x = (new_width - screen_width) // 2
        # Crop the image to fit screen width
        cropped_img = resized_img.crop(
            (offset_x, 0, offset_x + screen_width, screen_height))
    else:
        # Original image is taller or has the same aspect ratio, scale based on screen width
        new_width = screen_width
        new_height = int(new_width / aspect_ratio)
        resized_img = img.resize((new_width, new_height))
        # Calculate vertical offset to center the image
        offset_y = (new_height - screen_height) // 2
        # Crop the image to fit screen height
        cropped_img = resized_img.crop(
            (0, offset_y, screen_width, offset_y + screen_height))

    pixel_data = []
    for y in range(screen_height):
        for x in range(screen_width):
            r, g, b = cropped_img.getpixel((x, y))
            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            pixel_data.extend([(rgb565 >> 8) & 0xFF, rgb565 & 0xFF])

    return pixel_data

def textdraw(string):

    font = ImageFont.truetype("Tests/fonts/FreeMono.ttf", 24)

    text = ImageText.Text(string, font)

    # create an image
    im = Image.new("RGB", (board.LCD_WIDTH, board.LCD_HEIGHT), (0, 0, 0))

    # get a drawing context
    d = ImageDraw.Draw(im)

    # draw multiline text
    d.text((10,10), text, fill=(255, 255, 255))
    
    td = load_jpg_as_rgb565(im, board.LCD_WIDTH, board.LCD_HEIGHT)
    
    board.draw_image(0, 0, board.LCD_WIDTH, board.LCD_HEIGHT,td)

def statusbar(current, minimum, maximum):
    im = Image.new("RGB", (board.LCD_WIDTH, board.LCD_HEIGHT), (0, 0, 0))

    # get a drawing context
    d = ImageDraw.Draw(im)

    # Outside Rectangle
    d.rectangle(([0,110],[240,130]))

    # Linear Interpolation
    progress = ((current) * (235) // (maximum - minimum))

    # Internal Rectangle
    if progress > 0:
        d.rectangle(([5,115],[progress,125]),128)


    td = load_jpg_as_rgb565(im, board.LCD_WIDTH, board.LCD_HEIGHT)
    
    board.draw_image(0, 0, board.LCD_WIDTH, board.LCD_HEIGHT,td)


def on_button_pressed():
    print("Button pressed!")

    global times_pressed

    times_pressed = times_pressed + 1
    statusbar(times_pressed, 0, 10)

# Register button event
board.on_button_press(on_button_pressed)

# --- Initial Image Loading ---
# Load the image once at the beginning of the script
try:
    #textdraw("Hello World")
    statusbar(0, 0, 10)
except Exception as e:
    print("Failed")


try:
    print("Waiting for button press (Press Ctrl+C to exit)...")
    while True:
        # Check if the sound has finished playing and update the 'playing' flag
        if playing and not pygame.mixer.get_busy():
            playing = False
            # print("Sound finished playing.") # Optional print
        sleep(0.1)

except KeyboardInterrupt:
    print("Exiting program...")

finally:
    board.cleanup()
    pygame.mixer.quit()  # Quit the mixer