from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    # Create a 256x256 image with transparent background
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    
    # Draw a blue circle
    d.ellipse([(10, 10), (size-10, size-10)], fill=(0, 120, 215, 255))
    
    # Add text (CA for Clarikey Analytics)
    try:
        # Try to use a nice font if available
        font = ImageFont.truetype("arial.ttf", 120)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Center the text
    text = "CA"
    text_bbox = d.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    position = ((size - text_width) // 2, (size - text_height) // 2 - 20)
    
    # Draw white text
    d.text(position, text, fill=(255, 255, 255, 255), font=font)
    
    # Save as ICO
    assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    icon_path = os.path.join(assets_dir, 'icon.ico')
    
    # Save in multiple sizes for better quality
    img.save(icon_path, format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
    print(f"✅ Icon created at: {icon_path}")
    return icon_path

if __name__ == "__main__":
    create_icon()
