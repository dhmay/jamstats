__author__ = "Damon May"

import pandas as pd
from matplotlib.figure import Figure
from typing import List
import seaborn as sns
from matplotlib import pyplot as plt
from jamstats.data.game_data import DerbyGame
import logging
from jamstats.plots.plot_util import (
    make_team_color_palette,
    wordwrap_x_labels
)
import matplotlib.patches as mpatches
from matplotlib.pyplot import Figure
from matplotlib import gridspec

from jamstats.plots.plot_util import build_anonymizer_map, DerbyPlot
import traceback


logger = logging.Logger(__name__)


class JammerStatsPlotOneTeam(DerbyPlot):
    name = "JammerStatsPlotOneTeam"
    description = "Jammer stats for one team"
    section = "Basic Plots"

    def __init__(self, team_number: int, anonymize_names: bool = False) -> None:
        super(JammerStatsPlotOneTeam, self).__init__(anonymize_names=anonymize_names)
        self.team_number = team_number

    def plot(self, derby_game: DerbyGame) -> Figure:
        """Plot jammer stats for one team's jammers

        Args:
            derby_game (DerbyGame): derby game
            team_number (int): team number
            anonymize_names (bool): anonymize skater names

        Returns:
            Figure: figure
        """
        team_name = derby_game.team_1_name if self.team_number == 1 else derby_game.team_2_name
        pdf_jammer_data = derby_game.build_team_jammersummary_df(self.team_number)

        if self.anonymize_names:
            logger.debug("Anonymizing skater names.")
            name_dict = build_anonymizer_map(set(pdf_jammer_data.Jammer))
            pdf_jammer_data["Jammer"] = [name_dict[jammer] for jammer in pdf_jammer_data.Jammer]

        pdf_jammer_data = pdf_jammer_data.sort_values(["Jams", "Total Score"],
                                                      ascending=False)

        f, (ax0, ax1, ax2, ax3, ax4) = plt.subplots(1, 5)

        # build a palette
        n_jammers = len(set(pdf_jammer_data.Jammer))
        mypalette = sns.color_palette("rainbow", n_colors=n_jammers)

        ax = ax0
        sns.barplot(y="Jammer", x="Jams", hue="Jammer", legend=False,
                    data=pdf_jammer_data, ax=ax, palette=mypalette)
        ax.set_ylabel("")

        ax = ax1
        sns.barplot(y="Jammer", x="Total Score", hue="Jammer", legend=False,
                    data=pdf_jammer_data, ax=ax, palette=mypalette)
        ax.set_yticks([])
        ax.set_ylabel("")

        ax = ax2
        sns.barplot(y="Jammer", x="Mean Net Points", hue="Jammer", legend=False,
                data=pdf_jammer_data, ax=ax, palette=mypalette)
        ax.set_xlabel("Mean Net Points/Jam\n(own - opposing)")
        ax.set_yticks([])
        ax.set_ylabel("")

        ax = ax3
        sns.barplot(y="Jammer", x="Proportion Lead", hue="Jammer", legend=False,
                    data=pdf_jammer_data, ax=ax, palette=mypalette)
        ax.set_xlim(0,1)
        ax.set_yticks([])
        ax.set_ylabel("")

        ax = ax4
        sns.barplot(y="Jammer", x="Mean Time to Initial", hue="Jammer", legend=False,
                    data=pdf_jammer_data, ax=ax, palette=mypalette)
        ax.set_yticks([])
        ax.set_ylabel("")

        f.set_size_inches(16, min(2 + len(pdf_jammer_data), 11))
        f.suptitle(f"Jammer Stats: {team_name}")
        f.tight_layout()

        return f


class JammerStatsPlotTeam1(JammerStatsPlotOneTeam):
    name: str = "Team 1 Jammers"
    description: str = "Jammer stats for team 1"
    def __init__(self, anonymize_names: bool = False) -> None:
        super(JammerStatsPlotTeam1, self).__init__(1, anonymize_names=anonymize_names)

class JammerStatsPlotTeam2(JammerStatsPlotOneTeam):
    name: str = "Team 2 Jammers"
    description: str = "Jammer stats for team 2"
    def __init__(self, anonymize_names: bool = False) -> None:
        super(JammerStatsPlotTeam2, self).__init__(2, anonymize_names=anonymize_names)



class CumScoreByJamPlot(DerbyPlot):
    name: str = "Score by Jam"
    description: str = "Cumulative game score by jam"
    section = "Basic Plots"

    def plot(self, derby_game: DerbyGame) -> Figure:
        """Plot cumulative score by jam
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


class SimpleLeadSummaryPlot(DerbyPlot):
    name: str = "Lead Summary"
    description: str = "Barplot summarizing lead, loss and calloffs"
    section = "Basic Plots"

    def plot(self, derby_game: DerbyGame) -> Figure:
        """Barplot of lead

        Args:
            derby_game (DerbyGame): derby game

        Returns:
            Figure: barplot
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
        
        f, ax = plt.subplots()

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
            sns.barplot(y="prd_jam", x="Team with Lead", hue="Team with Lead", legend=False,
                        data=pdf_for_plot_called_or_lost, ax=ax,
                        palette=team_color_palette)
        if len(pdf_for_plot_lost) > 0:
            sns.barplot(y="prd_jam", x="Team with Lead", hue="Team with Lead", legend=False,
                        data=pdf_for_plot_lost, ax=ax, palette='dark:black')

        ax.set_ylabel("Jams")
        ax.set_title("Jams with Lead\n(black=lost, gray=not called)")
        # word-wrap too-long team names
        wordwrap_x_labels(ax)

        f.set_size_inches(6, 6)

        return f


class PenaltyCountsPlotByTeam(DerbyPlot):
    name: str = "Team Penalties"
    description: str = "Barplots counting each penalty type by team"
    section = "Basic Plots"

    def plot(self, derby_game: DerbyGame) -> Figure:
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
            pdf_team_penalty_counts = pdf_team_penalties.penalty_name.value_counts().reset_index()
            pdf_team_penalty_counts.columns = ["Penalty", "Count"]
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


class SkaterStatsPlotOneTeam(DerbyPlot):
    name: str = "Team Skater Stats"
    description: str = "Plots of penalties per skater"
    section = "Basic Plots"

    def __init__(self, team_number: int, anonymize_names: bool = False) -> None:
        super(SkaterStatsPlotOneTeam, self).__init__(anonymize_names=anonymize_names)
        self.team_number = team_number

    def plot(self, derby_game: DerbyGame) -> Figure:
        """Plot skater stats for one team's skaters

        Args:
            derby_game (DerbyGame): derby game
            team_number (int): team number
            anonymize_names (bool): anonymize skater names

        Returns:
            Figure: figure
        """
        team_name = derby_game.team_1_name if self.team_number == 1 else derby_game.team_2_name
        skater_lists = derby_game.pdf_jams_data[f"Skaters_{self.team_number}"]
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
        pdf_skater_data = pdf_skater_data[pdf_skater_data.Skater.notnull()]

        if self.anonymize_names:
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
            if self.anonymize_names:
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
            # There's probably some more-pandas-y way to do this. I tried and failed.
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
            pdf_skaters_inorder = pd.DataFrame({
                "Skater": pdf_penalty_plot.index})

            # add penalties per jam
            pdf_skater_data["penalty_count"] = [skater_penaltycount_map[skater]
                                                if skater in skater_penaltycount_map else 0
                                                for skater in pdf_skater_data.Skater]
            # sort skater data, too
            # Fix Issue #177: before, I had been sorting by skater penalty count,
            # but this led to mistakes in the specific penalties assigned to each skater.
            pdf_skater_data = pdf_skaters_inorder.merge(pdf_skater_data)
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


class SkaterStatsPlotTeam1(SkaterStatsPlotOneTeam):
    name: str = "Team 1 Skaters"
    description: str = "Skaters stats for team 1"
    def __init__(self, anonymize_names: bool = False) -> None:
        super(SkaterStatsPlotTeam1, self).__init__(1, anonymize_names=anonymize_names)


class SkaterStatsPlotTeam2(SkaterStatsPlotOneTeam):
    name: str = "Team 2 Skaters"
    description: str = "Skaters stats for team 2"
    def __init__(self, anonymize_names: bool = False) -> None:
        super(SkaterStatsPlotTeam2, self).__init__(2, anonymize_names=anonymize_names)
