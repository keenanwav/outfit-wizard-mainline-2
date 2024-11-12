import os
from PIL import Image, ImageDraw

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def create_colored_image(color, size, path):
    img = Image.new('RGB', size, color)
    img.save(path)

def create_white_pants_with_pattern():
    # Create a white pants image with a pattern to test secondary color detection
    img = Image.new('RGB', (200, 200), (245, 245, 245))  # Slight off-white base
    draw = ImageDraw.Draw(img)
    
    # Add a subtle pattern in a different color
    secondary_color = (220, 220, 230)  # Very light blue-gray
    for y in range(0, 200, 10):
        draw.line([(50, y), (150, y)], fill=secondary_color, width=2)
    
    return img

# Create directories
create_directory('images/shirts')
create_directory('images/pants')
create_directory('images/shoes')

# Create white pants with pattern
white_pants = create_white_pants_with_pattern()
white_pants.save('images/pants/white_casual_pants.png')

# Create other placeholder images
image_data = [
    ((255, 0, 0), 'images/shirts/red_casual_shirt.png'),
    ((0, 0, 0), 'images/shoes/black_casual_shoes.png'),
    ((0, 255, 0), 'images/shirts/green_formal_shirt.png'),
    ((100, 100, 100), 'images/pants/gray_formal_pants.png'),
    ((139, 69, 19), 'images/shoes/brown_formal_shoes.png'),
    ((255, 192, 203), 'images/shirts/pink_casual_shirt.png'),
    ((0, 0, 0), 'images/pants/black_casual_pants.png'),
    ((255, 255, 255), 'images/shoes/white_casual_shoes.png'),
]

for color, path in image_data:
    create_colored_image(color, (200, 200), path)

print("Placeholder images created successfully.")
