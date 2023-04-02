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
from matplotlib import gridspec
import traceback
from jamstats.plots.plot_util import build_anonymizer_map


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

    pdf_jammer_data = pdf_jammer_data.sort_values(["Jams", "Total Score"], ascending=False)

    f, (ax0, ax1, ax2, ax3, ax4) = plt.subplots(1, 5)

    # build a palette that'll be the same for both teams
    max_n_jammers = max([len(set(derby_game.pdf_jams_data.jammer_name_1)),
                         len(set(derby_game.pdf_jams_data.jammer_name_2))])
    mypalette = sns.color_palette("rainbow", n_colors=max_n_jammers)

    ax = ax0
    sns.barplot(y="Jammer", x="Jams", data=pdf_jammer_data, ax=ax, palette=mypalette)
    ax.set_ylabel("")

    ax = ax1
    sns.barplot(y="Jammer", x="Total Score", data=pdf_jammer_data, ax=ax, palette=mypalette)
    ax.set_yticks([])
    ax.set_ylabel("")

    ax = ax2
    sns.barplot(y="Jammer", x="Mean Net Points",
            data=pdf_jammer_data, ax=ax, palette=mypalette)
    ax.set_xlabel("Mean Net Points/Jam\n(own - opposing)")
    ax.set_yticks([])
    ax.set_ylabel("")

    ax = ax3
    sns.barplot(y="Jammer", x="Proportion Lead", data=pdf_jammer_data, ax=ax, palette=mypalette)
    ax.set_xlim(0,1)
    ax.set_yticks([])
    ax.set_ylabel("")

    ax = ax4
    sns.barplot(y="Jammer", x="Mean Time to Initial", data=pdf_jammer_data, ax=ax, palette=mypalette)
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
    }).sort_values("Skater")

    if anonymize_names:
        logger.debug("Anonymizing skater names.")
        name_dict = build_anonymizer_map(set(pdf_skater_data.Skater))
        pdf_skater_data["Skater"] = [name_dict[skater] for skater in pdf_skater_data.Skater]   

    # Try to add penalty data.
    penalty_plot_is_go = False
    try:
        pdf_team_penalties = derby_game.pdf_penalties[
            derby_game.pdf_penalties.team == team_name].copy()
        pdf_team_penalties = pdf_team_penalties.rename(columns={
            "Name": "Skater"
        })
        if anonymize_names:
            pdf_team_penalties["Skater"] = [name_dict[skater]
                                            for skater in pdf_team_penalties.Skater]   

        pdf_team_penalties["Penalty"] = [
            code + ": " + name
            for code, name in zip(*[pdf_team_penalties.penalty_code,
                                    pdf_team_penalties.penalty_name])
        ]
        pdf_penalties_long = (
            pdf_team_penalties.groupby(['Skater', 'Penalty']).size().reset_index())
        pdf_penalties_long = pdf_penalties_long.rename(columns={
            0: "penalty_count"
        })
        a_penalty = list(pdf_team_penalties.Penalty)[0]
        
        # add rows for skaters with no penalties.
        # There's probably some more-pandas-y way to do this. I trie and failed.
        skaters_no_penalties = set(pdf_skater_data.Skater).difference(
            set(set(pdf_team_penalties.Skater)))
        # add rows in the skaters table for skaters with penalties who didn't appear there.
        missingskaters_with_penalties = set(pdf_team_penalties.Skater).difference(set(pdf_skater_data.Skater))
        pdf_skater_data = pd.concat([pdf_skater_data, pd.DataFrame({
            "Skater": list(missingskaters_with_penalties),
            "Jams": [1] * len(missingskaters_with_penalties)
        })])

        pdf_penalties_long = pd.DataFrame({
            "Skater": list(pdf_penalties_long.Skater) + list(skaters_no_penalties),
            "Penalty": list(pdf_penalties_long.Penalty) + [a_penalty] * len(skaters_no_penalties),
            "penalty_count": list(pdf_penalties_long["penalty_count"]) + [0] * len(skaters_no_penalties)
        })

        pdf_penalties_long = pdf_penalties_long[~pdf_penalties_long.Skater.isna()]

        # calculate number of penalties per skater. Again, there must be a better way,
        # probably with groupby. Eh.
        skater_penaltycount_map = {
            skater: sum(pdf_penalties_long[pdf_penalties_long.Skater == skater].penalty_count)
            for skater in set(pdf_penalties_long.Skater)
        }

        pdf_penalty_plot = pdf_penalties_long.pivot(
            columns='Penalty', index='Skater', values="penalty_count")

        pdf_penalty_plot["skater_order"] = [skater_penaltycount_map[skater]
                                           for skater in pdf_penalty_plot.index]
        pdf_penalty_plot = pdf_penalty_plot.sort_values("skater_order", ascending=False)
        pdf_penalty_plot = pdf_penalty_plot.drop(columns=["skater_order"])

        # sort skater data, too
        
        # this would be better done with a dataframe and a join. Eh.
        pdf_skater_data["skater_order"] = [skater_penaltycount_map[skater]
                                            for skater in pdf_skater_data.Skater]
        pdf_skater_data = pdf_skater_data.sort_values("skater_order", ascending=False)
        pdf_skater_data = pdf_skater_data.drop(columns=["skater_order"])

        # add penalties per jam
        pdf_skater_data["penalty_count"] = [skater_penaltycount_map[skater]
                                            for skater in pdf_skater_data.Skater]
        pdf_skater_data["penalties_per_jam"] = (
            pdf_skater_data["penalty_count"] / pdf_skater_data["Jams"])

        penalty_plot_is_go = True
    except Exception as e:
        logger.warn(f"Failed to make skater penalty subplot:")
        logger.warn(traceback.format_exc())

    f, dummy_axis = plt.subplots()
    dummy_axis.set_xticks([])
    dummy_axis.set_yticks([])
    # create grid for different subplots
    spec = gridspec.GridSpec(ncols=3, nrows=1,
                             width_ratios=[1, 3, 1], wspace=0)

    ax = f.add_subplot(spec[0])
    sns.barplot(y="Skater", x="Jams", data=pdf_skater_data, ax=ax, color="black")
    ax.set_title("Jams") 
    ax.set_ylabel("")

    if penalty_plot_is_go:
        # color penalties
        penalty_color_map = dict(zip(*[pdf_team_penalties.Penalty,
                                       pdf_team_penalties.penalty_color]))

        ax = f.add_subplot(spec[1])
        pdf_penalty_plot.plot(kind="barh", stacked=True, ax=ax,
            color=penalty_color_map)
        plt.gca().invert_yaxis()
        ax.set_title(f"Penalties by skater")
        ax.set_ylabel("")
        ax.set_xlabel("Penalties")
        ax.set_yticks([])
        # add numeric penalties
        penalty_counts = list(pdf_skater_data.penalty_count)
        for i in range(len(pdf_skater_data)):
            ax.text(.5, i, penalty_counts[i], size="small",
                    horizontalalignment="center",
                    verticalalignment="center")

        ax = f.add_subplot(spec[2])
        sns.barplot(y="Skater", x="penalties_per_jam", data=pdf_skater_data, ax=ax, color="black")
        ax.set_title("Penalties/Jam") 
        ax.set_ylabel("")
        ax.set_xlabel("Penalties/Jam")
        ax.set_yticks([])

    f.set_size_inches(13, min(2 + len(pdf_skater_data), 11))
    f.suptitle(f"Skater Stats: {team_name}")
    f.tight_layout()
    return f


