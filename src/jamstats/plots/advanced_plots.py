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
import numpy as np
from jamstats.plots.plot_util import (
    make_team_color_palette,
    wordwrap_x_labels
)


logger = logging.Logger(__name__)

def plot_jammers_by_team(derby_game: DerbyGame) -> Figure:
    """Plot jammers by team

    Args:
        derby_game (DerbyGame): Derby game

    Returns:
        Figure: figure
    """
    pdf_jams_data = derby_game.pdf_jams_data

    jammer_jamcounts_1 = list(pdf_jams_data.value_counts("jammer_name_1"))
    jammer_jamcounts_2 = list(pdf_jams_data.value_counts("jammer_name_2"))

    jammer_jamcounts = jammer_jamcounts_1 + jammer_jamcounts_2
    team_names_for_jamcounts = ([derby_game.team_1_name] * len(jammer_jamcounts_1) +
                                [derby_game.team_2_name] * len(jammer_jamcounts_2))
    pdf_jammer_jamcounts = pd.DataFrame({
        "team": team_names_for_jamcounts,
        "jam_count": jammer_jamcounts
    })

    team_color_palette = make_team_color_palette(derby_game)

    f, axes = plt.subplots(1, 3)
    ax = axes[0]
    sns.barplot(x="team", y="jammers",
                data=pd.DataFrame({
                    "team": [derby_game.team_1_name, derby_game.team_2_name],
                    "jammers": [sum(pdf_jammer_jamcounts.team == derby_game.team_1_name),
                                sum(pdf_jammer_jamcounts.team == derby_game.team_2_name)]
                }),
                ax=ax, palette=team_color_palette)
    # word-wrap too-long team names
    wordwrap_x_labels(ax)
    ax.set_title("Jammers per team")

    ax = axes[1]
    sns.violinplot(x="team", y="jam_count", data=pdf_jammer_jamcounts, cut=0, ax=ax,
                   palette=team_color_palette, inner="stick")
    ax.set_title("Jams per jammer")
    ax.set_ylabel("Jams per jammer")
    # word-wrap too-long team names
    wordwrap_x_labels(ax)

    pdf_jammer_summary_1 = pdf_jams_data.groupby(
        "jammer_name_1").agg({"jammer_points_1": "mean", "Number": "count"}).rename(
        columns={"jammer_points_1": "mean_jam_score", "Number": "n_jams"})
    pdf_jammer_summary_1.index = range(len(pdf_jammer_summary_1))
    pdf_jammer_summary_2 = pdf_jams_data.groupby(
        "jammer_name_2").agg({"jammer_points_2": "mean", "Number": "count"}).rename(
        columns={"jammer_points_2": "mean_jam_score", "Number": "n_jams"}) 
    pdf_jammer_summary_2.index = range(len(pdf_jammer_summary_2))

    ax =axes[2]
    sns.scatterplot(x="n_jams", y="mean_jam_score", data=pdf_jammer_summary_1,
                    label=derby_game.team_2_name, color=team_color_palette[0])
    sns.scatterplot(x="n_jams", y="mean_jam_score", data=pdf_jammer_summary_2,
                    label=derby_game.team_2_name, color=team_color_palette[1])
    ax.set_title("Mean jam score vs.\n# jams per jammer")
    ax.set_ylabel("Mean jam score")
    ax.set_xlabel("# jams")
    # word-wrap too-long team names
    wordwrap_x_labels(ax)
    ax.legend().remove()

    f.set_size_inches(14,6)
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

        # add penalties per jam
        pdf_skater_data["penalty_count"] = [skater_penaltycount_map[skater]
                                            if skater in skater_penaltycount_map else 0
                                            for skater in pdf_skater_data.Skater]
        # sort skater data, too
        pdf_skater_data = pdf_skater_data.sort_values("penalty_count", ascending=False)
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


