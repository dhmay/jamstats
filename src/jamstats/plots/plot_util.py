
__author__ = "Damon May"

import seaborn as sns
from jamstats.data.game_data import DerbyGame


def prepare_to_plot() -> None:
    """Prepare Seaborn to make pretty plots.
    """
    sns.set_context("talk")
    sns.set_style("white")


def make_team_color_palette(derby_game: DerbyGame):
    return sns.color_palette([derby_game.team_color_1, derby_game.team_color_2])

