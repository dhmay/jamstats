__author__ = "Damon May"

from matplotlib.figure import Figure
from typing import Iterable, Dict
import seaborn as sns
from jamstats.data.game_data import DerbyGame
import logging
from matplotlib import pyplot as plt
import random
import string
import pandas as pd

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

    f, (ax0, ax1, ax2, ax3, ax4) = plt.subplots(1, 5)

    ax = ax0
    sns.barplot(y="Jammer", x="Jams", data=pdf_jammer_data, ax=ax)
    ax.set_ylabel("")

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

    ax = ax4
    sns.barplot(y="Jammer", x="Mean Time to Initial", data=pdf_jammer_data, ax=ax)
    ax.set_yticks([])
    ax.set_ylabel("")

    f.set_size_inches(16, min(2 + len(pdf_jammer_data), 11))
    f.suptitle(f"Jammer Stats: {team_name}")
    f.tight_layout()

    return f


def plot_skater_stats_team1(derby_game: DerbyGame,
                            anonymize_names: bool = False) -> Figure:
    return plot_skater_stats(derby_game, 1, anonymize_names=anonymize_names)


def plot_skater_stats_team2(derby_game: DerbyGame,
                            anonymize_names: bool = False) -> Figure:
    return plot_skater_stats(derby_game, 2, anonymize_names=anonymize_names)


def plot_skater_stats(derby_game: DerbyGame, team_number: int,
                      anonymize_names: bool = False) -> Figure:
    """Plot skater stats for one team's skaters

    Args:
        derby_game (DerbyGame): derby game
        team_number (int): team number
        anonymize_names (bool): anonymize skater names

    Returns:
        Figure: figure
    """
    team_name = derby_game.team_1_name if team_number == 1 else derby_game.team_2_name
    skater_lists = derby_game.pdf_jams_data[f"Skaters_{team_number}"]
    skater_jamcount_map = {}
    for skater_list in skater_lists:
        for skater in skater_list:
            if skater not in skater_jamcount_map:
                skater_jamcount_map[skater] = 0
            skater_jamcount_map[skater] += 1

    pdf_skater_data = pd.DataFrame({
        "Skater": list(skater_jamcount_map.keys()),
        "Jams": list(skater_jamcount_map.values()),
    })

    pdf_team_penalties = derby_game.pdf_penalties[
        derby_game.pdf_penalties.team == team_name]
    pdf_team_penalty_counts = pdf_team_penalties.Name.value_counts().reset_index().rename(
        columns={"index": "Skater", "Name": "Penalties"})
    # there is for sure a more efficient way to figure out most common penalty.
    # But I want to make sure I get the lowest-in-alphabet letter
    skater_mostcommon_penalties = []
    for skater in pdf_team_penalty_counts.Skater:
        pdf_skater_penalty_counts = pdf_team_penalties[
            pdf_team_penalties.Name == skater].penalty_code.value_counts().reset_index().rename(
                columns={"index": "penalty_code", "penalty_code": "Count"}
            )
        penalties_tiedfor_max = list(pdf_skater_penalty_counts[
            pdf_skater_penalty_counts.Count == max(pdf_skater_penalty_counts.Count)].penalty_code)
        skater_mostcommon_penalties.append(sorted(penalties_tiedfor_max)[0])
    pdf_team_penalty_counts["Top Penalty"] = skater_mostcommon_penalties
    

    pdf_skater_data = pdf_skater_data.merge(
        pdf_team_penalty_counts, on="Skater", how="left").fillna({
            "Penalties": 0, "Top Penalty": ""})

    if anonymize_names:
        logger.debug("Anonymizing skater names.")
        name_dict = build_anonymizer_map(set(pdf_skater_data.Skater))
        pdf_skater_data["Skater"] = [name_dict[skater] for skater in pdf_skater_data.Skater]    

    pdf_skater_data = pdf_skater_data.sort_values("Skater")

    f, axes = plt.subplots(1, 2)

    ax = axes[0]
    sns.barplot(y="Skater", x="Jams", data=pdf_skater_data, ax=ax)
    ax.set_title("Jams")
    ax.set_ylabel("")

    ax = axes[1]
    sns.barplot(y="Skater", x="Penalties", data=pdf_skater_data, ax=ax)
    for i, penalty in enumerate(pdf_skater_data["Top Penalty"]):
        ax.text(.5, i, penalty,
                horizontalalignment="center",
                verticalalignment="center")
    ax.set_title("Penalties (top marked)")

    ax.set_yticklabels([])
    ax.set_ylabel("")


    f.set_size_inches(8, min(2 + len(pdf_skater_data), 11))
    f.suptitle(f"Skater Stats: {team_name}")
    f.tight_layout() 
    return f


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