import os
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.conf import settings

class Command(BaseCommand):
    help = 'Migrates existing local media files to the configured cloud storage'

    def handle(self, *args, **options):
        local_media_root = settings.BASE_DIR / 'media'
        
        if not os.path.exists(local_media_root):
            self.stdout.write(self.style.ERROR('Local media directory does not exist.'))
            return

        self.stdout.write(self.style.SUCCESS('Starting media migration...'))
        
        count = 0
        for root, dirs, files in os.walk(local_media_root):
            for file in files:
                local_path = os.path.join(root, file)
                # Relative path for the storage backend
                relative_path = os.path.relpath(local_path, local_media_root)
                
                if not default_storage.exists(relative_path):
                    self.stdout.write(f'Uploading: {relative_path}...')
                    with open(local_path, 'rb') as f:
                        default_storage.save(relative_path, f)
                    count += 1
                else:
                    self.stdout.write(self.style.WARNING(f'Skipped (already exists): {relative_path}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully migrated {count} files to cloud storage.'))
