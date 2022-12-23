__author__ = "Damon May"

import pandas as pd
from matplotlib.figure import Figure
from typing import List, Optional
import seaborn as sns
from matplotlib import pyplot as plt
from jamstats.data.game_data import DerbyGame
import logging
from jamstats.plots.plot_util import make_team_color_palette


logger = logging.Logger(__name__)


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
    team_names_for_jamcounts = ([team_1] * len(jammer_jamcounts_1) +
                                [team_2] * len(jammer_jamcounts_2))
    pdf_jammer_jamcounts = pd.DataFrame({
        "team": team_names_for_jamcounts,
        "jam_count": jammer_jamcounts
    })

    team_color_palette = make_team_color_palette(derby_game)

    f, axes = plt.subplots(1, 3)
    ax = axes[0]
    sns.barplot(x="team", y="jammers",
                data=pd.DataFrame({
                    "team": [team_1, team_2],
                    "jammers": [sum(pdf_jammer_jamcounts.team == team_1),
                                sum(pdf_jammer_jamcounts.team == team_2)]
                }),
                ax=ax, palette=team_color_palette)
    ax.set_title("Jammers per team")

    ax = axes[1]
    sns.violinplot(x="team", y="jam_count", data=pdf_jammer_jamcounts, cut=0, ax=ax,
                   palette=team_color_palette, inner="stick")
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
    sns.scatterplot(x="n_jams", y="mean_jam_score", data=pdf_jammer_summary_1, label=team_1,
                    color=team_color_palette[0])
    sns.scatterplot(x="n_jams", y="mean_jam_score", data=pdf_jammer_summary_2, label=team_2,
                    color=team_color_palette[1])
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

    f = plt.figure(figsize=(8,3))
    ax = plt.subplot(111)
    ax.axis('off')
    ax.table(cellText=pdf_game_summary.values,
             colLabels=pdf_game_summary.columns, bbox=[0,0,1,1])
    return f


def plot_game_teams_summary_table(derby_game: DerbyGame) -> Figure:
    """Make a table figure out of the teams summary dataframe,
    suitable for writing to a .pdf

    Args:
        derby_game (DerbyGame): a derby game

    Returns:
        Figure: table figure
    """
    pdf_game_teams_summary = derby_game.extract_game_teams_summary().transpose()
    pdf_game_teams_summary = pdf_game_teams_summary.rename({"n_scoring_trips": "Scoring trips"})
    pdf_game_teams_summary["asdf"] = pdf_game_teams_summary.index
    pdf_game_teams_summary = pdf_game_teams_summary[["asdf", 0, 1]]
    f = plt.figure(figsize=(8, 10))
    ax = plt.subplot(111)
    ax.axis('off')
    ax.table(cellText=pdf_game_teams_summary.values,
            colLabels=None, bbox=[0,0,1,1])
    return f

def plot_jam_lead_and_scores_period1(derby_game: DerbyGame) -> Figure:
    return plot_jam_lead_and_scores(derby_game, period=1)

def plot_jam_lead_and_scores_period2(derby_game: DerbyGame) -> Figure:
    return plot_jam_lead_and_scores(derby_game, period=2)

def plot_jam_lead_and_scores(derby_game: DerbyGame,
                             period: Optional[int] = None) -> Figure:
    """Given a long-format jam dataframe, visualize lead and scores per jam

    Args:
        derby_game (DerbyGame): a derby game
        period (int): Period to plot. If not provided, plot both

    Returns:
        Figure: figure
    """
    logger.debug("Plotting jam lead and scores...")
    pdf_jam_data_long = derby_game.build_jams_dataframe_long()
    if period is not None:
        logger.debug(f"Restricting to period {period}")
        pdf_jam_data_long = pdf_jam_data_long[pdf_jam_data_long.PeriodNumber == period]

    f, (ax0, ax1) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [1, 4]})
    
    teamname_number_map = {derby_game.team_1_name: 1, derby_game.team_2_name: 2}
    pdf_jam_data_long["team_number"] = [teamname_number_map[name] for name in pdf_jam_data_long.team]
    
    ax = ax0
    pdf_jam_data_long_byjam = pdf_jam_data_long.sort_values(["prd_jam", "team_number"])
    pdf_jambools = pdf_jam_data_long_byjam[["StarPass", "Lost", "Lead", "Calloff", "NoInitial"]]

    # set letter codes for each column
    pdf_jambools = pdf_jambools.rename(columns={"Lost": "lOst"})
    column_lettercode_map = {
        "StarPass": "SP",
        "lOst": "O",
        "Lead": "L",
        "Calloff": "C",
        "NoInitial": "NI"
    }

    team_color_map = {derby_game.team_1_name: 1,
                      derby_game.team_2_name: 2}
    team_colors = [team_color_map[team] for team in pdf_jam_data_long_byjam.team]
    jamboolint_dict = {}
    for col in pdf_jambools.columns:
        jamboolint_dict[col] = [team_color if abool else 0
                                for team_color, abool in zip(*[team_colors, pdf_jambools[col]])]
    team_color_palette = make_team_color_palette(derby_game)
    colors = [(1,1,1), team_color_palette[0], team_color_palette[1]]
    pdf_jambool_heatmap = pd.DataFrame(jamboolint_dict)
    sns.heatmap(pdf_jambool_heatmap, ax=ax, cbar=False, cmap=sns.color_palette(colors, as_cmap=True))
    # add lines separating jams
    for i in range(len(pdf_jambools)):
        if i % 2 == 0:
            pdf_linedata = {
                "x": [0, len(pdf_jambools.columns)],
                "y": [i, i],
            }
            sns.lineplot(x="x", y="y", data=pdf_linedata, color="black", ax=ax)
    # add letter indicators of attributes
    for i in range(len(pdf_jambools.columns)):
        col = pdf_jambools.columns[i]
        vals = list(pdf_jambools[col])
        for j in range(len(vals)):
            if vals[j]:
                ax.text(i + .5, j + .5, column_lettercode_map[col], size="small",
                        horizontalalignment="center",
                        verticalalignment="center")
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_xticks([x+.5 for x in range(len(pdf_jambool_heatmap.columns))])
    ax.set_yticklabels([])
    ax.set_xticklabels(pdf_jambool_heatmap.columns, rotation=90)
    ax.set_title("Attributes")

    ax = ax1
    sns.barplot(x="JamScore", y="prd_jam", data=pdf_jam_data_long, hue="team", ax=ax,
                palette=team_color_palette)
    n_period_jams = len(set(pdf_jam_data_long.prd_jam))
    ax.legend()
    # add lines separating jams
    highscore = ax.get_xlim()[1]
    for i in range(n_period_jams):
        pdf_linedata = {
            "x": [0, highscore],
            "y": [i + 0.5, i + 0.5],
        }
        sns.lineplot(x="x", y="y", data=pdf_linedata, color="black", ax=ax)
    ax.set_xlim((0, highscore))
    ax.set_ylim((n_period_jams - 0.5, -0.5))
    title = "Points per jam by team"
    if period is not None:
        title = title + f" (period {period})"
    ax.set_title(title)
    ax.set_xlabel("Points")
    ax.set_ylabel(None)

    f.set_size_inches(8, 11)
    f.tight_layout()

    logger.debug("Done plotting.")
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

    team_color_palette = make_team_color_palette(derby_game)

    f, ax = plt.subplots()
    sns.lineplot(x="prd_jam", y="TotalScore",
                 data=pdf_jam_data_long[pdf_jam_data_long.team == team_1], label=team_1,
                 estimator=None, color=team_color_palette[0])
    sns.lineplot(x="prd_jam", y="TotalScore",
                 data=pdf_jam_data_long[pdf_jam_data_long.team == team_2], label=team_2,
                 estimator=None, color=team_color_palette[1])

    # determine break betwen periods, if any. Draw a line there.
    n_periods = len(set(derby_game.pdf_jams_data.PeriodNumber))
    if n_periods == 2:
        n_jams_period1 = sum(derby_game.pdf_jams_data.PeriodNumber == 1)
        sns.lineplot(x=[n_jams_period1 - 0.5, n_jams_period1 - 0.5],
                     y=[0, max(pdf_jam_data_long.TotalScore)])

    for tick in ax.get_xticklabels():
        tick.set_rotation(90)
    ax.set_title("Cumulative score by jam")
    ax.set_xlabel("Period:Jam")
    ax.set_ylabel("Score")

    f.set_size_inches(11, 8)
    f.tight_layout()

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
    """violin plot time to initial

    Args:
        derby_game (DerbyGame): derby game

    # TODO: currently, ordering teams by team name in this plot. Order by team number
    for consistency.

    Returns:
        Figure: violin plot
    """
    team_color_palette = make_team_color_palette(derby_game)
    pdf_jams_with_lead = derby_game.pdf_jams_data[derby_game.pdf_jams_data.Lead_1 |
                                                  derby_game.pdf_jams_data.Lead_2].copy()
    pdf_jams_data_long = derby_game.build_jams_dataframe_long()
    pdf_jams_with_lead["Team with Lead"] = [derby_game.team_1_name if team1_has_lead
                                            else derby_game.team_2_name
                                            for team1_has_lead in pdf_jams_with_lead.Lead_1]
    f, axes = plt.subplots(1, 3)

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
        sns.barplot(y="prd_jam", x="Team with Lead", data=pdf_for_plot_all, ax=ax,
                    color="gray")
    if len(pdf_for_plot_called_or_lost) > 0:
        sns.barplot(y="prd_jam", x="Team with Lead", data=pdf_for_plot_called_or_lost, ax=ax,
                    palette=team_color_palette)
    if len(pdf_for_plot_lost) > 0:
        sns.barplot(y="prd_jam", x="Team with Lead",
                    data=pdf_for_plot_lost, ax=ax, color="black")

    ax.set_ylabel("Jams")
    ax.set_title("Jams with Lead\n(black=lost, gray=not called)")

    ax = axes[1]
    pdf_plot = pdf_jams_data_long.sort_values("team").rename(columns={
        "team": "Team"
    })
    sns.violinplot(y="first_scoring_pass_durations", x="Team",
                   data=pdf_plot, cut=0, ax=ax,
                   inner="stick", palette=team_color_palette)
    ax.set_ylabel("Time to Initial (s)")
    ax.set_title("Time to Initial per jam")

    ax = axes[2]
    colors = [team_color_palette[0] if lead_team == 1
              else team_color_palette[1] if lead_team == 2
              else '#888888'
              for lead_team in derby_game.pdf_jams_data.team_with_lead]
    sns.scatterplot(data=derby_game.pdf_jams_data,
                    x="first_scoring_pass_durations_1",
                    y="first_scoring_pass_durations_2",
                    color=colors, ax=ax)
    max_tti_time = max([
        max(derby_game.pdf_jams_data.first_scoring_pass_durations_1),
        max(derby_game.pdf_jams_data.first_scoring_pass_durations_2)])
    # 1:1 line
    sns.lineplot(x="x", y="y", data=pd.DataFrame({
        "x": [0, max_tti_time],
        "y": [0, max_tti_time]}),
        ax=ax)
    ax.set_xlabel(derby_game.team_1_name)
    ax.set_ylabel(derby_game.team_2_name)
    ax.set_title("Time to Initial,\nTeam vs. Team (color = lead)")

    f.set_size_inches(15, 6)
    f.tight_layout()

    return f


def plot_team_penalty_counts(derby_game: DerbyGame) -> Figure:
    """barplot team penalty counts

    Args:
        derby_game (DerbyGame): a derby game

    Returns:
        Figure: barplot
    """
    team_color_palette = make_team_color_palette(derby_game)
    team_plot_pdfs = []
    for team in [derby_game.team_1_name, derby_game.team_2_name]:
        pdf_team_penalties = derby_game.pdf_penalties[
            derby_game.pdf_penalties.team == team
        ]
        pdf_team_penalty_counts = (pdf_team_penalties
            .penalty_name.value_counts().reset_index().rename(
                columns={"index": "Penalty", "penalty_name": "Count"}))
        pdf_team_penalty_counts["team"] = team
        team_plot_pdfs.append(pdf_team_penalty_counts)
    
    pdf_penalty_counts = pd.concat(team_plot_pdfs)
    pdf_penalty_counts = pdf_penalty_counts.sort_values("Penalty")
    
    f, ax = plt.subplots()

    sns.barplot(y="Penalty", x="Count", data=pdf_penalty_counts,
                hue="team", ax=ax, palette=team_color_palette)
    ax.set_title(f"Penalty counts") 
    ax.set_ylabel("")

    f.set_size_inches(8, 11)
    f.tight_layout()
    return f
