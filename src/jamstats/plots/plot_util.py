
__author__ = "Damon May"

import seaborn as sns
from jamstats.data.game_data import DerbyGame
import logging
from matplotlib import pyplot as plt
from typing import Any, Iterable, Dict
from textwrap import wrap
import random
from matplotlib.pyplot import Figure

from abc import ABCMeta, abstractmethod

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


class DerbyPlot(ABCMeta):
    """Base class for all plots
    """
    def __init__(self) -> None:
        self.name = "DerbyPlot"
        pass

    def get_name(self) -> str:
        """Get the name of the plot.
        Returns:
            str: name
        """
        return self.name

    @abstractmethod
    def plot(self, derby_game: DerbyGame) -> Figure: 
        """Plot the plot using the passed-in DerbyGame.

        Args:
            derby_game (DerbyGame): Derby Game

        Returns:
            Figure: matplotlib figure
        """
        pass


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


def convert_millis_to_min_sec_str(millis: int) -> str:
    """ Convert milliseconds to a string of minutes:seconds.

    Args:
        millis (int): milliseconds

    Returns:
        str: minutes:seconds
    """
    minutes = int(millis/(1000*60))%60
    seconds = int(millis/1000)%60
    seconds_str = str(seconds)
    if seconds < 10:
        seconds_str = "0" + seconds_str
    
    return f"{minutes}:{seconds_str}"


def build_anonymizer_map(names: Iterable[str]) -> Dict[str, str]:
    """Build a dictionary from unique passed-in names to randomly selected
    anonymized skater names.

    Will fail if you ask for more names than the list contains (about 60)

    Args:
        names (Iterable[str]): input names

    Returns:
        Dict[str, str]: map from input names to anonymized names
    """
    # just in case the names aren't unique
    names_set_list = list(set(names))
    anonymized_names = random.sample(ANONYMIZED_SKATER_NAMES, len(names_set_list))
    return {
        names_set_list[i]: anonymized_names[i]
        for i in range(len(names_set_list))
    }


ANONYMIZED_SKATER_NAMES = [
    "Middle Skull Crush",
    "Magic Missile",
    "Caffiend",
    "Artemis Foul",
    "Madame Fury",
    "Rejected",
    "Elena Traffic",
    "Fate Skar",
    "Bee Knighter",
    "Hate Skar'd",
    "Clever Bruise",
    "Sudden Beth",
    "Nasty, Brutish and Me",
    "Penalty Fox",
    "Mike Wheeler",
    "Foe Stops",
    "Foul Doubt",
    "Scarlight Express",
    "Stang 'Er Things",
    "Strangler Things",
    "Tragic Missile",
    "Skate of Shock",
    "Murder Hornet",
    "Max May-wheeled",
    "Boba Teen",
    "Superscar",
    "Elenavalanche",
    "Scar the Grouch",
    "Scar Wylde",
    "Rebel Girl",
    "Scarhawk",
    "Sass Squatch",
    "Stronger Than You",
    "Scartillery",
    "Bad Assassin",
    "Sassassin",
    "Ambulance",
    "Global Harming",
    "Seabattle",
    "Cascade Deranged",
    "Columbia Shiv 'Er",
    "Scarstruck",
    "Sneak Attrack",
    "Duel Wheeled",
    "Awful Good",
    "Broad Sword",
    "Roll for Damage",
    "Nat Twenty",
    "Scorehammer",
    "Javelin",
    "Unarmed Strike",
    "Morning Scar",
    "Critical Roll",
    "Shortsword",
    "Chaos Muppet",
    "Scartemis",
    "Kestrel",
    "No Regrette",
    "The Sparkly Cloud Killer",
    "Ada Hatelace",
    "Wheela Monster",
    "Poison Dart Frog",
]