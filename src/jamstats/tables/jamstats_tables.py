from jamstats.data.game_data import DerbyGame
from jamstats.plots.plot_util import build_anonymizer_map
from jamstats.tables.table_util import DerbyTable, DerbyHTMLElement
import pandas as pd
import logging
import numpy as np
from pandas.io.formats.style import Styler
from jamstats.plots.plot_util import (convert_millis_to_min_sec_str, PENALTYSTATUS_ORDER_DTYPE)

DEFAULT_N_RECENT_PENALTIES = 10

logger = logging.Logger(__name__)


class BothTeamsJammersTable(DerbyHTMLElement):
    name: str = "Jammers"
    description: str = "Summary tables with jammers for both teams"
    section: str = "Tables"

    def build_html(self, derby_game: DerbyGame) -> str: 
        """Build the table HTML

        Args:
            derby_game (DerbyGame): Derby Game

        Returns:
            str: HTML
        """
        pdf_team1 = get_oneteam_jammer_pdf(derby_game, 1, anonymize_names=self.anonymize_names)
        pdf_team2 = get_oneteam_jammer_pdf(derby_game, 2, anonymize_names=self.anonymize_names)
        styler_1 = pdf_team1.style
        styler_2 = pdf_team2.style
        table_html_1 = styler_1.hide(axis="index").to_html()
        table_html_2 = styler_2.hide(axis="index").to_html()
        team1_tablecell_html = f"<H2>{derby_game.team_1_name} ({len(pdf_team1)})</H2>" + table_html_1
        team2_tablecell_html = f"<H2>{derby_game.team_2_name} ({len(pdf_team2)})</H2>" + table_html_2
        return "<table><tr valign='top'><td>" + team1_tablecell_html + "</td><td>" + team2_tablecell_html + "</td></tr></table>"


def get_oneteam_jammer_pdf(derby_game: DerbyGame, team_number: int,
                           anonymize_names: bool = False) -> pd.DataFrame:
    """Load a table of jammer data for one team

    Args:
        derby_game (DerbyGame): derby game
        team_number (int): team number
        anonymize_names (bool, optional): Aonymize names? Defaults to False.

    Returns:

    """
    pdf_jammer_data = derby_game.build_team_jammersummary_df(team_number)
    if anonymize_names:
        logger.debug("Anonymizing skater names.")
        name_dict = build_anonymizer_map(set(pdf_jammer_data.Jammer))
        pdf_jammer_data["Jammer"] = [name_dict[skater]
                                     for skater in pdf_jammer_data.Jammer] 
    pdf_jammer_data["% Lead"] = (pdf_jammer_data["Proportion Lead"] * 100).astype(int)
    pdf_jammer_data = pdf_jammer_data.drop(columns=["Proportion Lead"])

    pdf_jammer_data = pdf_jammer_data.rename(columns={
        "Lead Count": "Lead",
        "Lost Count": "Lost",
        "Total Score": "Points"
    })
    pdf_jammer_data["Jammer"] = pdf_jammer_data.Number + "  " + pdf_jammer_data.Jammer
    pdf_jammer_data = pdf_jammer_data[[
        "Jammer", "Jams", "Points", "Lead", "% Lead", "Lost"
    ]]
    pdf_jammer_data = pdf_jammer_data.sort_values("Jammer")

    return pdf_jammer_data


class BothTeamsSkaterPenaltiesTable(DerbyHTMLElement):
    name: str = "All Penalties"
    description: str = "Summary tables with penalties per skater for both teams"
    section: str = "Tables"

    def build_html(self, derby_game: DerbyGame) -> str: 
        """ Get a html table of both teams' penalties

        Args:
            derby_game (DerbyGame): Derby Game

        Returns:
            str: HTML
        """

        pdf_team1_skaterpenalties = build_oneteam_skaterpenaltycounts_pdf(
            derby_game, derby_game.team_1_name, anonymize_names=self.anonymize_names)
        pdf_team2_skaterpenalties = build_oneteam_skaterpenaltycounts_pdf(
            derby_game, derby_game.team_2_name, anonymize_names=self.anonymize_names)

        # apply formatting. Change text color of each row based on penalty count
        table_htmls = []
        for pdf in [pdf_team1_skaterpenalties, pdf_team2_skaterpenalties]:
            styler = pdf.style.set_properties(**{'color': 'green'})
            red_rows = np.where(pdf['Count'] > 6, 'color: red', '')
            styler = styler.apply(lambda _: red_rows)
            orange_rows = np.where(pdf['Count'] == 6, 'color: orange', '')
            styler = styler.apply(lambda _: orange_rows)
            yellow_rows = np.where(pdf['Count'] == 5, 'color: yellow', '')
            styler = styler.apply(lambda _: yellow_rows)
            # gray background
            styler = styler.set_properties(**{'background-color': '#999999'})
            styler = styler.set_table_attributes("style='display:inline'").hide(axis="index")
            table_htmls.append(styler.to_html())

        table_html_1, table_html_2 = table_htmls

        n_team1_penalties = sum(pdf_team1_skaterpenalties.Count)
        n_team2_penalties = sum(pdf_team2_skaterpenalties.Count)
        team1_tablecell_html = f"<H2>{derby_game.team_1_name} ({n_team1_penalties})</H2>" + table_html_1
        team2_tablecell_html = f"<H2>{derby_game.team_2_name} ({n_team2_penalties})</H2>" + table_html_2
        return "<table><tr valign='top'><td>" + team1_tablecell_html + "</td><td>" + team2_tablecell_html + "</td></tr></table>"


def build_oneteam_skaterpenaltycounts_pdf(derby_game: DerbyGame, team_name: str,
                                          anonymize_names: bool=False) -> pd.DataFrame:
    """Build a dataframe of skater penalties for one team

    Args:
        derby_game (DerbyGame): Derby game
        team_name (str): Team name
        anonymize_names (bool, optional): Anonymize names?. Defaults to False.

    Returns:
        pd.DataFrame: Table with skater penalties, one row per skater
    """
    
    pdf_team_penalties = derby_game.pdf_penalties[
        derby_game.pdf_penalties.team == team_name].copy()
    pdf_team_penalties = pdf_team_penalties.rename(columns={
        "Name": "Skater"
    })

    if anonymize_names:
        logger.debug("Anonymizing skater names.")
        name_dict = build_anonymizer_map(set(pdf_team_penalties.Skater))
        pdf_team_penalties["Skater"] = [name_dict[skater]
                                        for skater in pdf_team_penalties.Skater]   

    pdf_penalties_long = (
        pdf_team_penalties.groupby(['RosterNumber', 'Skater',]).size().reset_index())
    pdf_penalties_long = pdf_penalties_long.rename(columns={
        0: "Count"
    })
    pdf_penalties_long = pdf_penalties_long.sort_values("Count", ascending=False)
    pdf_penalties_long = pdf_penalties_long.rename(columns={"RosterNumber": "Number"})

    return pdf_penalties_long


class OfficialsRosterTable(DerbyTable):
    """Table with ref and NSO rosters
    """
    name: str = "Officials Roster"
    description: str = "Table with ref and NSO rosters"
    can_show_before_game_start: bool = True

    def prepare_table_dataframe(self, derby_game: DerbyGame) -> pd.DataFrame: 
        """Combine the referee and NSO rosters into one table

        Args:
            derby_game (DerbyGame): Derby Game

        Returns:
            pd.DataFrame: Table with all officials
        """
        pdf_allofficials_roster = pd.concat([
            derby_game.pdf_ref_roster.rename(columns={"Name": "Referee"}),
            derby_game.pdf_nso_roster.rename(columns={"Name": "NSO"})], axis=1)
        pdf_allofficials_roster = pdf_allofficials_roster.fillna("")
        return pdf_allofficials_roster


class CallerDashboard(DerbyHTMLElement):
    """Caller Dashboard
    """
    name: str = "Caller Dashboard"
    description: str = "Dashboard with info for callers in one place"
    section: str = "Tables"

    def build_html(self, derby_game: DerbyGame) -> str: 
        """Build the HTML

        Args:
            derby_game (DerbyGame): Derby Game

        Returns:
            str: HTML
        """
        # build stripped-down game summary table
        pdf_game_teams_summary = derby_game.extract_game_teams_summary()
        pdf_game_teams_summary = pdf_game_teams_summary.drop(columns=[
            "Calloff", "NoInitial", "Skaters played"])
        # add Absolute Difference row
        pdf_game_teams_summary = pd.DataFrame({
            column: [pdf_game_teams_summary.loc[0, column],
                    pdf_game_teams_summary.loc[1, column],
                    abs(pdf_game_teams_summary.loc[0, column] -
                        pdf_game_teams_summary.loc[1, column])]
            if column != "Team"
            else [pdf_game_teams_summary.loc[0, column],
                pdf_game_teams_summary.loc[1, column],
                "Difference (absolute)"]
            for column in pdf_game_teams_summary.columns
        })
        pdf_game_teams_summary.index = range(len(pdf_game_teams_summary))
        styler = pdf_game_teams_summary.style.set_table_attributes(
            "style='display:inline'").hide(axis="index")
        html_game_summary = styler.to_html()

        # if we're *not* in a jam, show the jammers for the next jam
        if not derby_game.game_data_dict["jam_is_running"]:
            next_jam_section = "\n<p><b>Next jam's jammers:</b><br>\n"
            next_jam_section = next_jam_section + f"<table width=100% style='padding: 5px'><tr><th>{derby_game.team_1_name}</th><th>{derby_game.team_2_name}</th></tr>\n"
            next_jam_section += f"<tr><td>{derby_game.game_data_dict['team_1_jammer_number']} {derby_game.game_data_dict['team_1_jammer_name']}</td>\n"
            next_jam_section += f"<td>{derby_game.game_data_dict['team_2_jammer_number']} {derby_game.game_data_dict['team_2_jammer_name']}</td></tr>\n"
            next_jam_section += f"</table>\n"
            html_game_summary = html_game_summary + next_jam_section
            
        # build most-recent jam table
        pdf_jams_sorted_desc = derby_game.pdf_jams_data.sort_values(["PeriodNumber", "Number"],
                                                                    ascending=False)
        pdf_jams_sorted_desc.index = range(len(pdf_jams_sorted_desc))
        html_current_jam = get_singlejam_skaters_html(derby_game, pdf_jams_sorted_desc.head(1),
                                                    anonymize_names=self.anonymize_names)
        
        result =  "<p>" + html_game_summary + "</p><p>" + html_current_jam

        if len(pdf_jams_sorted_desc) > 1:
            second_most_recent_jam_html = get_singlejam_skaters_html(
                derby_game, pdf_jams_sorted_desc[1:].head(1),
                anonymize_names=self.anonymize_names)
            result = result + second_most_recent_jam_html

        result = result + "<p>Positions: P=Pivot, J=Jammer, B=Blocker<br/>"
        result = result + "Position notes: (NI)=No Initial, (L)=Lead, (LO)=Lost, (SP)=Star Pass<p/>"
        result = result + f"<table width=0% style='background-color: lightgray'><tr><td><br/>Penalty status:<ul>\
            <li style='color: yellow; background-color: lightgray'>Not Yet: skater on way to box</li>\
            <li style='color: red; background-color: lightgray'>Serving: skater in box</li>\
            <li style='color: green; background-color: lightgray'>Served: skater has completed serving penalty</li>\
            </li></ul></td></tr></table>"
        result = result + "</p>"
        return result


def get_current_skaters_html(derby_game: DerbyGame, anonymize_names: bool = False) -> str:
    """Get a table of the current skaters as html

    Args:
        derby_game (DerbyGame): derby game

    Returns:
        str: html table
    """
    
    pdf_jams_sorted_desc = derby_game.pdf_jams_data.sort_values(["PeriodNumber", "Number"], ascending=False)
    pdf_jams_sorted_desc.index = range(len(pdf_jams_sorted_desc))

    most_recent_jam_html = get_singlejam_skaters_html(derby_game, pdf_jams_sorted_desc.head(1),
                                                      anonymize_names=anonymize_names)
    result = most_recent_jam_html
    if len(pdf_jams_sorted_desc) > 1:
        result = result + "<br/><H4>Previous jam:</H4>"
        second_most_recent_jam_html = get_singlejam_skaters_html(derby_game, pdf_jams_sorted_desc[1:].head(1),
                                                                 anonymize_names=anonymize_names)
        result = result + second_most_recent_jam_html

    result = result + "<p>Positions: P=Pivot, J=Jammer, B=Blocker<br/>"
    result = result + "Position notes: (NI)=No Initial, (L)=Lead, (LO)=Lost, (SP)=Star Pass<p/>"
    result = result + f"<table width=0% style='background-color: lightgray'><tr><td><br/>Penalty status:<ul>\
        <li style='color: yellow; background-color: lightgray'>Not Yet: skater on way to box</li>\
        <li style='color: red; background-color: lightgray'>Serving: skater in box</li>\
        <li style='color: green; background-color: lightgray'>Served: skater has completed serving penalty</li>\
        </li></ul></td></tr></table>"
    return result


def get_singlejam_skaters_html(derby_game: DerbyGame, pdf_one_jam: pd.DataFrame,
                               anonymize_names: bool = False) -> str:
    """Get per-team tables of the skaters for a *single jam* as html

    Args:
        derby_game (DerbyGame): derby game
        pdf_one_jam (pd.DataFrame): table with a single row of jam data

    Returns:
        str: html table
    """
    pdf_team1_jam_skaters = get_team_jam_skaters_pdf(derby_game, derby_game.team_1_name,
                                                         pdf_one_jam,
                                                         anonymize_names=anonymize_names)
    pdf_team2_jam_skaters = get_team_jam_skaters_pdf(derby_game, derby_game.team_2_name,
                                                         pdf_one_jam,
                                                         anonymize_names=anonymize_names)
    map_penalty_to_color = lambda val: 'color: red' if "Serving" in val \
                                else 'color: yellow' if "Not Yet" in val \
                                else 'color: green' if "Served" in val \
                                else ''
    map_penaltycount_to_color = lambda val: 'color: red' if int(val) > 6 \
                                else 'color: orange' if int(val) == 6 \
                                else 'color: yellow' if int(val) == 5 \
                                else ''
    table_htmls = []
    for pdf in [pdf_team1_jam_skaters, pdf_team2_jam_skaters]:
        styler = pdf.style.set_properties(**{'background-color': 'lightgray'})
        styler = styler.applymap(map_penalty_to_color,
            subset=["Penalty"])
    table_htmls = []
    for pdf in [pdf_team1_jam_skaters, pdf_team2_jam_skaters]:
        styler = pdf.style.set_properties(**{'background-color': 'lightgray'})
        styler = styler.applymap(map_penalty_to_color,
            subset=["Penalty"])
        styler = styler.applymap(map_penaltycount_to_color,
            subset=["Pen. Count"]).hide(axis="index")
        styler = styler.set_table_attributes("style='display:inline'").hide(axis="index")
        table_htmls.append(styler.to_html())

    _, latest_jam_row_dict = next(pdf_one_jam.iterrows())
    period = latest_jam_row_dict["PeriodNumber"]
    number = latest_jam_row_dict["Number"]
    result = f"Period {period}, Jam {number}<br>"

    # extract current jam score per team
    _, latest_jam_row_dict = next(pdf_one_jam.iterrows())
    team_1_jamscore = latest_jam_row_dict["JamScore_1"]
    team_2_jamscore = latest_jam_row_dict["JamScore_2"]

    result = result + f"<table width=0%><tr><td><h5>{derby_game.team_1_name}: {team_1_jamscore}</h5>{table_htmls[0]}</td>"
    result = result + f"<td><h5>{derby_game.team_2_name}: {team_2_jamscore}</h5>{table_htmls[1]}</td></tr></table>\n"    
    return result


def get_team_jam_skaters_pdf(derby_game: DerbyGame, team_name: str,
                             pdf_one_jam: pd.DataFrame,
                             anonymize_names: bool = False,
                             include_alljam_serving_penalties: bool = True) -> pd.DataFrame:
    """Get a table of one team's current skaters

    Args:
        derby_game (DerbyGame): derby game
        team_name (str): team name
        include_alljam_serving_penalties (bool, optional): if True, add all penalties
            in "Serving" or "Not Yet" status to this jam's penalties. Defaults to True.

    Returns:
        str: html table
    """
    _, latest_jam_row_dict = next(pdf_one_jam.iterrows())
    period = latest_jam_row_dict["PeriodNumber"]
    number = latest_jam_row_dict["Number"]

    field_suffix = "1" if team_name == derby_game.team_1_name else "2"
    skaters = latest_jam_row_dict[f"Skaters_{field_suffix}"]
    jammer = latest_jam_row_dict[f"jammer_name_{field_suffix}"]
    pivot = latest_jam_row_dict[f"pivot_name_{field_suffix}"]
    lead = latest_jam_row_dict[f"Lead_{field_suffix}"]
    lost = latest_jam_row_dict[f"Lost_{field_suffix}"]
    starpass = latest_jam_row_dict[f"StarPass_{field_suffix}"]
    noinitial = latest_jam_row_dict[f"NoInitial_{field_suffix}"]

    position_list = []
    for s in skaters:
        if s == jammer:
            position = "J"
            if noinitial:
                position += " (NI)"
            elif lost:
                position += " (LO)"
            elif lead:
                position += " (L)"
        elif s == pivot:
            position = "P"
            if starpass:
                position += " (SP)"
        else:
            position = "B"
        position_list.append(position)
    pdf_team_current_skaters = pd.DataFrame({
        "Position": position_list,
        "Name": skaters,
    })

    # add skater numbers
    pdf_roster_formerge = derby_game.pdf_roster[["RosterNumber", "Name"]]
    # this shouldn't be necessary, but sometimes the roster has duplicate names
    pdf_roster_formerge = pdf_roster_formerge.drop_duplicates("Name", keep="first")

    # if no active skaters, Name gets wrong type
    pdf_team_current_skaters["Name"] = pdf_team_current_skaters["Name"].astype(str)
    pdf_team_current_skaters = pdf_team_current_skaters.merge(pdf_roster_formerge, on="Name")
 

    # concat skater number and name
    pdf_team_current_skaters["position_number"] = [
        1 if p.startswith("J") else 2 if p.startswith("P") else 3 for p in pdf_team_current_skaters.Position
    ] 
    pdf_team_current_skaters = pdf_team_current_skaters.sort_values(["position_number", "RosterNumber"])
    pdf_team_current_skaters = pdf_team_current_skaters.drop(columns=["position_number"])
    pdf_team_current_skaters = pdf_team_current_skaters.rename(columns={"RosterNumber": "Number"})
    pdf_team_current_skaters.index = range(len(pdf_team_current_skaters))

    # add skater penalty count
    pdf_thisteam_penalties = derby_game.pdf_penalties[derby_game.pdf_penalties["team"] == team_name]
    pdf_skater_penaltycount = pdf_thisteam_penalties.Name.value_counts().to_frame()
    pdf_skater_penaltycount = pdf_skater_penaltycount.rename(columns={"count": "Pen. Count"})
    pdf_skater_penaltycount["Name"] = pdf_skater_penaltycount.index
    pdf_skater_penaltycount.index = range(len(pdf_skater_penaltycount))
    pdf_team_current_skaters = pdf_team_current_skaters.merge(pdf_skater_penaltycount, on="Name", how="left")
    pdf_team_current_skaters["Pen. Count"] = pdf_team_current_skaters["Pen. Count"].fillna(0)
    pdf_team_current_skaters["Pen. Count"] = pdf_team_current_skaters["Pen. Count"].astype(int)

    # add penalties from this jam.

    # get all the recent penalties for this team
    pdf_recent_penalties = make_recent_penalties_dataframe(derby_game, n_penalties_for_table=100)
    pdf_recent_penalties = pdf_recent_penalties[pdf_recent_penalties["Team"] == team_name]

    # restrict to the last three jams in the current period, up to the current jam
    pdf_recent_penalties = pdf_recent_penalties[pdf_recent_penalties["Period"] == period]
    pdf_recent_penalties = pdf_recent_penalties[pdf_recent_penalties["Jam"] <= number]
    most_recent_jams = sorted(list(set(pdf_recent_penalties["Jam"])), reverse=True)[:3]
    pdf_recent_penalties = pdf_recent_penalties[pdf_recent_penalties["Jam"].isin(most_recent_jams)]

    if include_alljam_serving_penalties:
        # Change the jam number of all "Serving" or "Not Yet" penalties to the current jam,
        # so they are included.
        pdf_recent_penalties.loc[pdf_recent_penalties["Status"].isin(["Serving", "Not Yet"]), "Period"] = period
        pdf_recent_penalties.loc[pdf_recent_penalties["Status"].isin(["Serving", "Not Yet"]), "Jam"] = number
    
    
    # restrict to penalties in this jam
    pdf_recent_penalties = pdf_recent_penalties[(pdf_recent_penalties["Period"] == period)
                                                & (pdf_recent_penalties["Jam"] == number)]
    # only most recent penalty for each skater
    # Show "Serving" penalties first, then "Not Yet" penalties, then "Served" penalties.
    # Within each category, sort by most recent
    pdf_recent_penalties = pdf_recent_penalties.sort_values(["Status", "Time in Jam"], ascending=[True, False])
    pdf_recent_penalties = pdf_recent_penalties.drop_duplicates("Name", keep="first")
    pdf_recent_penalties["PenaltyAndStatus"] = pdf_recent_penalties["Penalty"] + "\n(" + pdf_recent_penalties["Status"].astype(str) + ")"
    pdf_recent_penalties = pdf_recent_penalties[["Name", "PenaltyAndStatus"]]
    pdf_recent_penalties = pdf_recent_penalties.rename(columns={"PenaltyAndStatus": "Penalty"})
    pdf_team_current_skaters = pd.merge(pdf_team_current_skaters, pdf_recent_penalties,
                                        on="Name", how="left")
    pdf_team_current_skaters = pdf_team_current_skaters[["Position", "Number", "Name", "Pen. Count", "Penalty"]]
    pdf_team_current_skaters = pdf_team_current_skaters.fillna("")

    pdf_team_current_skaters = pdf_team_current_skaters.rename(columns={
        "Position": "Pos",
        "Number": "#",
    })

    if anonymize_names:
        name_dict = build_anonymizer_map(set(pdf_team_current_skaters.Name))
        pdf_team_current_skaters["Name"] = [name_dict[skater] for skater in pdf_team_current_skaters.Name] 
    return pdf_team_current_skaters


class GameSummaryTable(DerbyTable):
    """Table of game summary information
    """
    name: str = "Game Summary"
    description: str = "Basic summary data about the game"

    def prepare_table_dataframe(self, derby_game: DerbyGame) -> pd.DataFrame: 
        """Make a table figure out of the game summary dataframe,
        suitable for writing to a .pdf

        Args:
            derby_game (DerbyGame): a derby game

        Returns:
            Figure: table figure
        """
        pdf_game_summary = derby_game.extract_game_summary()
        return pdf_game_summary


class GameTeamsSummaryTable(DerbyTable):
    """Table of game teams summary information
    """
    name: str = "Teams Summary"
    description: str = "Basic summary data about the teams"

    def prepare_table_dataframe(self, derby_game: DerbyGame) -> pd.DataFrame: 
        """Make a table figure out of the game summary dataframe,
        suitable for writing to a .pdf

        Args:
            derby_game (DerbyGame): a derby game

        Returns:
            Figure: table figure
        """
        pdf_game_teams_summary = derby_game.extract_game_teams_summary().transpose()
        pdf_game_teams_summary = pdf_game_teams_summary.rename({"n_scoring_trips": "Scoring trips"})
        pdf_game_teams_summary["Value"] = pdf_game_teams_summary.index
        pdf_game_teams_summary = pdf_game_teams_summary[["Value", 0, 1]]
        pdf_game_teams_summary = pdf_game_teams_summary.rename(columns={
            0: derby_game.team_1_name,
            1: derby_game.team_2_name,
        })
        return pdf_game_teams_summary


class RecentPenaltiesTable(DerbyTable):
    """Table with most recent penalties
    """
    name: str = "Recent Penalties"
    description: str = "Most recent penalties"

    def __init__(self, 
                 n_penalties_for_table: int = DEFAULT_N_RECENT_PENALTIES,
                 anonymize_names: bool = False,
                 anonymize_teams: bool = False) -> None:
        super(RecentPenaltiesTable, self).__init__(anonymize_names=anonymize_names,
                         anonymize_teams=anonymize_teams)
        self.n_penalties_for_table = n_penalties_for_table

    def prepare_table_dataframe(self, derby_game: DerbyGame) -> pd.DataFrame: 
        """Make table out of most recent penalties

        Args:
            derby_game (DerbyGame): Derby Game

        Returns:
            pd.DataFrame: Table with all officials
        """
        pdf_recent_penalties = make_recent_penalties_dataframe(
            derby_game, n_penalties_for_table=self.n_penalties_for_table)
        if self.anonymize_names:
            name_dict = build_anonymizer_map(set(pdf_recent_penalties.Name))
            pdf_recent_penalties["Name"] = [name_dict[skater] for skater in pdf_recent_penalties.Name] 
        return pdf_recent_penalties

    def build_html(self, derby_game: DerbyGame) -> str: 
        """Build the table HTML: prepare the data, then style it.

        Args:
            derby_game (DerbyGame): Derby Game

        Returns:
            Figure: matplotlib figure
        """
        pdf_recent_penalties = self.prepare_table_dataframe(derby_game)
        map_team_to_color = lambda team: f"color: {derby_game.team_color_1}" if team == derby_game.team_1_name \
            else f"color: {derby_game.team_color_2}" if team == derby_game.team_2_name \
            else ''
        styler = pdf_recent_penalties.style.applymap(map_team_to_color, subset=["Team"]).hide(axis="index")

        # if either team is white, don't use white background.
        # This will break if white plays gray
        #if derby_game.team_color_1.lower() == "#ffffff" or derby_game.team_color_2.lower() == "#ffffff":
        #    styler = styler.set_properties(**{'background-color': 'gray'})
        return styler.to_html(index=False)


def make_recent_penalties_dataframe(derby_game: DerbyGame,
                                    n_penalties_for_table: int = DEFAULT_N_RECENT_PENALTIES) -> pd.DataFrame:
    """Make a dataframe out of most recent penalties

    Args:
        derby_game (DerbyGame): a derby game
        n_penalties_for_table (int, optional): number of penalties to include in table.

    Returns:
        Figure: table figure
    """    
    # Sort penalties by time, then merge with jam data to get the time in jam
    pdf_recent_penalties = derby_game.pdf_penalties.sort_values(
        "Time", ascending=False)[:n_penalties_for_table].copy()
    pdf_recent_penalties = pdf_recent_penalties.merge(derby_game.pdf_jams_data[
        ["prd_jam", "WalltimeStart"]], on="prd_jam")
    pdf_recent_penalties["Time in Jam"] = pdf_recent_penalties["Time"] - pdf_recent_penalties["WalltimeStart"]
    pdf_recent_penalties["Time in Jam"] = [convert_millis_to_min_sec_str(x)
                                           for x in pdf_recent_penalties["Time in Jam"]]
    pdf_recent_penalties["Status"] = pdf_recent_penalties["Status"].astype(PENALTYSTATUS_ORDER_DTYPE)

    # Make pretty names for columns
    pdf_recent_penalties = pdf_recent_penalties.rename(columns={
        "PeriodNumber": "Period",
        "JamNumber": "Jam",
        "team": "Team",
        "penalty_name": "Penalty"})
    # restrict, order columns
    pdf_recent_penalties = pdf_recent_penalties[[
        "Team", "Name", "Penalty", "Status", "Period", "Jam", "Time in Jam"]]

    return pdf_recent_penalties 


class BothTeamsRosterTable(DerbyTable):
    """Table with rosters for both teams
    """
    name: str = "Team Rosters"
    description: str = "Rosters of both teams"
    can_show_before_game_start: bool = True

    def prepare_table_dataframe(self, derby_game: DerbyGame) -> pd.DataFrame: 
        """Combine the referee and NSO rosters into one table

        Args:
            derby_game (DerbyGame): Derby Game

        Returns:
            pd.DataFrame: Table with all officials
        """
        pdf_team1_roster = format_team_roster_fordisplay(
            derby_game, derby_game.team_1_name, anonymize_names=self.anonymize_names)
        pdf_team1_roster.index = range(len(pdf_team1_roster))
        pdf_team2_roster = format_team_roster_fordisplay(
            derby_game, derby_game.team_2_name, anonymize_names=self.anonymize_names)
        pdf_team2_roster.index = range(len(pdf_team2_roster))
        pdf_bothteams_roster = pd.concat([pdf_team1_roster, pdf_team2_roster], axis=1)
        pdf_bothteams_roster = pdf_bothteams_roster.fillna("")
        return pdf_bothteams_roster


class BothTeamsRosterWithJammerAndPivot(DerbyTable):
    """team roster dataframe with jammers and pivots
    """
    name: str = "Team Rosters with Jammers and Pivots"
    description: str = "Rosters of both teams, with Jammers and pivots indicated"
    can_show_before_game_start: bool = False

    def prepare_table_dataframe(self, derby_game: DerbyGame) -> pd.DataFrame: 
        pdf_team_roster1 = format_team_roster_fordisplay(derby_game, derby_game.team_1_name,
                                                        show_jammers_and_pivots=True)
        pdf_team_roster1.index = range(len(pdf_team_roster1))
        pdf_team_roster2 = format_team_roster_fordisplay(derby_game, derby_game.team_2_name,
                                                        show_jammers_and_pivots=True)
        pdf_team_roster2.index = range(len(pdf_team_roster2))

        pdf_bothteams_roster = pd.concat([pdf_team_roster1, pdf_team_roster2], axis=1)
        return pdf_bothteams_roster


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
        pdf_jammer_counts = pdf_jammer_counts.rename(columns={"count": "Jammed"})
        pdf_jammer_counts["Number"] = pdf_jammer_counts.index
        pdf_team_roster = pdf_team_roster.merge(pdf_jammer_counts, on="Number", how="left")
        pdf_team_roster["Jammed"] = pdf_team_roster["Jammed"].fillna(0).astype(int)
        # now do pivot
        pdf_pivot_counts = pd.DataFrame(derby_game.pdf_jams_data[f"pivot_number_{team_number}"].value_counts())
        pdf_pivot_counts = pdf_pivot_counts.rename(columns={f"count": "Pivoted"})
        pdf_pivot_counts["Number"] = pdf_pivot_counts.index
        pdf_team_roster = pdf_team_roster.merge(pdf_pivot_counts, on="Number", how="left")
        pdf_team_roster["Pivoted"] = pdf_team_roster["Pivoted"].fillna(0).astype(int)

    pdf_team_roster = pdf_team_roster.drop(columns=["Number", "Name"])


    return pdf_team_roster