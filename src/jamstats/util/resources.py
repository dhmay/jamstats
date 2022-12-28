
__author__ = "Damon May"

from typing import Any
import logging
from matplotlib import pyplot as plt
from importlib import resources as importlib_resources
import sys, os
import io
import traceback

logger = logging.Logger(__name__)

resource_file_dict = {
}

def get_jamstats_logo_image() -> bytes:
    """Get the jamstats logo image as bytes. Try to load from the resources.
    If ail, generate from a matplotlib plot
    Returns:
        Image: jamstats logo
    """
    try:
        return get_resource("jamstats_logo.png")
    except Exception as e:
        logger.info(f"Failed to load logo image from resources: {e}")
        f, ax = plt.subplots()
        ax.text(0.5, 0.5, "Jamstats", transform=ax.transAxes, ha="center", size=80)
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png')
        resource_file_dict["jamstats_logo.png"] = img_buf.getvalue()
        return resource_file_dict["jamstats_logo.png"]


def get_jamstats_version() -> str:
    """Get the jamstats version string
    Returns:
        str: jamstats version
    """
    try:
        return get_resource("jamstats_version.txt").strip()
    except Exception as e:
        logger.info(f"Failed to load version from resources: {e}")
        logger.info(traceback.format_exc())
    return "unknown"


def get_resource(resource_filename: str) -> Any:
    """Load a binary file from the package or from the resources directory.
    This repeats a lot of code from get_resource_text, but I don't know how to not do that

    Args:
        resource_filename (str): filename to load

    Returns:
        Any: the file as bytes or str, depending on the file type
    """
    is_binary = resource_filename.endswith(".png")
    if resource_filename not in resource_file_dict:
        if hasattr(sys, '_MEIPASS'):
            # we appear to be running from a pyinstaller bundle
            logger.debug("Loading image from MEIPASS")
            bundle_dir = getattr(sys, '_MEIPASS')
            path_to_logo = os.path.abspath(os.path.join(bundle_dir, resource_filename))
            with open(path_to_logo, 'rb' if is_binary else 'r') as f:
                resource_file_dict[resource_filename] = f.read()
        else:
            # we appear to be running from source
            logger.debug("Loading image from source")
            with importlib_resources.path('jamstats.resources', resource_filename) as path:
                contents = path.read_bytes() if is_binary else path.read_text()
                resource_file_dict[resource_filename] = contents
    return resource_file_dict[resource_filename]