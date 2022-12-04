__author__ = "Damon May"

from typing import Dict
import pandas as pd


def get_team_number_name_map(jams_metadata_dict: Dict[str, str]) -> Dict[int, str]:
    """Convenience method to extract a map from team number to team name
    from the jams metadata dictionary.

    Args:
        jams_metadata_dict (Dict[str, str]): _description_

    Returns:
        Dict[int, str]: _description_
    """
    team_1 = jams_metadata_dict["team_1"]
    team_2 = jams_metadata_dict["team_2"]

    team_number_name_map = {
        1: team_1,
        2: team_2
    }
    return team_number_name_map


def extract_game_summary(pdf_jams_data: pd.DataFrame) -> pd.DataFrame:
    """Build a gross game-summary dataframe

    Args:
        pdf_jams_data (pd.DataFrame): jams data

    Returns:
        pd.DataFrame: game summary dataframe
    """
    n_periods = len(set([x for x in pdf_jams_data.PeriodNumber if x > 0]))
    n_jams = len(pdf_jams_data.prd_jam)  # is this correct? Is jam 0 a real jam?
    period_duration_seconds = max(pdf_jams_data.jam_endtime_seconds)
    period_duration_minutes = period_duration_seconds / 60
    final_score_team_1 = max(pdf_jams_data.TotalScore_1)
    final_score_team_2 = max(pdf_jams_data.TotalScore_2)

    gross_summary_dict = {
        "Periods": n_periods,
        "Jams": n_jams,
        "Minutes": period_duration_minutes,
        "Team 1 Final Score": final_score_team_1,
        "Team 2 Final Score": final_score_team_2,
    }

    pdf_game_summary = pd.DataFrame({
        "Statistic": gross_summary_dict.keys(),
        "Value": gross_summary_dict.values()})

    return pdf_game_summary


def extract_game_teams_summary(pdf_jams_data: pd.DataFrame) -> pd.DataFrame:
    """Build a summary dataframe with per-team data

    Args:
        pdf_jams_data (pd.DataFrame): jams data

    Returns:
        pd.DataFrame: teams summary dataframe
    """
    cols_to_sum = ["Calloff", "Injury", "JamScore", "Lead", "Lost", "NoInitial",
               "StarPass", "n_scoring_trips"]
    teams_summary_dict = {"Team": ["Team1", "Team2", "both"]}
    for col in cols_to_sum:
        sum_1 = sum(pdf_jams_data[col + "_1"])
        sum_2 = sum(pdf_jams_data[col + "_2"])
        sum_both = sum_1 + sum_2
        teams_summary_dict[col] = [sum_1, sum_2, sum_both]
        
    pdf_game_teams_summary = pd.DataFrame(teams_summary_dict)
    return pdf_game_teams_summary


def build_teams_together_dataframe(pdf_jams_data: pd.DataFrame,
                                   jams_metadata_dict: Dict[str, str]) -> pd.DataFrame:
    """Transform pdf_jams_data into a dataframe with one row per (jam, team)

    Args:
        pdf_jams_data (pd.DataFrame): jams data
        jams_metadata_dict (Dict[str, str]): 

    Returns:
        pd.DataFrame: dataframe with one row per (jam, team)
    """
    team_number_name_map = get_team_number_name_map(jams_metadata_dict)
    cols_repeated_byteam = [x for x in pdf_jams_data.columns
                        if x.endswith("_1")]
    cols_repeated_byteam = [x[:-2] for x in cols_repeated_byteam]
    pdf_repeatedcols_team1 = (pdf_jams_data[["prd_jam"] +
                              [x + "_1" for x in cols_repeated_byteam]])
    pdf_repeatedcols_team1["team"] = team_number_name_map[1]
    pdf_repeatedcols_team1 = pdf_repeatedcols_team1.rename(
        columns={x + "_1": x for x in cols_repeated_byteam})
    pdf_repeatedcols_team2 = pdf_jams_data[["prd_jam"] + [x + "_2" for x in cols_repeated_byteam]]
    pdf_repeatedcols_team2["team"] = team_number_name_map[2]
    pdf_repeatedcols_team2 = pdf_repeatedcols_team2.rename(columns={x + "_2": x for x in cols_repeated_byteam})

    pdf_jam_data_long = pd.concat([pdf_repeatedcols_team1, pdf_repeatedcols_team2])
    return pdf_jam_data_long