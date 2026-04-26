import argparse
import os
import subprocess
import sys
from time import sleep

import markdown
import pygame  # Import pygame
from faster_whisper import WhisperModel
from PIL import Image, ImageDraw, ImageFont, ImageText

from WhisPlay import WhisPlayBoard

board = WhisPlayBoard()
board.set_backlight(50)

global_image_data = None
image_filepath = None

# Initialize pygame mixer
pygame.mixer.init()
sound = None  # Global sound variable
playing = False  # Global variable to track if sound is playing
recording = False
poll = None

# Initializing Speech to Text
model_size = "tiny.en"
model = WhisperModel(model_size, device="cpu", compute_type="int8")


def set_wm8960_volume_stable(volume_level: str):
    """
    Sets the 'Speaker' volume for the wm8960 sound card using the amixer command.

    Args:
        volume_level (str): The desired volume value, e.g., '90%' or '121'.
    """

    CARD_NAME = "wm8960soundcard"
    CONTROL_NAME = "Speaker"
    DEVICE_ARG = f"hw:{CARD_NAME}"

    command = ["amixer", "-D", DEVICE_ARG, "sset", CONTROL_NAME, volume_level]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)

        print(
            f"INFO: Successfully set '{CONTROL_NAME}' volume to {volume_level} on card '{CARD_NAME}'."
        )

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to execute amixer.", file=sys.stderr)
        print(f"Command: {' '.join(command)}", file=sys.stderr)
        print(f"Return Code: {e.returncode}", file=sys.stderr)
        print(f"Error Output:\n{e.stderr}", file=sys.stderr)
    except FileNotFoundError:
        print(
            "ERROR: 'amixer' command not found. Ensure it is installed and in PATH.",
            file=sys.stderr,
        )


def load_jpg_as_rgb565(img, screen_width, screen_height):
    # img = Image.open(filepath).convert('RGB')
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
            (offset_x, 0, offset_x + screen_width, screen_height)
        )
    else:
        # Original image is taller or has the same aspect ratio, scale based on screen width
        new_width = screen_width
        new_height = int(new_width / aspect_ratio)
        resized_img = img.resize((new_width, new_height))
        # Calculate vertical offset to center the image
        offset_y = (new_height - screen_height) // 2
        # Crop the image to fit screen height
        cropped_img = resized_img.crop(
            (0, offset_y, screen_width, offset_y + screen_height)
        )

    pixel_data = []
    for y in range(screen_height):
        for x in range(screen_width):
            r, g, b = cropped_img.getpixel((x, y))
            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            pixel_data.extend([(rgb565 >> 8) & 0xFF, rgb565 & 0xFF])

    return pixel_data


def textDraw(string):

    font = ImageFont.truetype("Tests/fonts/FreeMono.ttf", 24)

    text = ImageText.Text(string, font)

    # create an image
    im = Image.new("RGB", (board.LCD_WIDTH, board.LCD_HEIGHT), "black")

    # get a drawing context
    d = ImageDraw.Draw(im)

    # draw multiline text
    d.text((10, 10), text, fill="white")

    td = load_jpg_as_rgb565(im, board.LCD_WIDTH, board.LCD_HEIGHT)

    board.draw_image(0, 0, board.LCD_WIDTH, board.LCD_HEIGHT, td)


def speech2text():
    fulltext = ""
    segments, info = model.transcribe("main.mp3", beam_size=5)

    print(
        "Detected language '%s' with probability %f"
        % (info.language, info.language_probability)
    )
    segments = list(segments)  # The transcription will actually run here.

    for segment in segments:
        print("%s", segment.text)
        fulltext += segment.text

    html = markdown.markdown(fulltext)

    with open(
        "Speech.html", "w", encoding="utf-8", errors="xmlcharrefreplace"
    ) as output_file:
        output_file.write(html)


# Button callback function
def on_button_pressed():
    print("Button pressed!")
    print("Recording for 15 seconds")
    global recording, p
    recording = True
    p = subprocess.Popen(["arecord", "-d", "15", "main.mp3"], shell=False)

# Register button event
board.on_button_press(on_button_pressed)

try:
    print("Waiting for button press (Press Ctrl+C to exit)...")
    while True:
        if recording is True and poll is None:
            textDraw("Recording ...")
            poll = p.poll()
            if poll is not None:
                speech2text()
        else:
            recording = False
            board.fill_screen(0x00)
        sleep(0.1)

except KeyboardInterrupt:
    print("Exiting program...")

finally:
    board.cleanup()
    pygame.mixer.quit()  # Quit the mixer
