from PIL import Image, ImageDraw

# Create a new RGBA image (with transparency)
width = 300
height = 200
img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw a semi-transparent rectangle
rectangle_color = (255, 255, 255, 128)  # White with 50% transparency
draw.rectangle([0, 0, width, height], fill=rectangle_color)

# Save the image
img.save('Rectangle 7.png', 'PNG')
