__author__ = "Damon May"
"""Methods for turning game JSON into Pandas dataframes
"""

import pandas as pd
from typing import Dict, Any
from jamstats.data.game_data import DerbyGame, DerbyGameFactory

# Columns to keep at the team+jam level
TEAMJAM_SUMMARY_COLUMNS = [
    "Calloff", "Injury", "JamScore", "Lead",
    "Lost", "NoInitial", "StarPass", "TotalScore", "jammer_name", "jammer_number"]


class JsonDerbyGameFactory(DerbyGameFactory):
    """Build DerbyGame objects from JSON
    """
    def __init__(self, game_json: Dict[Any, Any]):
        self.game_json = game_json
        
    def get_derby_game(self) -> DerbyGame:
        """Build the derby game

        Returns:
            DerbyGame: derby game
        """
        pdf_game_state = json_to_game_dataframe(self.game_json)
        game_data_dict = extract_game_data_dict(pdf_game_state)
        pdf_roster = extract_roster(pdf_game_state,
                                    game_data_dict["team_1"],
                                    game_data_dict["team_2"])
        pdf_game_data = extract_jam_data(pdf_game_state, pdf_roster)
        return DerbyGame(pdf_game_data, game_data_dict)


def json_to_game_dataframe(game_json: Dict[Any, Any]) -> pd.DataFrame:
    """Read in the json and turn it into a Pandas DataFrame.
    The json is just a huge, flat dictionary, with structure
    in the key names, separated by ".". Chunk up the key strings
    by ".".

    Args:
        game_json (Dict[Any, Any]): JSON representing a game

    Returns:
        pd.DataFrame: result dataframe
    """
    game_dict = game_json["state"]

    pdf_game_state = pd.DataFrame({
        "key": game_dict.keys(),
        "value": game_dict.values()})
    pdf_game_state["key_chunks"] = [
        key.split(".") for key in pdf_game_state.key]
    pdf_game_state["n_key_chunks"] = [
        len(chunks) for chunks in pdf_game_state["key_chunks"]]
    # all keys have at least two chunks, so pull the first two
    # into their own fields
    pdf_game_state["keychunk_0"] = [
        x[0] for x in pdf_game_state["key_chunks"]]
    pdf_game_state["keychunk_1"] = [
        x[1] for x in pdf_game_state["key_chunks"]]

    return pdf_game_state

def extract_game_data_dict(pdf_game_state: pd.DataFrame) -> Dict[str, Any]:
    """Extract some basic game-level data.

    Args:
        pdf_game_state (pd.DataFrame): game PDF

    Returns:
        Dict[str, Any]: key-value pairs of game-level info
    """
    team_name_1 = list(pdf_game_state[
        pdf_game_state.key == "ScoreBoard.Team(1).Name"].value)[0]
    team_name_2 = list(pdf_game_state[
        pdf_game_state.key == "ScoreBoard.Team(2).Name"].value)[0]
    return {
        "team_1": team_name_1,
        "team_2": team_name_2
    }

def extract_jam_data(pdf_game_state: pd.DataFrame,
                     pdf_roster: pd.DataFrame) -> pd.DataFrame:
    """Process all the jam-level data into a dataframe
    with one row per jam.

    Args:
        pdf_game_state (pd.DataFrame): game state dataframe
        pdf_roster (pd.DataFrame): roster dataframe

    Returns:
        pd.DataFrame: jam data dataframe
    """
    # Jam-level data all lives under the "Period" structure
    pdf_period = pdf_game_state[
        pdf_game_state.keychunk_1.str.startswith("Period")]
    # All the "Period" fields have at least 3 chunks
    pdf_period["keychunk_2"] = [
        chunks[2] for chunks in pdf_period.key_chunks]
    
    pdf_jam_data = pdf_period[
        pdf_period.keychunk_2.str.startswith("Jam(")]
    # All the "Jam" fields have at least 3 chunks
    pdf_jam_data["keychunk_3"] = [x[3] for x in pdf_jam_data.key_chunks]

    # Extract jam and period into columns
    pdf_jam_data["jam"] = [
        int(x[len("Jam("):-1]) for x in pdf_jam_data.keychunk_2]
    pdf_jam_data["period"] = [
        int(x[len("Period("):-1]) for x in pdf_jam_data.keychunk_1]
    # Make a column combining jam and period. This is our key column.
    pdf_jam_data["prd_jam"] = [
        f"{period}:{'0' if (jam < 10) else ''}{jam}" 
        for period, jam in zip(*[pdf_jam_data.period, pdf_jam_data.jam])]
    n_jams = len(set(pdf_jam_data.prd_jam))

    # There are some jam fields with one entry per jam.
    # Grab those into a dataframe
    pdf_jam_fieldcounts = pd.DataFrame(
        pdf_jam_data.keychunk_3.value_counts())
    jam_simple_fields = pdf_jam_fieldcounts[
        pdf_jam_fieldcounts.keychunk_3 == n_jams].index
    pdf_jam_simpledata = pdf_jam_data[
        pdf_jam_data.keychunk_3.isin(jam_simple_fields)]

    pdf_jams_summary = pdf_jam_simpledata[
        ["keychunk_3", "jam", "period", "prd_jam", "value"]].pivot(
        index="prd_jam", columns="keychunk_3", values="value")
    # Grab the jam number back out into a column
    pdf_jams_summary["prd_jam"] = pdf_jams_summary.index
    pdf_jams_summary.index = range(len(pdf_jams_summary))

    # For some reason there's an empty 0th jam recorded in an empty 0th period.
    # Remove it.
    pdf_jams_summary = pdf_jams_summary[pdf_jams_summary.prd_jam != "0:00"]

    # all time values are in ms.
    pdf_jams_summary["duration_seconds"] = pdf_jams_summary.Duration / 1000

    # process the team jam info for each team
    pdf_teamjam_team1 = process_team_jam_info(pdf_jam_data, 1, n_jams, pdf_roster)
    pdf_teamjam_team2 = process_team_jam_info(pdf_jam_data, 2, n_jams, pdf_roster)

    # merge jam summary data with team jam data
    pdf_jams_summary_withteams = (
        pdf_jams_summary
        .merge(pdf_teamjam_team1, on="prd_jam")
        .merge(pdf_teamjam_team2, on="prd_jam"))

    # add a column indicating whether anyone called it off
    pdf_jams_summary_withteams["Calloff_any"] = [x or y
                                                for x, y
                                                in zip(*[pdf_jams_summary_withteams.Calloff_1,
                                                         pdf_jams_summary_withteams.Calloff_2])]

    # transform times we're keeping from ms to s
    pdf_jams_summary_withteams["jam_duration_seconds"] = (
        pdf_jams_summary_withteams["PeriodClockElapsedEnd"] -
        pdf_jams_summary_withteams["PeriodClockElapsedStart"]) / 1000
    pdf_jams_summary_withteams["jam_starttime_seconds"] = pdf_jams_summary_withteams[
        "PeriodClockElapsedStart"] / 1000
    pdf_jams_summary_withteams["jam_endtime_seconds"] = pdf_jams_summary_withteams[
        "PeriodClockElapsedEnd"] / 1000

    # Drop a bunch of useless columns
    pdf_jams_summary_withteams = pdf_jams_summary_withteams.drop(columns=[
    "Duration", "Id", "Next", "PeriodClockDisplayEnd", "Previous", "Readonly",
    "PeriodClockElapsedEnd", "PeriodClockElapsedStart"])

    return pdf_jams_summary_withteams

def extract_roster(pdf_game_state: pd.DataFrame,
                   team_name_1: str, team_name_2: str) -> pd.DataFrame:
    """Extract a DataFrame representing the rosters of the two
    teams.

    Args:
        pdf_game_state (pd.DataFrame): _description_
        team_name_1 (str): _description_
        team_name_2 (str): _description_

    Returns:
        pd.DataFrame: _description_
    """
    pdf_game_state_roster = pdf_game_state[
        pdf_game_state.key.str.contains(
            f"ScoreBoard.PreparedTeam\({team_name_1}\).Skater") |
        pdf_game_state.key.str.contains(
            f"ScoreBoard.PreparedTeam\({team_name_2}\).Skater")]
    pdf_game_state_roster["team"] = [
        chunks[1][chunks[1].index("(") + 1:chunks[1].index(")")]
        for chunks in pdf_game_state_roster.key_chunks]
    pdf_game_state_roster["skater"] = [
        chunks[2][chunks[2].index("(") + 1:chunks[2].index(")")]
        for chunks in pdf_game_state_roster.key_chunks]
    pdf_game_state_roster["roster_key"] = [
        chunks[3] for chunks in pdf_game_state_roster.key_chunks]

    pdf_roster = pdf_game_state_roster.pivot(index="skater", columns="roster_key", values="value")
    return pdf_roster


def process_team_jam_info(pdf_jam_data: pd.DataFrame, team_number: int,
                          n_jams: int, pdf_roster: pd.DataFrame) -> pd.DataFrame:
    """Process the jam info for one team.

    Args:
        pdf_jam_data (pd.DataFrame): jam dataframe
        team_number (int): team number to process
        n_jams (int): number of jams in the file
        pdf_roster (pd.DataFrame): roster dataframe

    Returns:
        pd.DataFrame: pdf with info for one team's jams
    """
    pdf_ateamjams_data = pdf_jam_data[
        pdf_jam_data.keychunk_3.str.contains(f"TeamJam\({team_number}")]
    pdf_ateamjams_data["keychunk_4"] = [chunks[4] for chunks in pdf_ateamjams_data.key_chunks]
    #print(set(pdf_ateamjams_data["keychunk_4"]))
    pdf_ateamjam_fieldcounts = pd.DataFrame(pdf_ateamjams_data["keychunk_4"].value_counts())

    # Grab the one-per-jam fields from the teamjam dataframe, identifying by the fact that they
    # occur n_jams times. Exception: ScoringTrip can occur that many times, so get rid of it.
    teamjam_simple_fields = pdf_ateamjam_fieldcounts[
        (pdf_ateamjam_fieldcounts.keychunk_4 == n_jams)
        & ~pdf_ateamjam_fieldcounts.keychunk_4.index.str.contains("ScoringTrip")].index
    
    # I don't think we need anything in the ScoringTrip fields, but if we do this is the place to
    # parse it. Maybe counting scoring trips would be interesting?

    pdf_ateamjams_simpledata = pdf_ateamjams_data[
        pdf_ateamjams_data.keychunk_4.isin(teamjam_simple_fields)]
    
    pdf_ateamjams_summary = pdf_ateamjams_simpledata[["keychunk_4", "prd_jam", "value"]].pivot(
        index="prd_jam", 
        columns="keychunk_4", values="value")
    pdf_ateamjams_summary["prd_jam"] = pdf_ateamjams_summary.index
    pdf_ateamjams_summary.index = range(len(pdf_ateamjams_summary))

    # add jammer info
    pdf_ateamjams_summary["jammer_id"] = list(pdf_ateamjams_data[
        pdf_ateamjams_data.key.str.endswith("Fielding(Jammer).Skater")].value)
    pdf_ateamjams_summary = pdf_ateamjams_summary.merge(pdf_roster.rename(
        columns={"Id": "jammer_id", "Name": "jammer_name", "Number": "jammer_number"}),
        on="jammer_id")

    pdf_scoringtrips = parse_scoringtrip_data(pdf_ateamjams_data)
    # need to rename the informational columns of pdf_scoringtrips
    scoringtrip_cols_to_rename = [x for x in pdf_scoringtrips.columns
                                  if x != "prd_jam"]

    pdf_ateamjams_summary_withscoringtrips = pdf_ateamjams_summary.merge(pdf_scoringtrips, on="prd_jam")
    pdf_ateamjams_summary_kept = pdf_ateamjams_summary_withscoringtrips[
        ["prd_jam"] + TEAMJAM_SUMMARY_COLUMNS + scoringtrip_cols_to_rename]

    pdf_ateamjams_summary_kept_colsrenamed = pdf_ateamjams_summary_kept.rename(
        columns={col: f"{col}_{team_number}"
                 for col in TEAMJAM_SUMMARY_COLUMNS + scoringtrip_cols_to_rename})
    return pdf_ateamjams_summary_kept_colsrenamed.sort_values("prd_jam")


def parse_scoringtrip_data(pdf_ateamjams_data: pd.DataFrame) -> pd.DataFrame:
    """ Parse the data we want from the scoring trips.
    Currently just counting them. If we want score counts from individual trips, or something,
    parse it out and add it here.

    Args:
        pdf_ateamjams_data (pd.DataFrame): 

    Returns:
        pd.DataFrame: _description_
    """
    jams = []
    scoring_pass_counts = []
    for prd_jam in sorted(list(set(pdf_ateamjams_data.prd_jam))):
        pdf_thisjam = pdf_ateamjams_data[pdf_ateamjams_data.prd_jam == prd_jam]
        thisjam_keys = set(pdf_thisjam.key)
        thisjam_scoringtrip_keys = [x for x in thisjam_keys if "ScoringTrip" in x]
        scoring_trip_chunks = [akey.split(".")[4] for akey in thisjam_scoringtrip_keys]
        scoring_trip_numbers = [int(achunk[achunk.index("(")+1:-1])
                                for achunk in scoring_trip_chunks]
        n_scoring_passes = max(scoring_trip_numbers)
        jams.append(prd_jam)
        scoring_pass_counts.append(n_scoring_passes)
    pdf_scoring_pass_counts = pd.DataFrame({
        "prd_jam": jams,
        "n_scoring_trips": scoring_pass_counts
    })
    pdf_scoring_pass_counts.index = range(len(pdf_scoring_pass_counts))
    return pdf_scoring_pass_counts