__author__ = "Damon May"
"""Methods for turning game JSON into Pandas dataframes
"""

import pandas as pd
from typing import Dict, Any
from jamstats.data.game_data import DerbyGame
import logging
import seaborn as sns

logger = logging.Logger(__name__)

# Columns to keep at the team+jam level
TEAMJAM_SUMMARY_COLUMNS = [
    "Calloff", "Injury", "JamScore", "Lead",
    "Lost", "NoInitial", "StarPass", "TotalScore", "jammer_name", "jammer_number",
    "Skaters"]


def load_json_derby_game(game_json) -> DerbyGame:
    """Load the derby game stored in a json dict

    Returns:
        DerbyGame: derby game
    """
    json_major_version = get_json_major_version(game_json["state"])
    pdf_game_state = json_to_game_dataframe(game_json)
    game_data_dict = extract_game_data_dict(pdf_game_state)
    pdf_roster = extract_roster(pdf_game_state,
                                game_data_dict["team_1"],
                                game_data_dict["team_2"])
    pdf_game_data = extract_jam_data(pdf_game_state, pdf_roster)
    pdf_penalties = extract_penalties(pdf_game_state, pdf_roster,
                                      json_major_version)
    try:
        pdf_team_colors = extract_team_colors(pdf_game_state)
    except Exception as e:
        logger.warn(f"Failed to extract team colors. Exception: {e}")

    return DerbyGame(pdf_game_data, game_data_dict, pdf_penalties, pdf_team_colors)


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

    json_major_version = get_json_major_version(game_dict)

    if json_major_version == 5:
        # v5.0 adds a "Game(<game_id>)" chunk to almost every key. Get rid of that.

        # In-process games have both "CurrentGame" fields and fields
        # annotated with a game identifier. Complete games don't have
        # "CurrentGame" fields.
        # I believe the "CurrentGame" fields are the ones I want,
        # for in-process games. Strip out the others.
        logger.debug(f"Found version 5. Checking for in-progress game...")
        is_in_progress_game = False
        for key in game_dict:
            if ".CurrentGame." in key:
               is_in_progress_game = True
               break
        if is_in_progress_game:
            logger.debug(f"Found in-progress game. Stripping rows. Before: {len(game_dict)} keys")
            game_dict_new = {}
            for key in game_dict:
                if not key.split(".")[1].startswith("Game("):
                    game_dict_new[key.replace("CurrentGame", "Game(dummy)")] = game_dict[key]
            game_dict = game_dict_new
            logger.debug(f"After: {len(game_dict)} keys.")
        game_dict_new = {
            ".".join([chunk for chunk in key.split(".") if not chunk.startswith("Game(")]):
            game_dict[key]
            for key in game_dict
        }
        game_dict = game_dict_new
        

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


def get_json_major_version(game_dict: Dict[str, Any]) -> int:
    """Get the major version of CRG used to generate the file

    Args:
        pdf_game_state (pd.DataFrame): pandas representation of the whole game json

    Returns:
        int: major version
    """
    version_str = game_dict["ScoreBoard.Version(release)"]
    major_version = version_str.split(".")[0]
    assert(major_version.startswith("v"))
    logger.debug(f"JSON major version string: {major_version}")
    return int(major_version[1:])


def get_json_major_version_from_pdf(pdf_game_data: pd.DataFrame) -> int:
    """Get the major version of CRG used to generate the file

    Args:
        pdf_game_state (pd.DataFrame): pandas representation of the whole game json

    Returns:
        int: major version
    """
    version_str = list(
        pdf_game_data[pdf_game_data.key == "ScoreBoard.Version(release)"].value)[0]
    major_version = version_str.split(".")[0]
    assert(major_version.startswith("v"))
    return int(major_version[1:])


def extract_game_data_dict(pdf_game_state: pd.DataFrame) -> Dict[str, Any]:
    """Extract some basic game-level data.

    Args:
        pdf_game_state (pd.DataFrame): game PDF

    Returns:
        Dict[str, Any]: key-value pairs of game-level info
    """
    team1_key = "ScoreBoard.Team(1).Name"
    team2_key = "ScoreBoard.Team(2).Name"

    team_name_1 = list(pdf_game_state[
        pdf_game_state.key == team1_key].value)[0]
    team_name_2 = list(pdf_game_state[
        pdf_game_state.key == team2_key].value)[0]

    # Get rid of weird characters in team names
    team_name_1 = cleanup_team_name(team_name_1)
    team_name_2 = cleanup_team_name(team_name_2)

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
    pdf_jam_data = build_jam_dataframe(pdf_game_state)
    pdf_teamindependent_jam_data = extract_nonteam_jam_data(pdf_jam_data)
    n_jams = len(pdf_teamindependent_jam_data)
    logger.debug(f"Jams: {n_jams}")

    # process the team jam info for each team
    # Add 1 to jam count for jam 0
    pdf_teamjam_team1 = process_team_jam_info(pdf_jam_data, 1, n_jams+1, pdf_roster)
    pdf_teamjam_team2 = process_team_jam_info(pdf_jam_data, 2, n_jams+1, pdf_roster)
    
    # merge jam summary data with team jam data
    pdf_jams_summary_withteams = (
        pdf_teamindependent_jam_data
        .merge(pdf_teamjam_team1, on="prd_jam")
        .merge(pdf_teamjam_team2, on="prd_jam"))

    logger.debug(f"After merging teamjams: {len(pdf_jams_summary_withteams)}")

    # Add net points column
    pdf_jams_summary_withteams["net_points_1"] = (
        pdf_jams_summary_withteams["JamScore_1"] - pdf_jams_summary_withteams["JamScore_2"])
    pdf_jams_summary_withteams["net_points_2"] = -pdf_jams_summary_withteams["net_points_1"]

    # add a column indicating whether anyone called it off
    pdf_jams_summary_withteams["Calloff_any"] = [
        x or y
        for x, y
        in zip(*[pdf_jams_summary_withteams.Calloff_1,
                 pdf_jams_summary_withteams.Calloff_2])]

    # calculate time to lead (None if no lead). It's the duration of the
    # first scoring pass for the team that got lead, if any.
    teams_with_lead = []
    times_to_lead = []
    for _, row in pdf_jams_summary_withteams.iterrows():
        time_to_lead = None
        team_with_lead = None
        if row["Lead_1"]:
            time_to_lead = row["first_scoring_pass_durations_1"]
            team_with_lead = 1
        elif row["Lead_2"]:
            time_to_lead = row["first_scoring_pass_durations_2"]
            team_with_lead = 2
        times_to_lead.append(time_to_lead)
        teams_with_lead.append(team_with_lead)
    pdf_jams_summary_withteams["time_to_lead"] = times_to_lead
    pdf_jams_summary_withteams["team_with_lead"] = teams_with_lead

    logger.debug(f"Made jams summary dataframe. Rows: {len(pdf_jams_summary_withteams)}")
    
    return pdf_jams_summary_withteams


def build_jam_dataframe(pdf_game_state: pd.DataFrame) -> pd.DataFrame:
   # Jam-level data all lives under the "Period" structure
    pdf_period = pdf_game_state.loc[
        pdf_game_state.keychunk_1.str.startswith("Period")].copy()
    # All the "Period" fields have at least 3 chunks
    pdf_period["keychunk_2"] = [
        chunks[2] for chunks in pdf_period.key_chunks]

    logger.debug(f"Found {len(pdf_period)} Period rows.")
    
    pdf_jam_data = pdf_period[
        pdf_period.keychunk_2.str.startswith("Jam(")].copy()
    # All the "Jam" fields have at least 3 chunks
    pdf_jam_data["keychunk_3"] = [x[3] for x in pdf_jam_data.key_chunks]

    logger.debug(f"Found {len(pdf_jam_data)} Jam rows.")

    # Extract jam and period into columns
    pdf_jam_data["jam"] = [
        int(x[len("Jam("):-1]) for x in pdf_jam_data.keychunk_2]
    pdf_jam_data["period"] = [
        int(x[len("Period("):-1]) for x in pdf_jam_data.keychunk_1]
    # Make a column combining jam and period. This is our key column.
    pdf_jam_data["prd_jam"] = [
        f"{period}:{'0' if (jam < 10) else ''}{jam}" 
        for period, jam in zip(*[pdf_jam_data.period, pdf_jam_data.jam])]
    return pdf_jam_data


def extract_nonteam_jam_data(pdf_jam_data: pd.DataFrame) -> pd.DataFrame:
    """Process all the team-independent jam-level data into a dataframe
    with one row per jam.

    Args:
        pdf_game_state (pd.DataFrame): game state dataframe

    Returns:
        pd.DataFrame: jam data dataframe
    """
    n_jams = len(set(pdf_jam_data.prd_jam))

    logger.debug(f"Found {n_jams} jams.") 

    # There are some jam fields with one entry per jam.
    # Grab those into a dataframe
    pdf_jam_fieldcounts = pd.DataFrame(
        pdf_jam_data.keychunk_3.value_counts())
    jam_simple_fields = pdf_jam_fieldcounts[
        pdf_jam_fieldcounts.keychunk_3 == n_jams].index
    pdf_jam_simpledata = pdf_jam_data[
        pdf_jam_data.keychunk_3.isin(jam_simple_fields)]
    logger.debug(f"Jam simple fields: {jam_simple_fields}")

    pdf_jams_summary = pdf_jam_simpledata[
        ["keychunk_3", "jam", "period", "prd_jam", "value"]].pivot(
        index="prd_jam", columns="keychunk_3", values="value")
    # Grab the jam number back out into a column
    pdf_jams_summary["prd_jam"] = pdf_jams_summary.index
    pdf_jams_summary.index = range(len(pdf_jams_summary))

    logger.debug(f"Jams summary rows: {len(pdf_jams_summary)}")

    # For some reason there's an empty 0th jam recorded in an empty 0th period.
    # Remove it.
    pdf_jams_summary = pdf_jams_summary[pdf_jams_summary.prd_jam != "0:00"]

    logger.debug(f"Jams summary rows (without 0:00): {len(pdf_jams_summary)}")

    # all time values are in ms.
    pdf_jams_summary["duration_seconds"] = pdf_jams_summary.Duration / 1000

    # transform times we're keeping from ms to s
    pdf_jams_summary["jam_duration_seconds"] = (
        pdf_jams_summary["PeriodClockElapsedEnd"] -
        pdf_jams_summary["PeriodClockElapsedStart"]) / 1000
    pdf_jams_summary["jam_starttime_seconds"] = pdf_jams_summary[
        "PeriodClockElapsedStart"] / 1000
    pdf_jams_summary["jam_endtime_seconds"] = pdf_jams_summary[
        "PeriodClockElapsedEnd"] / 1000

    # Drop a bunch of useless columns
    pdf_jams_summary = pdf_jams_summary.drop(columns=[
    "Duration", "Id", "Next", "PeriodClockDisplayEnd", "Previous", "Readonly",
    "PeriodClockElapsedEnd", "PeriodClockElapsedStart"])

    return pdf_jams_summary

def extract_roster(pdf_game_state: pd.DataFrame,
                   team_name_1: str, team_name_2: str) -> pd.DataFrame:
    """Extract a DataFrame representing the rosters of the two
    teams.

    Args:
        pdf_game_state (pd.DataFrame): game state dataframe
        team_name_1 (str): Name of team 1
        team_name_2 (str): Name of team 2

    Returns:
        pd.DataFrame: _description_
    """
    logger.debug("extract_roster begin")
    json_major_version = get_json_major_version_from_pdf(pdf_game_state)
    if json_major_version == 5:
        logger.debug("JSON version 5")
        team_string_1 = f"Team\(1\)"
        team_string_2 = f"Team\(2\)"
    elif json_major_version == 4:
        logger.debug("JSON version 4")
        team_string_1 = f"PreparedTeam\({team_name_1}\)"
        team_string_2 = f"PreparedTeam\({team_name_2}\)"
    
    team_string_1 = cleanup_team_name(team_string_1)
    team_string_2 = cleanup_team_name(team_string_2)

    logger.debug(f"Looking for teams in roster: {team_string_1}, {team_string_2}")
    pdf_game_state_roster = pdf_game_state.loc[
        pdf_game_state.key.str.contains(
            f"ScoreBoard.{team_string_1}.Skater") |
        pdf_game_state.key.str.contains(
            f"ScoreBoard.{team_string_2}.Skater")
    ].copy()

    pdf_game_state_roster["team"] = [
        chunks[1][chunks[1].index("(") + 1:chunks[1].index(")")]
        for chunks in pdf_game_state_roster.key_chunks]
    logger.debug("Roster rows by team:")
    logger.debug(pdf_game_state_roster.team.value_counts())
    if json_major_version == 5:
        # Version 4 stored the team name. Version 5 stores the number,
        # so translate.
        pdf_game_state_roster["team"] = [team_name_1 if team == "1"
                                         else team_name_2 if team == "2"
                                         else "????"
                                         for team in pdf_game_state_roster["team"]]
    pdf_game_state_roster["skater"] = [
        chunks[2][chunks[2].index("(") + 1:chunks[2].index(")")]
        for chunks in pdf_game_state_roster.key_chunks]
    pdf_game_state_roster["roster_key"] = [
        chunks[3] for chunks in pdf_game_state_roster.key_chunks]
    # dump a bunch of extraneous columns
    pdf_game_state_roster = pdf_game_state_roster[pdf_game_state_roster.roster_key.isin(
        ["Id", "Name", "RosterNumber", "team"]
    )]
    pdf_roster = pdf_game_state_roster.pivot(index="skater", columns="roster_key", values="value")

    skaterid_team_map = dict(zip(*[pdf_game_state_roster["skater"], pdf_game_state_roster["team"]]))
    pdf_roster["team"] = [skaterid_team_map[skater] for skater in pdf_roster.Id]
    logger.debug("Loaded roster. Skater count by team:")
    logger.debug(pdf_roster.team.value_counts())
    return pdf_roster


def process_team_jam_info(pdf_game_state: pd.DataFrame, team_number: int,
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
    pdf_ateamjams_data = pdf_game_state[
        pdf_game_state.keychunk_3.str.contains(f"TeamJam\({team_number}")].copy()
    pdf_ateamjams_data["keychunk_4"] = [chunks[4] for chunks in pdf_ateamjams_data.key_chunks]

    logger.debug(f"teamjam rows, team {team_number}: {len(pdf_ateamjams_data)}")

    pdf_ateamjam_fieldcounts = pd.DataFrame(pdf_ateamjams_data["keychunk_4"].value_counts())

    # Grab the one-per-jam fields from the teamjam dataframe, identifying by the fact that they
    # occur n_jams times. Exception: ScoringTrip can occur that many times, so get rid of it.
    teamjam_simple_fields = pdf_ateamjam_fieldcounts[
        (pdf_ateamjam_fieldcounts.keychunk_4 == n_jams)
        & ~pdf_ateamjam_fieldcounts.keychunk_4.index.str.contains("ScoringTrip")].index

    logger.debug(f"teamjam simple fields: {teamjam_simple_fields}")
    
    pdf_ateamjams_simpledata = pdf_ateamjams_data[
        pdf_ateamjams_data.keychunk_4.isin(teamjam_simple_fields)]

    pdf_ateamjams_summary = pdf_ateamjams_simpledata[["keychunk_4", "prd_jam", "value"]].pivot(
        index="prd_jam", 
        columns="keychunk_4", values="value")
    pdf_ateamjams_summary["prd_jam"] = pdf_ateamjams_summary.index
    pdf_ateamjams_summary.index = range(len(pdf_ateamjams_summary))

    logger.debug(f"teamjams pivoted rows: {len(pdf_ateamjams_summary)}")

    # add jammer info
    pdf_ateamjams_jammers = pdf_ateamjams_data[
        pdf_ateamjams_data.key.str.endswith("Fielding(Jammer).Skater")][
            ["prd_jam", "value"]].rename(columns={"value": "jammer_id"})
    pdf_ateamjams_summary = pdf_ateamjams_summary.merge(pdf_ateamjams_jammers,
        on="prd_jam", how="left")
    pdf_ateamjams_summary = pdf_ateamjams_summary.merge(pdf_roster.rename(
        columns={"Id": "jammer_id", "Name": "jammer_name", "RosterNumber": "jammer_number"}),
        on="jammer_id", how="left")

    logger.debug(f"After adding jammer info: {len(pdf_ateamjams_summary)}")

    # add list of skater names per jam
    pdf_jam_skater_lists = extract_team_perjam_skaters(pdf_ateamjams_data, pdf_roster)
    pdf_ateamjams_summary = pdf_ateamjams_summary.merge(
        pdf_jam_skater_lists, on="prd_jam"
    )
    logger.debug(f"After adding skaters/jam: {len(pdf_ateamjams_summary)}")

    pdf_scoringtrips = parse_scoringtrip_data(pdf_ateamjams_data)
    # need to rename the informational columns of pdf_scoringtrips
    logger.debug(f"Loaded {len(pdf_scoringtrips)} scoring trips.")
    scoringtrip_cols_to_rename = [x for x in pdf_scoringtrips.columns
                                  if x != "prd_jam"]

    pdf_ateamjams_summary_withscoringtrips = pdf_ateamjams_summary.merge(
        pdf_scoringtrips, on="prd_jam")
    logger.debug(f"After adding scoring trips: {len(pdf_ateamjams_summary_withscoringtrips)}")
    pdf_ateamjams_summary_kept = pdf_ateamjams_summary_withscoringtrips[
        ["prd_jam"] + TEAMJAM_SUMMARY_COLUMNS + scoringtrip_cols_to_rename]

    pdf_ateamjams_summary_kept_colsrenamed = pdf_ateamjams_summary_kept.rename(
        columns={col: f"{col}_{team_number}"
                 for col in TEAMJAM_SUMMARY_COLUMNS + scoringtrip_cols_to_rename})

    return pdf_ateamjams_summary_kept_colsrenamed.sort_values("prd_jam")


def extract_team_perjam_skaters(pdf_ateamjams_data: pd.DataFrame,
                                pdf_roster: pd.DataFrame) -> pd.DataFrame:
    """Calculate the list of skater names per jam for this team.

    Args:
        pdf_ateamjams_data (pd.DataFrame): dataframe with a single team's jam data
        pdf_roster (pd.DataFrame): Roster dataframe

    Returns:
        pd.DataFrame: dataframe mapping prd_jam to list of skater names for the jam
    """
    logger.debug("extract_team_perjam_skaters begin")
    pdf_ateamjams_data_fielding = pdf_ateamjams_data[
        pdf_ateamjams_data["keychunk_4"].str.startswith("Fielding")].copy()
    pdf_ateamjams_data_fielding["keychunk_5"] = [
        chunks[5] for chunks in pdf_ateamjams_data_fielding.key_chunks]
    pdf_ateamjams_data_skaters = pdf_ateamjams_data_fielding[
        pdf_ateamjams_data_fielding.keychunk_5 == "Skater"]
    pdf_ateamjams_data_skaters = pdf_ateamjams_data_skaters.rename(columns={
        "value": "Id"
    })

    logger.debug(f"    Before roster merge, team jam skater data: {len(pdf_ateamjams_data_skaters)}")
    pdf_ateamjams_data_skaters_withname = pdf_ateamjams_data_skaters.merge(
        pdf_roster, on="Id")
    logger.debug(f"    After roster merge, team jam skater data: {len(pdf_ateamjams_data_skaters_withname)}")

    pdf_jam_skater_lists = pdf_ateamjams_data_skaters_withname.groupby(
        "prd_jam")["Name"].apply(list).reset_index()
    pdf_jam_skater_lists = pdf_jam_skater_lists.rename(columns={"Name": "Skaters"})
    logger.debug(f"    Jam skater lists length: {len(pdf_jam_skater_lists)}")

    return pdf_jam_skater_lists


def parse_scoringtrip_data(pdf_ateamjams_data: pd.DataFrame) -> pd.DataFrame:
    """ Parse the data we want from the scoring trips.
    Currently just counting them and getting the duration of the first one,
    which is "time to lead" for the team that gets lead.

    If we want score counts from individual trips, or something,
    parse it out and add it here.

    Args:
        pdf_ateamjams_data (pd.DataFrame): jam data for one team

    Returns:
        pd.DataFrame: scoring trip summary pdf with one row per jam
    """
    jams = []
    scoring_pass_counts = []
    first_scoring_pass_durations_seconds = []
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
        # "time to lead" (time between the start whistle and the lead jammer getting lead)
        # is stored as the Duration of ScoringTrip(1), which is a fake "scoring" trip
        # representing the initial pass.
        first_trip_duration_key = [x for x in thisjam_scoringtrip_keys
                                   if x.endswith("ScoringTrip(1).Duration")][0]
        first_trip_duration_seconds = int(list(
            pdf_thisjam[pdf_thisjam.key == first_trip_duration_key].value)[0]) / 1000
        first_scoring_pass_durations_seconds.append(
            first_trip_duration_seconds
        )
    pdf_scoring_pass_counts = pd.DataFrame({
        "prd_jam": jams,
        "n_scoring_trips": scoring_pass_counts,
        "first_scoring_pass_durations": first_scoring_pass_durations_seconds
    })
    pdf_scoring_pass_counts.index = range(len(pdf_scoring_pass_counts))
    return pdf_scoring_pass_counts


def extract_penalties(pdf_game_state: pd.DataFrame,
                      pdf_roster: pd.DataFrame,
                      json_major_version: int) -> pd.DataFrame:
    """Extract a dataframe with one row per penalty

    Args:
        pdf_game_state (pd.DataFrame): game state dataframe
        pdf_roster (pd.DataFrame): roster dataframe

    Returns:
        pd.DataFrame: penalty dataframe
    """
    logger.debug("extract_penalties begin")
    pdf_penalty_gamedata = pdf_game_state[(pdf_game_state.n_key_chunks == 5)].copy()
    pdf_penalty_gamedata["keychunk_2"] = [chunks[2] for chunks in pdf_penalty_gamedata.key_chunks]
    pdf_penalty_gamedata["keychunk_3"] = [chunks[3] for chunks in pdf_penalty_gamedata.key_chunks]
    pdf_penalty_gamedata = pdf_penalty_gamedata[
        pdf_penalty_gamedata.keychunk_3.str.startswith("Penalty(")]
    logger.debug(f"    Rows with `Penalty(`: {len(pdf_penalty_gamedata)}")
    pdf_penalty_gamedata["penalty_key"] = [chunks[4] for chunks in pdf_penalty_gamedata.key_chunks]
    pdf_penalty_gamedata["Id"] = [chunk[len("Skater("):-1]
                                  for chunk in pdf_penalty_gamedata.keychunk_2]
    pdf_penalty_gamedata = pdf_penalty_gamedata.merge(
        pdf_roster[["Id", "Name", "team"]], on="Id")
    logger.debug(f"    After merging with roster: {len(pdf_penalty_gamedata)}")
    pdf_penalties = pdf_penalty_gamedata[pdf_penalty_gamedata.penalty_key == "Code"]
    pdf_penalties = pdf_penalties.rename(columns={"value": "penalty_code"})
    pdf_penalties = pdf_penalties[["Name", "team", "penalty_code"]]
    logger.debug(f"    Before merge with penalty codes: {len(pdf_penalties)}")

    # add penalty names
    pdf_penalty_codes_names = build_penalty_code_name_map(pdf_game_state, json_major_version)
    pdf_penalties = pdf_penalties.merge(pdf_penalty_codes_names, on="penalty_code")
    logger.debug(f"Extracted penalties: {len(pdf_penalties)} rows.")
    return pdf_penalties


def build_penalty_code_name_map(pdf_game_state: pd.DataFrame,
                                json_major_version: int) -> Dict[str, str]:
    """Pull out the map from penalty codes to names that's repeated in every game file.

    Args:
        pdf_game_state (pd.DataFrame): game json in dataframe

    Returns:
        Dict[str, str]: map from letter codes to names
    """
    # this code is very inefficient -- will do string matching on the whole game dictionary
    logger.debug(f"build_penalty_code_name_map begin, version=={json_major_version}")
    if json_major_version == 5:
        pdf_penalty_codes = pdf_game_state[
            pdf_game_state["key"].str.contains("PenaltyCode")].copy()
    else:
        pdf_penalty_codes = pdf_game_state[pdf_game_state["key"].str.startswith(
            "ScoreBoard.PenaltyCodes.Code")].copy()
    pdf_penalty_codes["penalty_code"] = [x[-2:-1]
                                        for x in pdf_penalty_codes.key]       
    logger.debug(f"Built penalty code dataframe: {len(pdf_penalty_codes)} codes")
    if len(pdf_penalty_codes) == 0:
        logger.warn("Could not load penalty codes! Penalty plots will fail.")
    pdf_penalty_codes = pdf_penalty_codes[["penalty_code", "value"]].rename(columns={
        "value": "penalty_name"
    })
    # some of the penalty codes are quite long. Truncate at first comma
    pdf_penalty_codes["penalty_name"] = [penalty.split(",")[0]
                                         for penalty in pdf_penalty_codes.penalty_name]
    return pdf_penalty_codes
    

def cleanup_team_name(team_name: str) -> str:
    """ clean up weird characters in team names. I'm not positive this generalizes well.
    One of our teams had an apostrophe in it, and it was removed in the roster
    but not elsewhere.

    Args:
        team_name (str): team name with potentially weird characters

    Returns:
        stra: cleaned-up team name
    """
    return team_name.replace("'", "")


def extract_team_colors(pdf_game_data:pd.DataFrame) -> pd.DataFrame:
    """Extract the team color hex values from the game data

    Args:
        pdf_game_data (pd.DataFrame): game data

    Returns:
        pd.DataFrame: dataframe mapping team to color
    """
    pdf_team_colors = pdf_game_data[pdf_game_data.key.str.startswith("ScoreBoard.PreparedTeam") &
                                    pdf_game_data.key.str.endswith("Color(scoreboard_bg)")].copy()
    pdf_team_colors["team"] = [x[len("ScoreBoard.PreparedTeam("):-len(").Color(scoreboard_bg)")]
                            for x in pdf_team_colors.key]
    pdf_team_colors = pdf_team_colors[["team", "value"]].rename(columns={"value": "color"})
    logger.debug(f"Team colors: {pdf_team_colors}")
    return pdf_team_colors