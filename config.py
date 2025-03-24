# maps text to a location, size, and where in the cycle it should show up
text_bits = {
    'chunk1': {
            'text': 'Your Text Here',
            'location': (.5, .25),
            'font_size': 50,
            "when": 0,
            "duration": 1,
        },
    "chunk2": {
            'text': "your text here",
            'location': (.5, .5),
            'font_size': 12,
            "when": 0,
            "color_offset": .2,
            "duration": 1,
            "background": False
        }
}


diagonal_text = False
total_length_per_image = 750
color_increments = 6
default_frame_duration =  total_length_per_image // color_increments
path = "Image path here"
use_background = True
font_file = "CommunardRegular.otf"