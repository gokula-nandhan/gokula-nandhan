import sys
import os
from PIL import Image, ImageOps

def trim_blank_lines(ascii_str):
    lines = ascii_str.split("\n")
    first_non_blank = 0
    for i, line in enumerate(lines):
        if line.strip():
            first_non_blank = i
            break
            
    last_non_blank = len(lines) - 1
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip():
            last_non_blank = i
            break
            
    return "\n".join(lines[first_non_blank:last_non_blank+1])

def image_to_ascii(image_path, output_path, width=36, invert=True, contrast_factor=1.3, brightness_factor=1.0):
    try:
        img = Image.open(image_path)
    except Exception as e:
        print(f"Error opening image: {e}")
        return False
    
    # Convert to grayscale
    img = img.convert("L")
    
    # Apply brightness and contrast enhancement
    if brightness_factor != 1.0:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(brightness_factor)
    if contrast_factor != 1.0:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast_factor)
    
    # Calculate height based on target width and aspect ratio (monospace aspect ratio compensation)
    aspect_ratio = img.height / img.width
    height = int(width * aspect_ratio * 0.55)
    
    # Resize image
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    
    # Character ramp (density based from dark to bright)
    chars = " .,:;i1tfLCG08@"
    if invert:
        chars = chars[::-1]
        
    num_chars = len(chars)
    
    ascii_str = ""
    for y in range(img.height):
        for x in range(img.width):
            pixel_val = img.getpixel((x, y))
            char_idx = int((pixel_val / 255.0) * (num_chars - 1))
            ascii_str += chars[char_idx]
        ascii_str += "\n"
        
    # Trim top and bottom blank lines
    ascii_str = trim_blank_lines(ascii_str)
        
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ascii_str + "\n")
        
    print(f"Success: ASCII art saved to {output_path} ({width}x{height} raw, trimmed)")
    return True

if __name__ == "__main__":
    from PIL import ImageEnhance
    # Default parameters
    image_file = "images/avatar.png"
    output_file = "portrait.txt"
    width = 36
    invert = True
    
    # Simple argument parsing
    if len(sys.argv) > 1:
        image_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    if len(sys.argv) > 3:
        width = int(sys.argv[3])
    if len(sys.argv) > 4:
        invert = sys.argv[4].lower() == "true"
        
    image_to_ascii(image_file, output_file, width, invert)
