
__author__ = "Damon May"

import seaborn as sns
from jamstats.data.game_data import DerbyGame
import logging
from matplotlib import pyplot as plt
from typing import Any
from textwrap import wrap
import matplotlib.ticker as mticker

logger = logging.Logger(__name__)

DEFAULT_THEME = "white"

VALID_THEMES = [
    "white",
    "dark",
    "whitegrid",
    "darkgrid",
    "ticks"
]

# default maximum length of x labels
DEFAULT_XLABEL_MAX_LEN = 15

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


def wordwrap_x_labels(ax: Any, max_len: int = DEFAULT_XLABEL_MAX_LEN):
    """Wrap x labels on a plot so they don't overlap.

    ax argument is actually an Axes, but I don't know where that class lives

    Args:
        ax (AxesSubplot): Axes
    """
    new_xticklabels = []
    for tick in ax.get_xticklabels():
        orig_text = tick.get_text()
        new_text = "\n".join(wrap(orig_text, max_len))
        new_xticklabels.append(new_text)
    # this line is necessary in order to avoid a warning
    ticks = ax.get_xticks()
    if type(ticks) != list:
        ticks = ax.get_xticks().tolist()
    ax.set_xticks(ticks)
    ax.set_xticklabels(new_xticklabels)