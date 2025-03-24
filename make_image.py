import os, math, colorsys
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont
font_file = "CommunardRegular.otf"

from archive_congfig3 import text_bits, default_frame_duration, color_increments, path, use_background, diagonal_text
# Crop image to a centered square.

def draw_diagonal_text(image, text, font_path, font_size, fill, bg_fill, angle):
    # Ensure image supports transparency
    if image.mode != 'RGBA':
        image = image.convert('RGBA')

    # Load your custom font
    font = ImageFont.truetype(font_path, font_size)

    # Create a dummy drawing context to compute text size
    dummy_draw = ImageDraw.Draw(image)
    bbox = dummy_draw.textbbox((0, 0), text, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    # Add padding for background
    padding = 20
    bg_width = text_width + 2 * padding
    bg_height = text_height + 2 * padding
    # Create a transparent image for text
    text_img = Image.new('RGBA', (text_width, text_height), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_img)
    text_draw.rectangle((0, 0, bg_width, bg_height), fill=bg_fill)

    text_draw.text((0, 0), text, font=font, fill=fill)
    # add a background


    # Rotate text
    rotated_text = text_img.rotate(angle, expand=1)
    rotated_text.save("debug_rotated.png")

    rotated_width, rotated_height = rotated_text.size
    image_width, image_height = image.size

    # Auto-centered position
    position = ((image_width - rotated_width) // 2, (image_height - rotated_height) // 2)

    image.alpha_composite(rotated_text, position)

    # Adjust position to ensure text placement is visible
    paste_x, paste_y = position

    # Paste with correct transparency mask
    image.alpha_composite(rotated_text, (paste_x, paste_y))
    image.alpha_composite(rotated_text, (paste_x, paste_y - image_height // 2))
    image.alpha_composite(rotated_text, (paste_x, paste_y + image_height // 2))

    # Save debug image
    image.save("debug.png")
    return image




def square_crop(im):
    w, h = im.size
    min_dim = min(w, h)
    left = (w - min_dim) // 2
    top = (h - min_dim) // 2
    return im.crop((left, top, left + min_dim, top + min_dim))


def get_rainbow_color(i, total):
    # t should be in [0, 1]
    t = i / total
    r, g, b = colorsys.hsv_to_rgb(t, 1, 1)
    return (int(r * 255), int(g * 255), int(b * 255))


def draw_text_at_height_and_size(draw, text, location, target_size, font_size, color, text_color, scroll_offset=0):
    font = ImageFont.truetype(font_file, font_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    padding = 10
    rect_w, rect_h = text_w + 2 * padding, text_h + 2 * padding
    # Position rectangle at location
    rect_x, rect_y = (target_size[0] - rect_w) * location[0], (target_size[1] - rect_h) * location[1]
    rect_x += 2 * scroll_offset
    # if the text is FULLY off the screen, mod the rect_x by the width of the screen
    if rect_x < -rect_w:
        rect_x += target_size[0] + rect_w
    if use_background:
        draw.rectangle([rect_x, rect_y, rect_x + rect_w, rect_y + rect_h], fill=color)
    draw.text((rect_x + padding, rect_y + padding), text, fill=text_color, font=font)


def grab_image(path, color_idx, total, target_size=(500, 500)):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        pages = convert_from_path(path, first_page=1, last_page=1)
        if pages: im = pages[0]
        else: return None
    else:
        im = Image.open(path)
        if im.mode != "RGB":
            im = im.convert("RGB")
    im = square_crop(im).resize(target_size)
    if diagonal_text:
        color = get_rainbow_color(color_idx, total)
        bg_color = (255 - color[0], 255 - color[1], 255 - color[2])
        im = draw_diagonal_text(im, diagonal_text, font_file, 20, color, bg_color, 45)
    return im

# Process one file: open, crop, resize, and overlay text.
def process_file(im, index, total, target_size=(500, 500)):

    draw = ImageDraw.Draw(im)
    # increase font size

    # draw_text_at_height_and_size(draw, above_text, .3, target_size, 25, color, text_color)
    # draw_text_at_height_and_size(draw, below_text, .6, target_size, 35, text_color, color)
    for text in text_bits.values():

        time_in_loop = index / total
        display = False
        time_chunks = []
        scroll_offset = 0
        x_location, y_location = text["location"]


        if text["when"] + text["duration"] <= 1:
            time_chunks.append((text["when"], text["when"] + text["duration"]))
        else:
            time_chunks.append((text["when"], 1))
            time_chunks.append((0, text["when"] + text["duration"] - 1))
        for chunk in time_chunks:
            if time_in_loop >= chunk[0] and time_in_loop <= chunk[1]:
                display = True
                time_in = time_in_loop / text["duration"]
                color = get_rainbow_color((time_in + text.get("color_offset", 0)) * total, total)
                text_color = (255 - color[0], 255 - color[1], 255 - color[2])
        if text.get("scroll", False):
            scroll_offset = -2 * target_size[0] * time_in_loop
        if display:
            draw_text_at_height_and_size(draw, text['text'], (x_location, y_location), target_size, text["font_size"], color, text_color, scroll_offset)

    return im

# Recursively gather supported image files.
def gather_images(root_dir):
    paths = []
    for subdir, _, files in os.walk(root_dir):
        for f in files:
            if f.lower().endswith((".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".tif")):
                paths.append(os.path.join(subdir, f))
            else:
                print(f"Skipping {f}")
    return paths

# Main processing and GIF creation.
def create_slideshow(root_dir, output_gif, frame_duration=default_frame_duration):
    file_paths = gather_images(root_dir)
    total = len(file_paths)
    frames = []
    for idx, path in enumerate(file_paths):
        try:
            for incr in range(color_increments):
                base_image = grab_image(path, idx * color_increments + incr, total * color_increments)
                if not base_image: continue
                im = process_file(base_image, idx * color_increments + incr, total * color_increments)
                if im:
                    frames.append(im)
        except Exception as e:
            print(f"Error processing {path}: {e}")
    if frames:
        frames[0].save(output_gif, save_all=True, append_images=frames[1:], duration=frame_duration, loop=0)
        print(f"GIF saved as {output_gif}")
    else:
        print("No images processed.")

if __name__ == "__main__":
    # Replace with your folder path
    create_slideshow(path, "output.gif")
