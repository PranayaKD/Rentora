import os
import glob
from PIL import Image, ImageDraw
import numpy as np

def clean_car_images():
    cars_dir = os.path.join(os.path.dirname(__file__), '..', 'media', 'cars')
    cars_dir = os.path.abspath(cars_dir)
    pattern = os.path.join(cars_dir, '*.webp')
    files = glob.glob(pattern)
    print(f"Found {len(files)} webp files in {cars_dir}")
    
    modified = 0
    for f in files:
        if 'test_' in os.path.basename(f):
            continue
        try:
            im = Image.open(f).convert('RGBA')
            arr = np.array(im)
            corners = [arr[0, 0], arr[0, -1], arr[-1, 0], arr[-1, -1]]
            
            # Check if any corner is transparent already
            if any(c[3] < 50 for c in corners):
                continue
                
            w, h = im.width, im.height
            # Check if white background
            is_white = all(c[3] > 200 and c[0] > 230 and c[1] > 230 and c[2] > 230 for c in corners)
            # Check if black background
            is_black = any(c[3] > 200 and c[0] < 30 and c[1] < 30 and c[2] < 30 for c in corners)
            
            if not (is_white or is_black):
                continue
                
            thresh = 35 if is_white else 25
            
            # Floodfill from all 4 corners and midpoints of edges
            seeds = [
                (0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
                (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)
            ]
            for sx, sy in seeds:
                try:
                    ImageDraw.floodfill(im, (sx, sy), (0, 0, 0, 0), thresh=thresh)
                except Exception:
                    pass
            
            im.save(f, 'WEBP')
            modified += 1
            print(f"Cleaned background: {os.path.basename(f)}")
        except Exception as e:
            print(f"Error processing {f}: {e}")
            
    print(f"Total car images cleaned: {modified}")

if __name__ == '__main__':
    clean_car_images()

