__author__ = "Damon May"

import pandas as pd
from matplotlib.figure import Figure
from typing import List, Optional
import seaborn as sns
from matplotlib import pyplot as plt
from jamstats.data.game_data import DerbyGame
import logging
from jamstats.plots.plot_util import (
    make_team_color_palette,
    wordwrap_x_labels
)
import matplotlib.patches as mpatches
from jamstats.plots.plot_util import convert_millis_to_min_sec_str
from jamstats.plots.plot_util import build_anonymizer_map

from pandas.api.types import CategoricalDtype




logger = logging.Logger(__name__)


# ordered dtype so we can sort easily by penalty status
PENALTYSTATUS_ORDER_DTYPE = cat_size_order = CategoricalDtype(
    ['Serving', 'Not Yet', 'Served'], 
    ordered=True
)

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


def plot_roster_with_jammerpivot(derby_game: DerbyGame) -> Figure:
    """Make a table figure out of the team roster dataframe,
    suitable for writing to a .pdf

    Args:
        derby_game (DerbyGame): a derby game
        team_name (str): team name

    Returns:
        Figure: table figure
    """
    pdf_team_roster1 = format_team_roster_fordisplay(derby_game, derby_game.team_1_name,
                                                     show_jammers_and_pivots=True)
    pdf_team_roster1.index = range(len(pdf_team_roster1))
    pdf_team_roster2 = format_team_roster_fordisplay(derby_game, derby_game.team_2_name,
                                                     show_jammers_and_pivots=True)
    pdf_team_roster2.index = range(len(pdf_team_roster2))

    pdf_bothteams_roster = pd.concat([pdf_team_roster1, pdf_team_roster2], axis=1)
    f = plt.figure(figsize=(8, 10))
    ax = plt.subplot(111)
    ax.axis('off')
    ax.table(cellText=pdf_bothteams_roster.values,
             colLabels=pdf_bothteams_roster.columns, bbox=[0,0,1,1])
    return f

def format_team_roster_fordisplay(derby_game: DerbyGame, team_name: str,
                                  anonymize_names: str = False,
                                  show_jammers_and_pivots: bool = False) -> str:
    """Format team roster for display

    Args:
        derby_game (DerbyGame): derby game
        team_name (str): team name

    Returns:
        str: formatted team roster
    """
    pdf_team_roster = derby_game.pdf_roster[derby_game.pdf_roster.team == team_name]
    roster_cols = ["RosterNumber", "Name"]
    roster_has_pronouns = "Pronouns" in pdf_team_roster.columns
    if roster_has_pronouns:
        roster_cols.append("Pronouns")
    pdf_team_roster = pdf_team_roster[roster_cols]
    pdf_team_roster = pdf_team_roster.rename(columns={"Name": "Name", "RosterNumber": "Number"})
    if anonymize_names:
        name_dict = build_anonymizer_map(set(pdf_team_roster.Name))
        pdf_team_roster["Name"] = [name_dict[skater] for skater in pdf_team_roster.Name]  
    pdf_team_roster = pdf_team_roster.sort_values("Number")
    pdf_team_roster[f"{team_name} Skater"] = pdf_team_roster["Number"].astype(str) + " " + pdf_team_roster["Name"]
    if roster_has_pronouns:
        pdf_team_roster[f"{team_name} Skater"] = (
            pdf_team_roster[f"{team_name} Skater"] + " (" + pdf_team_roster["Pronouns"] + ")")
        pdf_team_roster = pdf_team_roster.drop(columns=["Pronouns"])

    team_number = 1 if team_name == derby_game.team_1_name else 2
    if show_jammers_and_pivots:
        pdf_jammer_counts = pd.DataFrame(derby_game.pdf_jams_data[f"jammer_number_{team_number}"].value_counts())
        pdf_jammer_counts = pdf_jammer_counts.rename(columns={f"jammer_number_{team_number}": "Jammed"})
        pdf_jammer_counts["Number"] = pdf_jammer_counts.index
        pdf_team_roster = pdf_team_roster.merge(pdf_jammer_counts, on="Number", how="left")
        pdf_team_roster["Jammed"] = pdf_team_roster["Jammed"].fillna(0).astype(int)
        # now do pivot
        pdf_pivot_counts = pd.DataFrame(derby_game.pdf_jams_data[f"pivot_number_{team_number}"].value_counts())
        pdf_pivot_counts = pdf_pivot_counts.rename(columns={f"pivot_number_{team_number}": "Pivoted"})
        pdf_pivot_counts["Number"] = pdf_pivot_counts.index
        pdf_team_roster = pdf_team_roster.merge(pdf_pivot_counts, on="Number", how="left")
        pdf_team_roster["Pivoted"] = pdf_team_roster["Pivoted"].fillna(0).astype(int)

    pdf_team_roster = pdf_team_roster.drop(columns=["Number", "Name"])


    return pdf_team_roster





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
            sns.lineplot(x="x", y="y", data=pdf_linedata, color="black", ax=ax, size=0.5)

    # add letter indicators of attributes and lines separating attributes
    for i in range(len(pdf_jambools.columns)):
        col = pdf_jambools.columns[i]
        vals = list(pdf_jambools[col])
        for j in range(len(vals)):
            if vals[j]:
                ax.text(i + .5, j + .5, column_lettercode_map[col], size="small",
                        horizontalalignment="center",
                        verticalalignment="center")
        # add line
        if 0 < i < len(pdf_jambools.columns):
            sns.lineplot(x="x", y="y", data=pd.DataFrame({
                "x": [i, i],
                "y": [0, len(pdf_jambools)]
            }), ax=ax, color="black")
    
    # add column labels up top
    for i in range(len(pdf_jambools.columns)):
        ax.text(i + 0.25, -.5, pdf_jambools.columns[i], rotation=90, size="large")

    ax.get_legend().remove()
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_xticks([x+.5 for x in range(len(pdf_jambool_heatmap.columns))])
    ax.set_yticklabels([])
    ax.set_xticklabels([])

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
        sns.lineplot(x="x", y="y", data=pdf_linedata, color="black", ax=ax, size=0.5)

    # add lines indicating lead
    for team_name in [derby_game.team_1_name, derby_game.team_2_name]:
        pdf_jamdata_thisteam = pdf_jam_data_long[pdf_jam_data_long.team == team_name].sort_values(
            "prd_jam")
        lead_indicators = list(pdf_jamdata_thisteam.Lead)
        scores = list(pdf_jamdata_thisteam.JamScore)
        for i in range(n_period_jams):
            if lead_indicators[i] and (scores[i] > 0):
                y_val = i - 0.22 if team_name == derby_game.team_1_name else i + 0.18
                sns.lineplot(x="x", y="y", data=pd.DataFrame({
                    "x": [0.23, scores[i] - 0.28],
                    "y": [y_val, y_val]
                }), color="#FFFFFF55", size=0.5)

    ax.set_xlim((0, highscore))
    ax.set_ylim((n_period_jams - 0.5, -0.5))
    title = "Points per jam by team"
    if period is not None:
        title = title + f" (period {period})"
    title = title + "\n(line indicates lead)"
    ax.set_title(title)
    ax.set_xlabel(None)
    ax.set_ylabel(None)

    # legend got screwed up by lines. Rebuild the legend
    patch_team_1 = mpatches.Patch(color=team_color_palette[0], label=derby_game.team_1_name)
    patch_team_2 = mpatches.Patch(color=team_color_palette[1], label=derby_game.team_2_name)
    ax.legend(handles=[patch_team_1, patch_team_2])

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
    pdf_jam_data_long = derby_game.build_jams_dataframe_long()

    team_color_palette = make_team_color_palette(derby_game)

    f, ax = plt.subplots()
    sns.lineplot(x="prd_jam", y="TotalScore",
                 data=pdf_jam_data_long[pdf_jam_data_long.team == derby_game.team_1_name],
                                        label=derby_game.team_1_name,
                 estimator=None, color=team_color_palette[0])
    sns.lineplot(x="prd_jam", y="TotalScore",
                 data=pdf_jam_data_long[pdf_jam_data_long.team == derby_game.team_2_name],
                                        label=derby_game.team_2_name,
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
    # sort by team number, to match up with palette
    pdf_jams_data_long["team_number"] = [1 if team == derby_game.team_1_name
                                         else 2
                                         for team in pdf_jams_data_long.team]
    pdf_jams_with_lead["team_number"] = [1 if team == derby_game.team_1_name
                                         else 2
                                         for team in pdf_jams_with_lead["Team with Lead"]]
    pdf_jams_with_lead = pdf_jams_with_lead.sort_values("team_number")
    
    f, axes = plt.subplots(1, 3)

    ax = axes[0]
    pdf_jams_with_lead["Lost"] = pdf_jams_with_lead.Lost_1 | pdf_jams_with_lead.Lost_2

    pdf_for_plot_all = pdf_jams_with_lead[
        ["Team with Lead", "prd_jam"]].groupby(
            ["Team with Lead"]).agg("count").reset_index()
    pdf_for_plot_lost = pdf_jams_with_lead[pdf_jams_with_lead.Lost][
        ["Team with Lead", "prd_jam"]].groupby(
            ["Team with Lead"]).agg("count").reset_index()
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
    # word-wrap too-long team names
    wordwrap_x_labels(ax)



    ax = axes[1]
    pdf_plot = pdf_jams_data_long.sort_values("team_number").rename(columns={
        "team": "Team"
    })
    if len(pdf_plot) > 0:
        sns.violinplot(y="first_scoring_pass_durations", x="Team",
                    data=pdf_plot, cut=0, ax=ax,
                    inner="stick", palette=team_color_palette)
    ax.set_ylabel("Time to Initial (s)")
    ax.set_title("Time to Initial per jam")
    # word-wrap too-long team names
    wordwrap_x_labels(ax)

    ax = axes[2]
    colors = [team_color_palette[0] if lead_team == 1
              else team_color_palette[1] if lead_team == 2
              else (.5, .5, .5)
              for lead_team in derby_game.pdf_jams_data.team_with_lead]
    if len(derby_game.pdf_jams_data) > 0:
        sns.scatterplot(data=derby_game.pdf_jams_data,
                        x="first_scoring_pass_durations_1",
                        y="first_scoring_pass_durations_2",
                        color=colors,
                        ax=ax)
    max_tti_time = 0
    if len(derby_game.pdf_jams_data) > 0:
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
        pdf_team_penalty_counts.sort_values("Penalty", inplace=True)
        pdf_team_penalty_counts["team_number"] = 1 if team == derby_game.team_1_name else 2
        team_plot_pdfs.append(pdf_team_penalty_counts)

    
    pdf_penalty_counts = pd.concat(team_plot_pdfs)
    # insert zeros
    rows_to_insert = []
    for penalty in set(pdf_penalty_counts.Penalty).difference(set(team_plot_pdfs[0].Penalty)):
        rows_to_insert.append({
            "Penalty": penalty, "team_number": 1, "team": derby_game.team_1_name, "Count": 0
        })
    for penalty in set(pdf_penalty_counts.Penalty).difference(set(team_plot_pdfs[1].Penalty)):
        rows_to_insert.append({
            "Penalty": penalty, "team_number": 2, "team": derby_game.team_2_name, "Count": 0
        })
    pdf_penalty_counts = pd.concat([pdf_penalty_counts,
                    pd.DataFrame(rows_to_insert)])
    pdf_penalty_counts = pdf_penalty_counts.sort_values(["Penalty", "team_number"])

    penalties_inorder = sorted(list(set(pdf_penalty_counts.Penalty)))
    print(pdf_penalty_counts)
    
    f, ax = plt.subplots()

    if len(pdf_penalty_counts) > 0:
        sns.barplot(y="Penalty", x="Count", data=pdf_penalty_counts,
                    hue="team", ax=ax, palette=team_color_palette)
        for i, row in pdf_penalty_counts.iterrows():
            offset = -.2 if row["team_number"] == 1 else .2
            ax.text(.5, penalties_inorder.index(row["Penalty"]) + offset,
                    row["Count"], size="small",
                    horizontalalignment="center",
                    verticalalignment="center")
    ax.set_title(f"Penalty counts") 
    ax.set_ylabel("")

    # add lines separating penalties
    for i in range(len(set(pdf_penalty_counts.Penalty)) - 1):
        sns.lineplot(x="x", y="y", data=pd.DataFrame({
            "x": [0, max(pdf_penalty_counts.Count)],
            "y": [i + 0.5, i + 0.5]
        }), color="black", ax=ax, size=0.5)

    # legend got screwed up by lines. Rebuild the legend
    patch_team_1 = mpatches.Patch(color=team_color_palette[0], label=derby_game.team_1_name)
    patch_team_2 = mpatches.Patch(color=team_color_palette[1], label=derby_game.team_2_name)
    ax.legend(handles=[patch_team_1, patch_team_2])
    ax.set_ylabel("")

    f.set_size_inches(8, 11)
    f.tight_layout()
    return f
