
__author__ = "Damon May"

import seaborn as sns
from jamstats.data.game_data import DerbyGame
import logging
from matplotlib import pyplot as plt

logger = logging.Logger(__name__, level=logging.DEBUG)

DEFAULT_THEME = "white"

VALID_THEMES = [
    "white",
    "dark",
    "whitegrid",
    "darkgrid",
    "ticks"
]


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

