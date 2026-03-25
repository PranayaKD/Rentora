import os
import sys
import django
from PIL import Image

# Add the current directory to the path so it can find the Django settings
sys.path.append(os.getcwd())

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rentora_project.settings')
django.setup()

from core.models import Car

def optimize_images():
    media_root = 'media/cars/'
    if not os.path.exists(media_root):
        print(f"Error: {media_root} does not exist.")
        return

    files = [f for f in os.listdir(media_root) if os.path.isfile(os.path.join(media_root, f))]
    
    for filename in files:
        file_path = os.path.join(media_root, filename)
        name, ext = os.path.splitext(filename)
        
        if ext.lower() in ['.jpg', '.jpeg', '.png', '.avif']:
            new_filename = f"{name}.webp"
            new_path = os.path.join(media_root, new_filename)
            
            try:
                with Image.open(file_path) as img:
                    # Special handling for the massive hero image
                    if filename == 'hero-main.jpg':
                        # Scale down if it's overly huge (e.g., > 2000px width)
                        if img.width > 1920:
                            ratio = 1920 / img.width
                            new_size = (1920, int(img.height * ratio))
                            img = img.resize(new_size, Image.Resampling.LANCZOS)
                        
                        img.save(new_path, 'WEBP', quality=85, optimize=True)
                        print(f"Optimized Hero Image: {filename} -> {new_filename}")
                    else:
                        img.save(new_path, 'WEBP', quality=95)
                        print(f"Converted: {filename} -> {new_filename}")
                
                # Update Database
                old_relative_path = f"cars/{filename}"
                new_relative_path = f"cars/{new_filename}"
                
                updated_count = Car.objects.filter(image=old_relative_path).update(image=new_relative_path)
                if updated_count > 0:
                    print(f"Updated {updated_count} car records for {new_filename}")
                
                # Delete original if it's NOT the hero image (keep a backup of hero just in case)
                if filename != 'hero-main.jpg' and os.path.exists(new_path):
                    # os.remove(file_path) # Uncomment if you want to save space immediately
                    pass

            except Exception as e:
                print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    optimize_images()
