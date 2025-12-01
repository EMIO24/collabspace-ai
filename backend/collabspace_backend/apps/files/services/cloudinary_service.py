import cloudinary
import cloudinary.uploader
from django.conf import settings
from PIL import Image
import io
import magic  # Requires: pip install python-magic
import mimetypes

class CloudinaryService:
    """Service for Cloudinary operations"""

    @staticmethod
    def _get_resource_type(file_type):
        """Determine Cloudinary resource type from MIME type"""
        if file_type.startswith('image/'):
            return 'image'
        elif file_type.startswith('video/') or file_type.startswith('audio/'):
            return 'video'
        else:
            return 'raw'

    @staticmethod
    def upload_file(file, folder='uploads', public_id=None, **kwargs):
        """Upload file to Cloudinary"""
        try:
            # Determine resource type
            # Note: We trust the validated content_type from validate_file here
            file_type = file.content_type if hasattr(file, 'content_type') else mimetypes.guess_type(file.name)[0]
            resource_type = kwargs.pop('resource_type', CloudinaryService._get_resource_type(file_type))

            result = cloudinary.uploader.upload(
                file,
                folder=folder,
                public_id=public_id,
                resource_type=resource_type,
                overwrite=False,
                use_filename=True,
                unique_filename=True,
                **kwargs
            )
            return {
                'success': True,
                'url': result['secure_url'],
                'public_id': result['public_id'],
                'format': result.get('format'),
                'width': result.get('width'),
                'height': result.get('height'),
                'bytes': result.get('bytes'),
                'duration': result.get('duration')
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def delete_file(public_id, file_type):
        """Delete file from Cloudinary"""
        try:
            resource_type = CloudinaryService._get_resource_type(file_type)
            result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
            return {'success': result.get('result') == 'ok'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def generate_thumbnail(public_id, file_type, width=200, height=200):
        """Generate thumbnail URL using Cloudinary transformations"""
        from cloudinary import CloudinaryImage

        if file_type.startswith('image/'):
            return CloudinaryImage(public_id).build_url(
                width=width,
                height=height,
                crop='fill',
                quality='auto',
                fetch_format='auto'
            )
        elif file_type.startswith('video/') or file_type.startswith('audio/'):
             return CloudinaryImage(public_id).build_url(
                resource_type="video",
                transformation=[
                    {'width': width, 'height': height, 'crop': 'fill'},
                    {'format': 'jpg', 'quality': 'auto', 'fetch_format': 'auto'}
                ]
             )
        return None

    @staticmethod
    def validate_file(file):
        """
        Validate file using python-magic for true type detection 
        and check size limits.
        """
        # 1. Check file size
        max_size_mb = settings.FILE_UPLOAD_MAX_SIZE / (1024 * 1024)
        if file.size > settings.FILE_UPLOAD_MAX_SIZE:
            return False, f"File size exceeds {max_size_mb:.0f}MB limit"

        # 2. Check file type using Magic Bytes (Header inspection)
        try:
            # Read the first 2KB to determine type, then reset pointer
            initial_pos = file.tell()
            head = file.read(2048)
            file.seek(initial_pos)
            
            mime_type = magic.from_buffer(head, mime=True)
            
            if mime_type not in settings.ALLOWED_FILE_TYPES:
                return False, f"File type '{mime_type}' not allowed"
            
            # Update the Django file object with the correct, verified type
            file.content_type = mime_type
            
        except Exception as e:
            return False, f"Failed to validate file type: {str(e)}"

        return True, "Valid"

    @staticmethod
    def compress_image(file, quality=85):
        """
        Compress image with safety checks for 'Decompression Bomb' attacks
        and memory limits.
        """
        if not file.content_type.startswith('image/'):
            return file

        try:
            # Prevent DecompressionBombError for huge images (limit pixels)
            # Standard limit is usually around 178MP.
            Image.MAX_IMAGE_PIXELS = 90000000 # Limit to ~90MP to be safe

            img = Image.open(file)
            
            # Safety: If image is absurdly large in dimensions but small in file size (compression bomb)
            # Verify dimensions before processing
            if img.width > 10000 or img.height > 10000:
                # Skip compression for ultra-large dimensions to prevent memory exhaustion
                return file

            output = io.BytesIO()

            # Convert RGBA to RGB for JPEG compression
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Compress
            img.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            
            # Create a mock UploadedFile object attributes
            output.name = file.name
            output.size = output.getbuffer().nbytes
            output.content_type = 'image/jpeg' 
            return output

        except Image.DecompressionBombError:
            print("Image decompression bomb detected. Skipping compression.")
            return file
        except Exception as e:
            print(f"Error compressing image: {e}") 
            # Fallback: Return original file if compression fails
            return file