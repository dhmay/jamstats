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


DEFAULT_N_RECENT_PENALTIES = 10


logger = logging.Logger(__name__)


# ordered dtype so we can sort easily by penalty status
PENALTYSTATUS_ORDER_DTYPE = cat_size_order = CategoricalDtype(
    ['Serving', 'Not Yet', 'Served'], 
    ordered=True
)


def plot_jammers_by_team(derby_game: DerbyGame) -> Figure:
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
                }),
                ax=ax, palette=team_color_palette)
    # word-wrap too-long team names
    wordwrap_x_labels(ax)
    ax.set_title("Jammers per team")

    ax = axes[1]
    sns.violinplot(x="team", y="jam_count", data=pdf_jammer_jamcounts, cut=0, ax=ax,
                   palette=team_color_palette, inner="stick")
    ax.set_title("Jams per jammer")
    ax.set_ylabel("Jams per jammer")
    # word-wrap too-long team names
    wordwrap_x_labels(ax)

    pdf_jammer_summary_1 = pdf_jams_data.groupby(
        "jammer_name_1").agg({"JamScore_1": "mean", "Number": "count"}).rename(
        columns={"JamScore_1": "mean_jam_score", "Number": "n_jams"})
    pdf_jammer_summary_1.index = range(len(pdf_jammer_summary_1))
    pdf_jammer_summary_2 = pdf_jams_data.groupby(
        "jammer_name_2").agg({"JamScore_2": "mean", "Number": "count"}).rename(
        columns={"JamScore_2": "mean_jam_score", "Number": "n_jams"}) 
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


def get_officials_roster_html(derby_game: DerbyGame,
                              anonymize_names: bool = False) -> str:
    """Get a table of the officials as html

    Args:
        derby_game (DerbyGame): derby game

    Returns:
        str: html table
    """
    html = "<table><tr><td valign='top'><H3>Referees</H3>"
    if len(derby_game.pdf_ref_roster) == 0:
        html = html + "No Data"
    else:
        html = html + derby_game.pdf_ref_roster.style.hide_index().to_html()
    html = html + "</td><td><td valign='top'><H3>NSOs</H3>"
    if len(derby_game.pdf_nso_roster) == 0:
        html = html + "No Data"
    else:
        html = html + derby_game.pdf_nso_roster.style.hide_index().to_html()
    html = html + "</td></tr></table>"
    return html


def get_caller_dashboard_html(derby_game: DerbyGame, anonymize_names: bool = False) -> str:
    """Build a dashboard for the announcer

    Args:
        derby_game (DerbyGame): derby game
        anonymize_names (bool, optional): anonymize names. Defaults to False.
    
    Returns:
        str: html dashboard
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
    styler = pdf_game_teams_summary.style.set_table_attributes("style='display:inline'").hide_index()
    html_game_summary = styler.render()

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
                                                  anonymize_names=anonymize_names)
    
    result =  "<p>" + html_game_summary + "</p><p>" + html_current_jam

    if len(pdf_jams_sorted_desc) > 1:
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
            subset=["Pen. Count"]).hide_index()
        styler = styler.set_table_attributes("style='display:inline'").hide_index()
        table_htmls.append(styler.render())

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
    """Get a table of one team's current skaters as html

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
    pdf_skater_penaltycount = pdf_skater_penaltycount.rename(columns={"Name": "Pen. Count"})
    pdf_skater_penaltycount["Name"] = pdf_skater_penaltycount.index
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


def get_game_summary_html(derby_game: DerbyGame) -> str:
    """Get a game summary table as html

    Args:
        derby_game (DebyGame): derby game

    Returns:
        str: html table
    """
    pdf_game_summary = derby_game.extract_game_summary()
    styler = pdf_game_summary.style.set_table_attributes("style='display:inline'").hide_index()
    return styler.render()


def plot_game_summary_table(derby_game: DerbyGame) -> Figure:
    """Make a table figure out of the game summary dataframe,
    suitable for writing to a .pdf

    Args:
        derby_game (DerbyGame): a derby game

    Returns:
        Figure: table figure
    """
    pdf_game_summary = derby_game.extract_game_summary()

    f = plt.figure(figsize=(8,6))
    ax = plt.subplot(111)
    ax.axis('off')
    ax.table(cellText=pdf_game_summary.values,
             colLabels=pdf_game_summary.columns, bbox=[0,0,1,1])
    return f


def get_game_teams_summary_html(derby_game: DerbyGame, anonymize_names: bool = False) -> str:
    """Get a game teams summary table as html

    Args:
        derby_game (DerbyGame): derby game

    Returns:
        str: html table
    """
    pdf_game_teams_summary = derby_game.extract_game_teams_summary().transpose()
    pdf_game_teams_summary = pdf_game_teams_summary.rename({"n_scoring_trips": "Scoring trips"})
    pdf_game_teams_summary["Team"] = pdf_game_teams_summary.index
    pdf_game_teams_summary = pdf_game_teams_summary[["Team", 0, 1]]
    pdf_game_teams_summary = pdf_game_teams_summary.rename(columns={0: derby_game.team_1_name,
                                                                    1: derby_game.team_2_name})
    pdf_game_teams_summary = pdf_game_teams_summary[pdf_game_teams_summary.Team != "Team"]
    styler = pdf_game_teams_summary.style.set_table_attributes("style='display:inline'").hide_index()
    return styler.render()

def plot_game_teams_summary_table(derby_game: DerbyGame, anonymize_names=False) -> Figure:
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


def get_team1_roster_html(derby_game: DerbyGame,
                          anonymize_names: bool = False) -> str:
    return get_team_roster_html(derby_game, derby_game.team_1_name, anonymize_names=anonymize_names)

def get_team2_roster_html(derby_game: DerbyGame,
                          anonymize_names: bool = False) -> str:
    return get_team_roster_html(derby_game, derby_game.team_2_name, anonymize_names=anonymize_names)

def get_bothteams_roster_html(derby_game: DerbyGame,
                              anonymize_names: bool = False) -> str:
    """Get a html table of both teams' rosters

    Args:
        derby_game (DerbyGame): a derby game

    Returns:
        str: html table
    """
    pdf_team1_roster = format_team_roster_fordisplay(derby_game, derby_game.team_1_name, anonymize_names=anonymize_names)
    pdf_team1_roster.index = range(len(pdf_team1_roster))
    pdf_team2_roster = format_team_roster_fordisplay(derby_game, derby_game.team_2_name, anonymize_names=anonymize_names)
    pdf_team2_roster.index = range(len(pdf_team2_roster))
    pdf_bothteams_roster = pd.concat([pdf_team1_roster, pdf_team2_roster], axis=1)
    pdf_bothteams_roster = pdf_bothteams_roster.fillna("")
    styler = pdf_bothteams_roster.style.set_table_attributes("style='display:inline'").hide_index()
    return styler.render()

def get_team_roster_html(derby_game: DerbyGame, team_name: str) -> str:
    """Build html table out of team roster

    Args:
        derby_game (DerbyGame): derby game
        team_name (str): team name

    Returns:
        str: HTML table
    """
    pdf_team_roster = format_team_roster_fordisplay(derby_game, team_name)
    styler = pdf_team_roster.style.set_table_attributes("style='display:inline'").hide_index()
    return styler.render()


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
    pdf_team_roster = pdf_team_roster[["RosterNumber", "Name"]]
    pdf_team_roster = pdf_team_roster.rename(columns={"Name": "Name", "RosterNumber": "Number"})
    if anonymize_names:
        name_dict = build_anonymizer_map(set(pdf_team_roster.Name))
        pdf_team_roster["Name"] = [name_dict[skater] for skater in pdf_team_roster.Name]  
    pdf_team_roster = pdf_team_roster.sort_values("Number")
    pdf_team_roster[f"{team_name} Skater"] = pdf_team_roster["Number"].astype(str) + " " + pdf_team_roster["Name"]

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


def get_recent_penalties_html(derby_game: DerbyGame,
                              n_penalties_for_table: int = DEFAULT_N_RECENT_PENALTIES,
                              anonymize_names: bool = False) -> str:
    """Make html table out of most recent penalties"""
    pdf_recent_penalties = make_recent_penalties_dataframe(derby_game,
                                                           n_penalties_for_table=n_penalties_for_table)
    if anonymize_names:
        name_dict = build_anonymizer_map(set(pdf_recent_penalties.Name))
        pdf_recent_penalties["Name"] = [name_dict[skater] for skater in pdf_recent_penalties.Name] 
    # add colors
    map_team_to_color = lambda team: f"color: {derby_game.team_color_1}" if team == derby_game.team_1_name \
        else f"color: {derby_game.team_color_2}" if team == derby_game.team_2_name \
        else ''
    styler = pdf_recent_penalties.style.applymap(map_team_to_color, subset=["Team"]).hide_index()

    # if either team is white, don't use white background.
    # This will break if white plays gray
    #if derby_game.team_color_1.lower() == "#ffffff" or derby_game.team_color_2.lower() == "#ffffff":
    #    styler = styler.set_properties(**{'background-color': 'gray'})
    return styler.render(index=False)


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
    pdf_penalty_counts = pdf_penalty_counts.sort_values(["Penalty", "team_number"])

    penalties_inorder = sorted(list(set(pdf_penalty_counts.Penalty)))
    
    f, ax = plt.subplots()

    if len(pdf_penalty_counts) > 0:
        sns.barplot(y="Penalty", x="Count", data=pdf_penalty_counts,
                    hue="team", ax=ax, palette=team_color_palette)
        for i, row in pdf_penalty_counts.iterrows():
            offset = .2 if row["team"] == derby_game.team_1_name else -.2
            ax.text(.5, penalties_inorder.index(row["Penalty"]) + offset, row["Count"], size="small",
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
