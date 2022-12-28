
__author__ = "Damon May"

import seaborn as sns
from jamstats.data.game_data import DerbyGame
import logging
from matplotlib import pyplot as plt
import importlib
import sys, os
import io
from PIL import Image

logger = logging.Logger(__name__)

DEFAULT_THEME = "white"

VALID_THEMES = [
    "white",
    "dark",
    "whitegrid",
    "darkgrid",
    "ticks"
]

resource_file_dict = {
}

def prepare_to_plot(theme:str = DEFAULT_THEME) -> None:
    """Prepare Seaborn to make pretty plots.
    """
    # Get rid of the warning about opening too many figures
    plt.rcParams.update({'figure.max_open_warning': 0})

    # this makes fonts bigger and lines thicker
    sns.set_context("talk")
    logger.info(f"Using theme {theme}")
    sns.set_style(theme)


def make_team_color_palette(derby_game: DerbyGame):
    return sns.color_palette([derby_game.team_color_1, derby_game.team_color_2])


def get_jamstats_logo_image() -> Image:
    """Get the jamstats logo image. Try to load from the resources.
    If ail, generate from a matplotlib plot
    Returns:
        Image: jamstats logo
    """
    try:
        return get_resource_binary("jamstats_logo.png")
    except Exception as e:
        logger.info(f"Failed to load logo image from resources: {e}")
        f, ax = plt.subplots()
        ax.text(0.5, 0.5, "Jamstats", transform=ax.transAxes, ha="center", size=80)
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png')
        resource_file_dict["jamstats_logo.png"] = img_buf.getvalue()
        return resource_file_dict["jamstats_logo.png"]


def get_resource_binary(resource_filename: str) -> Image:
    """Load an image from the package or from the resources directory

    Args:
        resource_filename (str): filename of the image

    Returns:
        Image: image
    """
    if resource_filename not in resource_file_dict:
        if hasattr(sys, '_MEIPASS'):
            # we appear to be running from a pyinstaller bundle
            logger.debug("Loading image from MEIPASS")
            bundle_dir = getattr(sys, '_MEIPASS')
            path_to_logo = os.path.abspath(os.path.join(bundle_dir, resource_filename))
            with open(path_to_logo, 'rb') as f:
                resource_file_dict[resource_filename] = f.read()
        else:
            # we appear to be running from source
            logger.debug("Loading image from source")
            with importlib.resources.path('jamstats.resources', resource_filename) as path:
                resource_file_dict[resource_filename] = path.read_bytes()
    return resource_file_dict[resource_filename]