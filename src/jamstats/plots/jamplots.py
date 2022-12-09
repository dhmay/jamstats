__author__ = "Damon May"

import pandas as pd
from matplotlib.figure import Figure
from typing import Dict, List
import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from jamstats.data.game_data import DerbyGame
import logging

logger = logging.Logger(__name__)

def save_game_plots_to_pdf(derby_game: DerbyGame,
                           out_filepath: str) -> None:
    """Read in a jams .tsv file, make all the plots, write to a .pdf

    Args:
        in_filepath (str): jams .tsv filepath
        out_filepath (str): output .pdf filepath
    """
    prepare_to_plot()
    figures = make_all_plots(derby_game)
    pdfout = PdfPages(out_filepath)
    logging.debug(f"Saving {len(figures)} figures to {out_filepath}")
    for figure in figures:
        pdfout.savefig(figure)
    pdfout.close()
    logging.debug(f"Wrote {out_filepath}")


def prepare_to_plot() -> None:
    """Prepare Seaborn to make pretty plots.
    """
    sns.set_context("talk")
    sns.set_style("white")

def make_all_plots(derby_game: DerbyGame) -> List[Figure]:
    """Build all plots, suitable for exporting to a .pdf

    Args:
        derby_game (DerbyGame): a derby game
    Returns:
        List[Figure]: figures
    """
    figures = []
    for plot_func in [
        plot_game_summary_table,
        plot_game_teams_summary_table,
        plot_jam_lead_and_scores,
        plot_cumulative_score_by_jam,
        plot_jammers_by_team,
        histogram_jam_duration,
        plot_lead_summary
    ]:
        try:
            figures.append(plot_func(derby_game))
        except Exception as e:
            logger.warn(f"Failed to make plot: {e}")
    return figures


def plot_jammers_by_team(derby_game: DerbyGame) -> Figure:
    """Plot jammers by team

    Args:
        derby_game (DerbyGame): Derby game

    Returns:
        Figure: figure
    """
    pdf_jams_data = derby_game.pdf_jams_data
    game_data_dict = derby_game.game_data_dict
    team_1 = game_data_dict["team_1"]
    team_2 = game_data_dict["team_2"]

    jammer_jamcounts_1 = list(pdf_jams_data.value_counts("jammer_name_1"))
    jammer_jamcounts_2 = list(pdf_jams_data.value_counts("jammer_name_2"))

    jammer_jamcounts = jammer_jamcounts_1 + jammer_jamcounts_2
    team_names_for_jamcounts = [team_1] * len(jammer_jamcounts_1) + [team_2] * len(jammer_jamcounts_2)
    pdf_jammer_jamcounts = pd.DataFrame({
        "team": team_names_for_jamcounts,
        "jam_count": jammer_jamcounts
    })

    f, axes = plt.subplots(1, 3)
    ax = axes[0]
    sns.barplot(x="team", y="jammers",
                data=pd.DataFrame({
                    "team": [team_1, team_2],
                    "jammers": [sum(pdf_jammer_jamcounts.team == team_1),
                                sum(pdf_jammer_jamcounts.team == team_2)]
                }),
                ax=ax)
    ax.set_title("Jammers per team")

    ax = axes[1]
    sns.violinplot(x="team", y="jam_count", data=pdf_jammer_jamcounts, cut=0, ax=ax)
    ax.set_title("Jams per jammer")
    ax.set_ylabel("Jams per jammer")

    pdf_jammer_summary_1 = pdf_jams_data.groupby(
        "jammer_name_1").agg({"JamScore_1": "mean", "Number": "count"}).rename(
        columns={"JamScore_1": "mean_jam_score", "Number": "n_jams"})
    pdf_jammer_summary_1.index = range(len(pdf_jammer_summary_1))
    pdf_jammer_summary_2 = pdf_jams_data.groupby(
        "jammer_name_2").agg({"JamScore_2": "mean", "Number": "count"}).rename(
        columns={"JamScore_2": "mean_jam_score", "Number": "n_jams"}) 
    pdf_jammer_summary_2.index = range(len(pdf_jammer_summary_2))

    ax =axes[2]
    sns.scatterplot(x="n_jams", y="mean_jam_score", data=pdf_jammer_summary_1, label=team_1)
    sns.scatterplot(x="n_jams", y="mean_jam_score", data=pdf_jammer_summary_2, label=team_2)
    ax.set_title("Mean jam score vs.\n# jams per jammer")
    ax.set_ylabel("Mean jam score")
    ax.set_xlabel("# jams")
    ax.legend().remove()

    f.set_size_inches(14,6)
    f.tight_layout()

    return f


def plot_game_summary_table(derby_game: DerbyGame) -> Figure:
    """Make a table figure out of the game summary dataframe,
    suitable for writing to a .pdf

    Args:
        derby_game (DerbyGame): a derby game

    Returns:
        Figure: table figure
    """
    pdf_game_summary = derby_game.extract_game_summary()

    f, ax = plt.subplots()
    ax.axis('tight')
    ax.axis('off')
    ax.table(cellText=pdf_game_summary.values,
             colLabels=pdf_game_summary.columns,
             loc='center')
    f.set_size_inches(8, 4)
    return f


def plot_game_teams_summary_table(derby_game: DerbyGame) -> Figure:
    """Make a table figure out of the teams summary dataframe,
    suitable for writing to a .pdf

    Args:
        derby_game (DerbyGame): a derby game

    Returns:
        Figure: table figure
    """
    pdf_game_teams_summary = derby_game.extract_game_teams_summary()

    f, ax = plt.subplots()
    ax.axis('tight')
    ax.axis('off')
    ax.table(cellText=pdf_game_teams_summary.values,
             colLabels=pdf_game_teams_summary.columns,
             loc='center')
    f.set_size_inches(8,4)
    return f


def plot_jam_lead_and_scores(derby_game: DerbyGame) -> Figure:
    """Given a long-format jam dataframe, visualize lead and scores per jam

    Args:
        derby_game (DerbyGame): a derby game

    Returns:
        Figure: figure
    """
    game_data_dict = derby_game.game_data_dict
    pdf_jam_data_long = derby_game.build_jams_dataframe_long()
    team_1 = game_data_dict["team_1"]
    team_2 = game_data_dict["team_2"]

    f, ax = plt.subplots()

    sns.barplot(x="JamScore", y="prd_jam", data=pdf_jam_data_long, hue="team")
    ax.legend()
    ax.set_title("Points per jam (O indicates lead, X if lost)")
    ax.set_xlabel("Points")
    ax.set_ylabel("Jam")

    pdf_team1 = pdf_jam_data_long[pdf_jam_data_long.team == team_1].sort_values("prd_jam")
    pdf_team2 = pdf_jam_data_long[pdf_jam_data_long.team == team_2].sort_values("prd_jam")

    jamidx = -1
    for lead_1, lost_1, lead_2, lost_2 in zip(*[pdf_team1.Lead, pdf_team1.Lost, pdf_team2.Lead, pdf_team2.Lost]):
        jamidx += 1
        if lead_1 or lead_2:
            offset = 0.0 if lead_1 else .4
            symbol = "X" if (lost_1 or lost_2) else "O"
            color = sns.color_palette()[0] if lead_1 else sns.color_palette()[1]
            ax.text(-0.9, jamidx + offset, symbol, color=color, size=14, weight="bold")
                
    f.set_size_inches(8, 11)
    return f


def plot_cumulative_score_by_jam(derby_game: DerbyGame) -> Figure:
    """Plot cumulative score by jam

    Args:

    Returns:
        Figure: figure with cumulative score by jam
    """
    game_data_dict = derby_game.game_data_dict
    pdf_jam_data_long = derby_game.build_jams_dataframe_long()
    team_1 = game_data_dict["team_1"]
    team_2 = game_data_dict["team_2"]

    f, ax = plt.subplots()
    sns.lineplot(y="prd_jam", x="TotalScore",
                 data=pdf_jam_data_long[pdf_jam_data_long.team == team_1], label=team_1,
                 estimator=None)
    sns.lineplot(y="prd_jam", x="TotalScore",
                 data=pdf_jam_data_long[pdf_jam_data_long.team == team_2], label=team_2,
                 estimator=None)
    ax.set_title("Cumulative score by jam")
    ax.set_xlabel("Score")
    ax.set_ylabel("Period:Jam")

    f.set_size_inches(8, 11)

    return f


def histogram_jam_duration(derby_game: DerbyGame) -> Figure:
    """histogram jam durations

    Args:
        pdf_jam_data (pd.DataFrame): jam data

    Returns:
        Figure: histogram of jam durations
    """
    f, ax = plt.subplots()
    sns.histplot(derby_game.pdf_jams_data.duration_seconds, ax=ax)
    ax.set_title("Jam duration (s)")
    ax.set_xlabel("Seconds")
    f.set_size_inches(8, 6)
    return f


def plot_lead_summary(derby_game: DerbyGame) -> Figure:
    """violin plot time to lead (from whistle until lead jammer gets lead)

    Args:
        derby_game (DerbyGame): derby game

    # TODO: currently, ordering teams by team name in this plot. Order by team number
    for consistency.

    Returns:
        Figure: violin plot
    """
    pdf_jams_with_lead = derby_game.pdf_jams_data[derby_game.pdf_jams_data.Lead_1 |
                                              derby_game.pdf_jams_data.Lead_2].copy()
    pdf_jams_with_lead["Team with Lead"] = [derby_game.team_1_name if team1_has_lead
                                            else derby_game.team_2_name
                                            for team1_has_lead in pdf_jams_with_lead.Lead_1]
    f, axes = plt.subplots(1, 2)
    ax = axes[0]
    pdf_jams_with_lead["Lost"] = pdf_jams_with_lead.Lost_1 | pdf_jams_with_lead.Lost_2

    pdf_for_plot_all = pdf_jams_with_lead[
        ["Team with Lead", "prd_jam"]].groupby(
            ["Team with Lead"]).agg("count").reset_index().sort_values("Team with Lead")
    pdf_for_plot_lost = pdf_jams_with_lead[pdf_jams_with_lead.Lost][
        ["Team with Lead", "prd_jam"]].groupby(
            ["Team with Lead"]).agg("count").reset_index().sort_values("Team with Lead")
    pdf_for_plot_called_or_lost = pdf_jams_with_lead[pdf_jams_with_lead.Lost |
                                                     pdf_jams_with_lead.Calloff_1 |
                                                     pdf_jams_with_lead.Calloff_2][
        ["Team with Lead", "prd_jam"]].groupby(
            ["Team with Lead"]).agg("count").reset_index().sort_values("Team with Lead")
    if len(pdf_for_plot_all) > 0:
        sns.barplot(y="prd_jam", x="Team with Lead", data=pdf_for_plot_all, ax=ax)
    if len(pdf_for_plot_called_or_lost) > 0:
        sns.barplot(y="prd_jam", x="Team with Lead", data=pdf_for_plot_called_or_lost, ax=ax,
                    color="gray")
    if len(pdf_for_plot_lost) > 0:
        sns.barplot(y="prd_jam", x="Team with Lead",
                    data=pdf_for_plot_lost, ax=ax, color="darkred")

    ax.set_ylabel("Jams")
    ax.set_title("Jams with Lead\n(red=lost, gray=called)")

    ax = axes[1]
    sns.violinplot(y="time_to_lead", x="Team with Lead",
                data=pdf_jams_with_lead.sort_values("Team with Lead"), cut=0, ax=ax,
                inner="stick")
    ax.set_ylabel("Time to get Lead")
    ax.set_title("Time to get Lead (s)\nper jam")
    logger.debug("Failed to make violinplot, probably lack of data.")
    f.set_size_inches(8, 4)
    f.tight_layout()

    return f