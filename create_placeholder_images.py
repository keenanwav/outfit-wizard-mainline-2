import os
from PIL import Image

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def create_colored_image(color, size, path):
    img = Image.new('RGB', size, color)
    img.save(path)

# Create directories
create_directory('images/shirts')
create_directory('images/pants')
create_directory('images/shoes')

# Create placeholder images
image_data = [
    ((255, 0, 0), 'images/shirts/red_casual_shirt.png'),
    ((0, 0, 255), 'images/pants/blue_casual_pants.png'),
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
