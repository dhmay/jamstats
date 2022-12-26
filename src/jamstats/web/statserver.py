__author__ = "Damon May"

from flask import (Flask, request, render_template_string, send_file)
from jamstats.data.game_data import DerbyGame
import importlib.resources
from jamstats.plots.plot_util import prepare_to_plot
from jamstats.plots.jamplots import (
        plot_game_summary_table,
        plot_game_teams_summary_table,
        plot_cumulative_score_by_jam,
        plot_jam_lead_and_scores_period1,    
        plot_jam_lead_and_scores_period2,
        plot_jammers_by_team,
        plot_lead_summary,
        histogram_jam_duration,
        plot_team_penalty_counts,
)
from jamstats.plots.skaterplots import (
    plot_jammer_stats_team1,
    plot_jammer_stats_team2,
    plot_skater_stats_team1,
    plot_skater_stats_team2,
)
import matplotlib
from datetime import datetime
import io
import logging
import pkg_resources

logger = logging.Logger(__name__)

app = Flask(__name__.split('.')[0])
app.jamstats_plots = None

PLOT_NAME_FUNC_MAP = {
    "Game Summary": plot_game_summary_table,
    "Teams Summary": plot_game_teams_summary_table,
    "Cumulative Score by Jam": plot_cumulative_score_by_jam,
    "Lead and Scores (Period 1)": plot_jam_lead_and_scores_period1,
    "Lead and Scores (Period 2)": plot_jam_lead_and_scores_period2,
    "Jammer Summery": plot_jammers_by_team,
    "Lead Summary": plot_lead_summary,
    "Jam Duration": histogram_jam_duration,
    "Team Penalty Counts": plot_team_penalty_counts,
    "Team 1 Jammers": plot_jammer_stats_team1,
    "Team 2 Jammers": plot_jammer_stats_team2,
    "Team 1 Skaters": plot_skater_stats_team1,
    "Team 2 Skaters": plot_skater_stats_team2,
}

def start(port: int, debug: bool = True) -> None:
    matplotlib.use('Agg')
    app.plotname_image_map = {}
    app.plotname_time_map = {}
    prepare_to_plot()
    app.run(host="127.0.0.1", port=port, debug=debug)


def set_game(derby_game: DerbyGame):
    app.derby_game = derby_game
    app.game_update_time = datetime.now()


@app.route("/")
def index():
    args = request.args
    
    plotlink_html_chunks = [
        f"<li><a href='/?plot_name={plot_name}'>{plot_name}</a></li>"
        for plot_name in PLOT_NAME_FUNC_MAP
    ]
    plot_link_html = "<ul>\n" + "\n".join(plotlink_html_chunks) + "</ul>\n"
    plot_name = args["plot_name"] if "plot_name" in args else "Game Summary"

    game_update_time_str = app.game_update_time.strftime("%Y-%m-%d, %H:%M:%S")
    jamstats_version = pkg_resources.require("jamstats")[0].version

    return render_template_string(f'''<!doctype html>
    <html>
        <head title="Jamstats">
        </head>
        <body>
            <table>
                <tr>
                    <th align="left" valign="top" width="200">
                        <table>
                            <tr>
                                <th>
                                    <img src="logo" width="200">
                                    <br>
                                    version {jamstats_version}
                                </th>
                            </tr>
                            <tr>
                                <th align="left" valign="top" bgcolor="lightgray" width="200">
                                    <p>Updated {game_update_time_str}</p>
                                    <p>{plot_link_html}</p>
                                </th>
                            </tr>
                        </table>
                    </th>
                    <th>
                        <p><img src="fig/{plot_name}" width="1000"/></p>
                    </th>
                </tr>
            </table>
        </body>
    </html>
    ''')

@app.route("/logo")
def show_logo():
    # add logo to table plots
    with importlib.resources.path("jamstats.resources", "jamstats_logo.png") as template_file:
        return send_file(open(template_file, "rb"), mimetype='image/png')

@app.route("/fig/<plot_name>")
def plot_figure(plot_name: str):
    """Plot a figure.

    Currently, very inefficient: this method makes the figure again only when necessary,
    but it *renders* it every time. I'm doing that because earlier I tried saving it to a
    buffer and reading the buffer every time, but somehow the buffer got closed between
    calls (multithreading?)

    Args:
        plot_name (str): name of plot to plot

    """
    if app.derby_game is None:
        return "No derby game set."

    should_rebuild = True
    if plot_name in app.plotname_time_map:
        mtime = app.plotname_time_map[plot_name]
        if mtime >= app.game_update_time:
            should_rebuild = False
    if should_rebuild: 
        logger.debug(f"Rebuilding {plot_name}")
        f = PLOT_NAME_FUNC_MAP[plot_name](app.derby_game)
        app.plotname_image_map[plot_name] = f
        app.plotname_time_map[plot_name] = datetime.now() 
    f = app.plotname_image_map[plot_name]
    buf = io.BytesIO()
    f.savefig(buf, format="png")
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

