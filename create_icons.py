import os
from PIL import Image, ImageDraw, ImageFont

icons = {
    "Emergency": "🚨",
    "Pain": "🤕",
    "Airway Obstruction": "😮‍💨",
    "Suction": "🩺",
    "Care": "💖",
    "Water": "💧",
    "Food": "🍲",
    "Dizziness": "😵",
    "Can't Sleep": "🛌",
    "Change Position": "🔀",
    "Right": "➡",
    "Left": "⬅",
    "Back": "⬇"
}

os.makedirs("icons", exist_ok=True)

# we try to use Windows emoji font
font_path = "C:\\Windows\\Fonts\\seguiemj.ttf"
try:
    font = ImageFont.truetype(font_path, 100)
except Exception as e:
    print("Could not load emoji font:", e)
    font = ImageFont.load_default()

for name, emoji_char in icons.items():
    safe_name = name.replace("'", "").replace(" ", "_").lower()
    path = os.path.join("icons", f"{safe_name}.png")
    
    # Create an image with transparent background
    img = Image.new("RGBA", (150, 150), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        # Get exact bounding box
        bbox = font.getbbox(emoji_char)
        # some emojis might have no bbox or offset
        if bbox is None:
            bbox = (0, 0, 100, 100)
        
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (150 - tw) // 2
        y = (150 - th) // 2 - bbox[1]
        
        draw.text((x, y), emoji_char, font=font, embedded_color=True, fill=(0,0,0,255))
    except Exception as e:
        print(f"Error drawing {name}: {e}")
        
    img.save(path)
    print(f"Created {path}")

print("Done.")
