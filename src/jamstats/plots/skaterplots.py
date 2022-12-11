__author__ = "Damon May"

from matplotlib.figure import Figure
from typing import Iterable, Dict
import seaborn as sns
from jamstats.data.game_data import DerbyGame
import logging
from matplotlib import pyplot as plt
import random
import string

logger = logging.Logger(__name__)

def plot_jammer_stats_team1(derby_game: DerbyGame,
                            anonymize_names: bool = False) -> Figure:
    return plot_jammer_stats(derby_game, 1, anonymize_names=anonymize_names)


def plot_jammer_stats_team2(derby_game: DerbyGame,
                            anonymize_names: bool = False) -> Figure:
    return plot_jammer_stats(derby_game, 2, anonymize_names=anonymize_names)


def plot_jammer_stats(derby_game: DerbyGame, team_number: int,
                      anonymize_names: bool = False) -> Figure:
    """Plot jammer stats for one team's jammers

    Args:
        derby_game (DerbyGame): derby game
        team_number (int): team number
        anonymize_names (bool): anonymize skater names

    Returns:
        Figure: figure
    """
    team_name = derby_game.team_1_name if team_number == 1 else derby_game.team_2_name
    pdf_jammer_data = derby_game.build_team_jammersummary_df(team_number)

    if anonymize_names:
        logger.debug("Anonymizing skater names.")
        name_dict = build_anonymizer_map(set(pdf_jammer_data.Jammer))
        pdf_jammer_data["Jammer"] = [name_dict[jammer] for jammer in pdf_jammer_data.Jammer]

    f, (ax0, ax1, ax2, ax3) = plt.subplots(1, 4)

    ax = ax0
    sns.barplot(y="Jammer", x="Jams", data=pdf_jammer_data, ax=ax)

    ax = ax1
    sns.barplot(y="Jammer", x="Total Score", data=pdf_jammer_data, ax=ax)
    ax.set_yticks([])
    ax.set_ylabel("")

    ax = ax2
    sns.barplot(y="Jammer", x="Mean Net Points", data=pdf_jammer_data, ax=ax)
    ax.set_yticks([])
    ax.set_ylabel("")

    ax = ax3
    sns.barplot(y="Jammer", x="Proportion Lead", data=pdf_jammer_data, ax=ax)
    ax.set_xlim(0,1)
    ax.set_yticks([])
    ax.set_ylabel("")

    f.set_size_inches(16, min(2 + len(pdf_jammer_data), 11))
    f.suptitle(f"Jammer Stats: {team_name}")
    f.tight_layout()

    return f


def build_anonymizer_map(names: Iterable[str],
                         anonymized_len = 8) -> Dict[str, str]:
    """Build a dictionary from unique passed-in names to randomly constructed names

    Args:
        names (Iterable[str]): input names
        anonymized_len (int, optional): length of anon names. Defaults to 8.

    Returns:
        Dict[str, str]: map from input names to anonymized names
    """
    names_set = set(names)
    anonymizer_dict = dict()
    for name in names_set:
        anonymizer_dict[name] = ''.join(
            random.choices(string.ascii_uppercase + string.digits,
                           k=anonymized_len))
    return anonymizer_dict