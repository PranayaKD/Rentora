"""
Rentora - Car Images Resolution & Clarity Enhancer
Upscales all low-resolution vehicle assets in media/cars to 3x high-DPI (Retina-ready 900px+),
applies edge-preserving unsharp masking to eliminate blur, and whitens noisy JPEG compression
artifacts in the background for a seamless studio finish.
"""
import os
import sys
from PIL import Image, ImageFilter
import numpy as np

def enhance_car_images(cars_dir):
    if not os.path.isdir(cars_dir):
        print(f"Directory not found: {cars_dir}")
        return

    processed = 0
    skipped = 0

    valid_extensions = ('.webp', '.jpg', '.jpeg', '.png')
    files = [f for f in os.listdir(cars_dir) if f.lower().endswith(valid_extensions)]

    print(f"Scanning {len(files)} vehicle assets in {cars_dir}...")

    for fname in files:
        if fname.startswith('test_'):
            continue

        filepath = os.path.join(cars_dir, fname)
        try:
            with Image.open(filepath) as img:
                w, h = img.size
                if w >= 800:
                    # Already high resolution
                    skipped += 1
                    continue

                # Calculate 3x upscale target
                target_w = w * 3
                target_h = h * 3

                # Convert to RGB
                rgb_img = img.convert('RGB')
                
                # 1. High-fidelity Lanczos 3x Resampling
                upscaled = rgb_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

                # 2. Adaptive unsharp mask to restore crisp edges and eliminate blur
                sharpened = upscaled.filter(ImageFilter.UnsharpMask(radius=1.5, percent=125, threshold=2))

                # 3. Whiten near-white background pixels (>238 in all RGB channels) to eliminate DCT compression noise
                arr = np.array(sharpened)
                near_white = (arr[:, :, 0] > 238) & (arr[:, :, 1] > 238) & (arr[:, :, 2] > 238)
                arr[near_white] = [255, 255, 255]
                cleaned = Image.fromarray(arr)

                # Save back to file with high quality
                ext = os.path.splitext(fname)[1].lower()
                if ext == '.webp':
                    cleaned.save(filepath, 'WEBP', quality=95, method=6)
                elif ext in ('.jpg', '.jpeg'):
                    cleaned.save(filepath, 'JPEG', quality=95, optimize=True)
                elif ext == '.png':
                    cleaned.save(filepath, 'PNG', optimize=True)

                processed += 1
        except Exception as e:
            print(f"Error processing {fname}: {e}")

    print(f"Finished! Enhanced {processed} images to 3x High-Resolution. Skipped {skipped} already high-res images.")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_dir = os.path.join(base_dir, 'media', 'cars')
    enhance_car_images(target_dir)

