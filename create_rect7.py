from PIL import Image, ImageDraw

# Create a new RGBA image with transparency
width = 300  # 30% of template width (1000px)
height = 240  # 20% of template height (1200px)
img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw a semi-transparent white rectangle with increased opacity
rectangle_color = (255, 255, 255, 128)  # White with 50% opacity (increased from 25%)
draw.rectangle([0, 0, width, height], fill=rectangle_color)

# Save the image
img.save('Rectangle 7.png', 'PNG')
