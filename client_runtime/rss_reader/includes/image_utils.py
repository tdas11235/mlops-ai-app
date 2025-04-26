import tempfile
import requests
import os
import base64
import logging


logger = logging.getLogger("image_utils")


def download_image(image_url, filename):
    """Synchronous function to download an image and save it to a temporary file."""
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, filename)
            # Write the image content to the file
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            logger.info(
                f"Image successfully downloaded and saved to {temp_path}")
            return temp_path  # Return the saved file path
        else:
            logger.error(
                f"Failed to download image. HTTP Status: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        return None


def image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Error encoding image to base64: {e}")
    return None


def base64_to_image(base64_string, output_path):
    try:
        with open(output_path, "wb") as image_file:
            image_file.write(base64.b64decode(base64_string))
        logger.info(f"Image successfully saved to {output_path}")
    except Exception as e:
        logger.error(f"Error decoding base64 to image: {e}")
