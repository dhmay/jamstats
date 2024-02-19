__author__ = "Damon May"

from matplotlib.figure import Figure
from typing import Dict
import seaborn as sns
from jamstats.data.game_data import DerbyGame
import logging
from matplotlib import pyplot as plt
import pandas as pd
from jamstats.plots.plot_util import (
    make_team_color_palette,
    wordwrap_x_labels
)
from jamstats.plots.plot_util import DerbyPlot
import matplotlib.patches as mpatches


logger = logging.Logger(__name__)


class JammersByTeamPlot(DerbyPlot):
    name: str = "Jammers by Team"
    description: str = "Multiple views on jammers by team"
    section = "Advanced Plots"

    def plot(self, derby_game: DerbyGame) -> Figure:
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
                    }), hue="team", legend=False,
                    ax=ax, palette=team_color_palette)
        # word-wrap too-long team names
        wordwrap_x_labels(ax)
        ax.set_title("Jammers per team")

        ax = axes[1]
        sns.violinplot(x="team", y="jam_count", data=pdf_jammer_jamcounts, cut=0, ax=ax,
                       hue="team", legend=False,
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


class PerJamDataOnePeriodPlot(DerbyPlot):
    name: str = "Per-Jam Data, One Period"
    description: str = "Everything about every jam in a period"
    section = "Advanced Plots"

    def __init__(self, period: int, anonymize_names: bool = False) -> None:
        super(PerJamDataOnePeriodPlot, self).__init__(anonymize_names=anonymize_names)
        self.period = period

    def plot(self, derby_game: DerbyGame) -> Figure:
        """Given a long-format jam dataframe, visualize lead and scores per jam

        Args:
            derby_game (DerbyGame): a derby game
            period (int): Period to plot. If not provided, plot both

        Returns:
            Figure: figure
        """
        logger.debug("Plotting jam lead and scores...")
        pdf_jam_data_long = derby_game.build_jams_dataframe_long()
        logger.debug(f"Restricting to period {self.period}")
        pdf_jam_data_long = pdf_jam_data_long[pdf_jam_data_long.PeriodNumber == self.period]

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
        title = title + f" (period {self.period})"
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


class PerJamDataPeriod1Plot(PerJamDataOnePeriodPlot):
    name: str = "Period 1 Jam Data"
    description: str = "Jam data for period 1"
    def __init__(self, anonymize_names: bool = False) -> None:
        super(PerJamDataPeriod1Plot, self).__init__(1, anonymize_names=anonymize_names)


class PerJamDataPeriod2Plot(PerJamDataOnePeriodPlot):
    name: str = "Period 2 Jam Data"
    description: str = "Jam data for period 2"
    def __init__(self, anonymize_names: bool = False) -> None:
        super(PerJamDataPeriod2Plot, self).__init__(2, anonymize_names=anonymize_names)


class TimeToInitialPassPlot(DerbyPlot):
    name: str = "Time to Initial"
    description: str = "Violin plots and scatterplots comparing time to initial pass per team"
    section = "Advanced Plots"

    def plot(self, derby_game: DerbyGame) -> Figure:    
        """violin plot and scatterplot time to initial

        Args:
            derby_game (DerbyGame): derby game

        # TODO: currently, ordering teams by team name in this plot. Order by team number for consistency.

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
        
        f, axes = plt.subplots(1, 2)

        ax = axes[0]
        pdf_plot = pdf_jams_data_long.sort_values("team_number").rename(columns={
            "team": "Team"
        })
        if len(pdf_plot) > 0:
            sns.violinplot(y="first_scoring_pass_durations", x="Team",
                        data=pdf_plot, cut=0, ax=ax, hue="Team", legend=False,
                        inner="stick", palette=team_color_palette)
        ax.set_ylabel("Time to Initial (s)")
        ax.set_title("Time to Initial per jam")
        # word-wrap too-long team names
        wordwrap_x_labels(ax)

        ax = axes[1]
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

        f.set_size_inches(12, 6)
        f.tight_layout()

        return f
