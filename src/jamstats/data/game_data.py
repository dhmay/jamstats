__author__ = "Damon May"

from typing import Dict
import pandas as pd
import time
from datetime import timedelta
import seaborn as sns
import logging
from matplotlib.colors import is_color_like


logger = logging.Logger(__name__)

class DerbyGame:
    """Class for storing all the data related to a derby game.
    """
    def __init__(self, pdf_jams_data: pd.DataFrame, game_data_dict: Dict[str, str],
                 pdf_penalties: pd.DataFrame, pdf_team_colors: pd.DataFrame,
                 pdf_roster: pd.DataFrame, pdf_ref_roster: pd.DataFrame,
                 pdf_nso_roster: pd.DataFrame):
        logger.debug("DerbyGame init")
        self.pdf_jams_data = pdf_jams_data
        self.pdf_roster = pdf_roster
        self.pdf_ref_roster = pdf_ref_roster
        self.pdf_nso_roster = pdf_nso_roster
        self.game_data_dict = game_data_dict
        self.team_1_name = game_data_dict["team_1"]
        self.team_2_name = game_data_dict["team_2"]

        logger.debug("Extracting game summary dict")
        self.game_summary_dict = self.extract_game_summary_dict()
        self.game_status = game_data_dict["game_status"]

        self.n_jams = self.game_summary_dict["Jams"]
        self.pdf_penalties = pdf_penalties
        self.pdf_team_colors = pdf_team_colors

        logger.debug("Handling team colors")
        self.team_color_1 = sns.color_palette()[0]
        self.team_color_2 = sns.color_palette()[1]
        if pdf_team_colors is not None:
            try:
                team_color_dict = dict(zip(pdf_team_colors.team, pdf_team_colors.color))
                if "1" in team_color_dict and "2" in team_color_dict:
                    # v5 format, team numbers
                    self.team_color_1 = team_color_dict["1"]
                    self.team_color_2 = team_color_dict["2"]
                else:
                    # v4 format, team names
                    self.team_color_1 = team_color_dict[self.team_1_name]
                    self.team_color_2 = team_color_dict[self.team_2_name]
                # try to make a palette with the team colors. If this fails, use the default
                sns.color_palette([self.team_color_1, self.team_color_2])
            except Exception as e:
                logger.debug("Failed to find teams in color definitions. Using default colors.")
                self.team_color_1 = sns.color_palette()[0]
                self.team_color_2 = sns.color_palette()[1]

    def anonymize_team_names(self) -> None:
        """Replace team names with "Team 1" and "Team 2"
        """
        self.game_data_dict["team_1"] = "Team 1"
        self.game_data_dict["team_2"] = "Team 2"
        name_replace_dict = {
            self.team_1_name: "Team 1",
            self.team_2_name: "Team 2",
        }
        self.pdf_jams_data = self.pdf_jams_data.replace(name_replace_dict)
        self.pdf_penalties = self.pdf_penalties.replace(name_replace_dict)
        self.pdf_team_colors = self.pdf_team_colors.replace(name_replace_dict)
        self.team_1_name = "Team 1"
        self.team_2_name = "Team 2"


    def set_team_color_1(self, acolor: str) -> None:
        if not is_color_like(acolor):
            raise ValueError(f"Invalid color specified: {acolor}")
        self.team_color_1 = acolor

    def set_team_color_2(self, acolor: str) -> None:
        if not is_color_like(acolor):
            raise ValueError(f"Invalid color specified: {acolor}")
        self.team_color_2 = acolor

    def extract_game_summary(self) -> pd.DataFrame:
        """Build a gross game-summary dataframe

        Returns:
            pd.DataFrame: game summary dataframe
        """
        gross_summary_dict = self.extract_game_summary_dict()
        pdf_game_summary = pd.DataFrame({
            "Statistic": gross_summary_dict.keys(),
            "Value": [str(x) for x in gross_summary_dict.values()]})

        return pdf_game_summary

    def extract_game_summary_dict(self) -> pd.DataFrame:
        """Build a gross game-summary dictionary

        Returns:
            pd.DataFrame: game summary dataframe
        """
        logger.debug("extract_game_summary_dict 1")
        n_periods = len(set([x for x in self.pdf_jams_data.PeriodNumber if x > 0]))
        logger.debug(f"Periods: {n_periods}")

        n_jams = len(self.pdf_jams_data.prd_jam)  # is this correct? Is jam 0 a real jam?
        logger.debug(f"Jams: {n_jams}")

        game_duration_s = 0
        for period in sorted(list(set(self.pdf_jams_data.PeriodNumber))):
            logger.debug(f"Extracting jam data for period {period}")
            pdf_per = self.pdf_jams_data[self.pdf_jams_data.PeriodNumber == period]
            period_duration_s = (max(pdf_per.jam_endtime_seconds) -
                                 min(pdf_per.jam_starttime_seconds))
            logger.debug(f"Period {period} duration: {period_duration_s} seconds")
            game_duration_s += period_duration_s
        logger.debug(f"Game duration: {game_duration_s} seconds")
    
        logger.debug("Calculating scores")
        if len(self.pdf_jams_data) == 0:
            score_team_1 = 0
            score_team_2 = 0
        else:
            score_team_1 = max(self.pdf_jams_data.TotalScore_1)
            score_team_2 = max(self.pdf_jams_data.TotalScore_2)

        # Per @erevrav, injuries accrue to jams, not teams, so the proper quantity
        # to represent at the game level is the number of jams that ended in injury.
        n_jams_with_injury = sum(self.pdf_jams_data.Injury_1 |
                                 self.pdf_jams_data.Injury_2)
        gross_summary_dict = {
            "Game Status": self.game_data_dict["game_status"],
            "Periods": n_periods,
            "Jams": n_jams,
            "Total Game Time": str(timedelta(seconds = int(game_duration_s))),
            f"{self.team_1_name} Score": score_team_1,
            f"{self.team_2_name} Score": score_team_2,
            "Injury Jams": n_jams_with_injury,
            "Scoreboard Version": self.game_data_dict["scoreboard_version"]
        }
        return gross_summary_dict

    def extract_game_teams_summary(self) -> pd.DataFrame:
        """Build a summary dataframe with per-team data

        Args:
            pdf_jams_data (pd.DataFrame): jams data

        Returns:
            pd.DataFrame: teams summary dataframe
        """
        cols_to_sum = ["Lead", "Lost", "Calloff", "NoInitial",
                       "StarPass"]
        teams_summary_dict = {"Team": [self.team_1_name, self.team_2_name]}

        # guarding against empty pdf_jams_data
        score_1 = 0
        score_2 = 0
        if len(self.pdf_jams_data) > 0:
            score_1 = max(self.pdf_jams_data.TotalScore_1)
            score_2 = max(self.pdf_jams_data.TotalScore_2)
        teams_summary_dict["Score"] = [score_1, score_2]

        # add skater counts
        n_skaters_in_jams_1 = len(set().union(*self.pdf_jams_data.Skaters_1))
        n_skaters_in_jams_2 = len(set().union(*self.pdf_jams_data.Skaters_2))

        for col in cols_to_sum:
            sum_1 = sum(self.pdf_jams_data[col + "_1"])
            sum_2 = sum(self.pdf_jams_data[col + "_2"])
            teams_summary_dict[col] = [sum_1, sum_2]

        teams_summary_dict["Skaters played"] = [n_skaters_in_jams_1, n_skaters_in_jams_2]

        if self.pdf_penalties is not None:
            n_penalties_1 = sum(self.pdf_penalties.team == self.team_1_name)
            n_penalties_2 = sum(self.pdf_penalties.team == self.team_2_name)
            teams_summary_dict["Total penalties"] = [n_penalties_1, n_penalties_2]
            
        pdf_game_teams_summary = pd.DataFrame(teams_summary_dict)
        return pdf_game_teams_summary

    def build_jams_dataframe_long(self) -> pd.DataFrame:
        """Transform game data into a dataframe with one row per (jam, team),
        which is more useful for some types of plots.

        Returns:
            pd.DataFrame: dataframe with one row per (jam, team)
        """
        cols_repeated_byteam = [x for x in self.pdf_jams_data.columns
                                if x.endswith("_1")]
        cols_repeated_byteam = [x[:-2] for x in cols_repeated_byteam]
        pdf_repeatedcols_team1 = (
            self.pdf_jams_data[["prd_jam", "PeriodNumber"] +
            [x + "_1" for x in cols_repeated_byteam]].copy())
        pdf_repeatedcols_team1["team"] = self.team_1_name
        pdf_repeatedcols_team1 = pdf_repeatedcols_team1.rename(
            columns={x + "_1": x for x in cols_repeated_byteam})
        pdf_repeatedcols_team2 = self.pdf_jams_data[
            ["prd_jam", "PeriodNumber"] +
            [x + "_2" for x in cols_repeated_byteam]].copy()
        pdf_repeatedcols_team2["team"] = self.team_2_name
        pdf_repeatedcols_team2 = pdf_repeatedcols_team2.rename(
            columns={x + "_2": x for x in cols_repeated_byteam})

        pdf_jam_data_long = pd.concat([pdf_repeatedcols_team1, pdf_repeatedcols_team2])
        return pdf_jam_data_long

    def build_team_jammersummary_df(self, team_number: int):
        """Build a dataframe with data on all the jammers for a team.

        Args:
            team_number (int): Team number
        """
        jammer_col = f"jammer_name_{team_number}"
        jammer_number_col = f"jammer_number_{team_number}"
        jamscore_col = f"jammer_points_{team_number}"
        netpoints_col = f"net_points_{team_number}"
        lead_prop_col = f"Lead_{team_number}"
        lost_col = f"Lost_{team_number}"
        time_to_initial_col = f"first_scoring_pass_durations_{team_number}"

        pdf_jams_data = self.pdf_jams_data.copy()

        # copy the lead column to use it in two ways. Same with score.
        pdf_jams_data["Lead Count"] = pdf_jams_data[lead_prop_col].astype(int)
        # fix up some types that sometimes get wrong
        pdf_jams_data[lost_col] = pdf_jams_data[lost_col].astype(int)
        
        pdf_jammer_data = pdf_jams_data.groupby([jammer_col, jammer_number_col]).agg({
            jamscore_col: "sum",
            netpoints_col: "mean",
            'Number': "count",
            lead_prop_col: "mean",
            "Lead Count": "sum",
            lost_col: "sum",
            time_to_initial_col: "mean"}).reset_index()

        pdf_jammer_data = pdf_jammer_data.rename(columns={
            jammer_col: "Jammer",
            jammer_number_col: "Number",
            jamscore_col: "Total Score",
            netpoints_col: "Mean Net Points",
            lead_prop_col: "Proportion Lead",
            lost_col: "Lost Count",
            "Number": "Jams",
            time_to_initial_col: "Mean Time to Initial",
        })

        # now, make a row for anyone who was a pivot who became jammer via star pass

        pdf_jams_with_star_passes = pdf_jams_data[pdf_jams_data[
            f"StarPass_{team_number}"] == True]
        pivots_who_jammed = list(set(pdf_jams_with_star_passes[f"pivot_name_{team_number}"]))
        jammers_who_only_pivotjammed = [x for x in pivots_who_jammed
                                       if x not in set(pdf_jammer_data.Jammer)]
        logger.debug(f"Team {team_number} jammers who only jammed as pivots: {len(jammers_who_only_pivotjammed)}")
        n_jammers_who_only_pivotjammed = len(jammers_who_only_pivotjammed)
        if n_jammers_who_only_pivotjammed > 0:
            pdf_allpivot_data = self.pdf_jams_data[
                [f"pivot_name_{team_number}", f"pivot_number_{team_number}"]
            ].drop_duplicates()
            pdf_allpivot_data = pdf_allpivot_data.rename(columns={
                f"pivot_name_{team_number}": "Jammer",
                f"pivot_number_{team_number}": "Number"
            })
            pdf_onlypivot_data = pdf_allpivot_data[pdf_allpivot_data["Jammer"].isin(
                jammers_who_only_pivotjammed)].copy()
            for column in [
                "Total Score", "Mean Net Points", "Lead Count", "Proportion Lead", "Lost Count",
                "Jams", "mean_jam_score"
            ]:
                pdf_onlypivot_data[column] = 0
            pdf_onlypivot_data["Mean Time to Initial"] = None
            pdf_jammer_data = pd.concat([pdf_jammer_data, pdf_onlypivot_data])
        
        # now, add score and jam counts for all the pivots who took star passes
        pdf_jams_data_starpassjams = pdf_jams_data[pdf_jams_data[f"StarPass_{team_number}"]]
        pdf_jammer_data["jams_afterstarpass"] =  [
            sum(pdf_jams_data_starpassjams[f"pivot_name_{team_number}"] == aname)
            for aname in pdf_jammer_data.Jammer
        ]
        pdf_jammer_data["Jams"] = pdf_jammer_data["Jams"] + pdf_jammer_data["jams_afterstarpass"]
        pdf_jammer_data = pdf_jammer_data.drop(columns=["jams_afterstarpass"])
        pdf_jammer_data["points_afterstarpass"] = [
            sum(pdf_jams_data_starpassjams[pdf_jams_data_starpassjams[f"pivot_name_{team_number}"] == aname][f"pivot_points_{team_number}"])
            for aname in pdf_jammer_data.Jammer
        ]
        pdf_jammer_data["Total Score"] = pdf_jammer_data["Total Score"] + pdf_jammer_data["points_afterstarpass"]
        pdf_jammer_data = pdf_jammer_data.drop(columns=["points_afterstarpass"])

        return pdf_jammer_data



