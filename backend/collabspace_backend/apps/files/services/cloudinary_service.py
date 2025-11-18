import cloudinary
import cloudinary.uploader
from django.conf import settings
from PIL import Image
import io
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
                **kwargs # Allow passing additional options
            )
            return {
                'success': True,
                'url': result['secure_url'],
                'public_id': result['public_id'],
                'format': result.get('format'),
                'width': result.get('width'),
                'height': result.get('height'),
                'bytes': result.get('bytes'),
                'duration': result.get('duration') # for video/audio
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
             # Generate a thumbnail for video/audio (e.g., first frame)
             return CloudinaryImage(public_id).build_url(
                resource_type="video",
                transformation=[
                    {'width': width, 'height': height, 'crop': 'fill'},
                    {'format': 'jpg', 'quality': 'auto', 'fetch_format': 'auto'}
                ]
             )
        return None

    @staticmethod
    def get_optimized_url(public_id, **transformations):
        """Get optimized URL with transformations"""
        from cloudinary import CloudinaryImage
        return CloudinaryImage(public_id).build_url(**transformations)

    @staticmethod
    def validate_file(file):
        """Validate file before upload"""
        max_size_mb = settings.FILE_UPLOAD_MAX_SIZE / (1024 * 1024)

        # Check file size
        if file.size > settings.FILE_UPLOAD_MAX_SIZE:
            return False, f"File size exceeds {max_size_mb:.0f}MB limit"

        # Check file type
        if file.content_type not in settings.ALLOWED_FILE_TYPES:
            # Fallback check
            guessed_type, _ = mimetypes.guess_type(file.name)
            if guessed_type and guessed_type in settings.ALLOWED_FILE_TYPES:
                file.content_type = guessed_type
            else:
                return False, f"File type '{file.content_type}' not allowed"

        return True, "Valid"

    @staticmethod
    def compress_image(file, quality=85):
        """Compress image before upload (for JPEG format)"""
        if not file.content_type.startswith('image/'):
            return file

        try:
            img = Image.open(file)
            output = io.BytesIO()

            # Convert RGBA to RGB for JPEG compression
            if img.mode == 'RGBA':
                img = img.convert('RGB')

            # Use JPEG for compression as it's efficient for this task
            img.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            
            # Create a mock UploadedFile object/adjust attributes
            output.name = file.name
            output.size = output.getbuffer().nbytes
            # Note: Content type changes to 'image/jpeg' if compressed to JPEG
            output.content_type = 'image/jpeg' 
            return output
        except Exception as e:
            # In a real app, use proper logging
            print(f"Error compressing image: {e}") 
            return file # Return original if compression fails