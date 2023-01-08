__author__ = "Damon May"

from flask import (Flask, request, render_template_string, send_file)
from jamstats.data.game_data import DerbyGame
from jamstats.plots.plot_util import prepare_to_plot
from jamstats.util.resources import (
    get_jamstats_logo_image, get_jamstats_version
)
import inspect


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
from jamstats.io.scoreboard_json_io import load_inprogress_game_from_server
import matplotlib
from datetime import datetime
import io
import logging
import socket


MIN_REQUERY_SERVER_SECONDS = 30

logger = logging.Logger(__name__)

app = Flask(__name__.split('.')[0])
app.jamstats_plots = None

PLOT_NAME_FUNC_MAP = {
    "Game Summary": plot_game_summary_table,
    "Teams Summary": plot_game_teams_summary_table,
    "Cumulative Score by Jam": plot_cumulative_score_by_jam,
    "Lead and Scores (Period 1)": plot_jam_lead_and_scores_period1,
    "Lead and Scores (Period 2)": plot_jam_lead_and_scores_period2,
    "Jammer Summary": plot_jammers_by_team,
    "Lead Summary": plot_lead_summary,
    "Jam Duration": histogram_jam_duration,
    "Team Penalty Counts": plot_team_penalty_counts,
    "Team 1 Jammers": plot_jammer_stats_team1,
    "Team 2 Jammers": plot_jammer_stats_team2,
    "Team 1 Skaters": plot_skater_stats_team1,
    "Team 2 Skaters": plot_skater_stats_team2,
}

def start(js_port: int, debug: bool = True, scoreboard_server: str = None,
          scoreboard_port: int = None, anonymize_names=False,
          theme="white") -> None:
    matplotlib.use('Agg')
    app.plotname_image_map = {}
    app.plotname_time_map = {}
    prepare_to_plot(theme=theme)
    app.scoreboard_server = scoreboard_server
    app.scoreboard_port = scoreboard_port
    app.ip = socket.gethostbyname(socket.gethostname())
    app.port = js_port
    app.anonymize_names=anonymize_names
    print(f"Starting jamstats server at http://{app.ip}:{app.port}  ;  Scoreboard port is '{app.scoreboard_port}'")
    app.run(host=app.ip, port=port, debug=debug)


def set_game(derby_game: DerbyGame):
    app.derby_game = derby_game
    app.game_update_time = datetime.now()


@app.route("/")
def index():
    if app.scoreboard_server is not None:
        # check and see if it's been long enough to requery the server
        seconds_since_update = (datetime.now() - app.game_update_time).total_seconds()
        if  seconds_since_update >= MIN_REQUERY_SERVER_SECONDS:
            logger.debug(f"Connecting to server {app.scoreboard_server}, "
                         "port {app.scoreboard_port}...")
            print(f"connecting to scoreboard server at http://{app.scoreboard_server}:{app.scoreboard_port} ")
            try:
                derby_game = load_inprogress_game_from_server(
                    app.scoreboard_server, app.scoreboard_port)
                set_game(derby_game)
            except Exception as e:
                logger.error("Failed to download in-game data from server "
                            f"{app.scoreboard_server}:{app.scoreboard_port}: {e}")

    args = request.args
    
    plotlink_html_chunks = [
        f"<li><a href='/?plot_name={plot_name}'>{plot_name}</a></li>"
        for plot_name in PLOT_NAME_FUNC_MAP
    ]
    plot_link_html = "<ul>\n" + "\n".join(plotlink_html_chunks) + "</ul>\n"
    plot_name = args["plot_name"] if "plot_name" in args else "Game Summary"

    game_update_time_str = app.game_update_time.strftime("%Y-%m-%d, %H:%M:%S")

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
                                    Jamstats version {get_jamstats_version()}
                                </th>
                            </tr>
                            <tr>
                                <th align="left" valign="top" bgcolor="lightgray" width="200">
                                    <p>Updated {game_update_time_str}</p>
                                    <p>{plot_link_html}</p>
                                </th>
                            </tr>
                            <tr>
                                <th align="left" valign="top" bgcolor="gray" width="200">
                                    <p>jamstats server:port :</p>
                                    <p>{app.ip}:{app.port}</p>
                                </th>
                            </tr>
                        </table>
                    </th>
                    <th>
                        <p><H2>{plot_name}</H2></p>
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
    return send_file(io.BytesIO(get_jamstats_logo_image()), mimetype='image/png')

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

        plotfunc = PLOT_NAME_FUNC_MAP[plot_name]

        # add anonymize arg if the function has it
        kwargs = {}
        sig = inspect.signature(plotfunc)
        if "anonymize_names" in sig.parameters:
            kwargs["anonymize_names"] = app.anonymize_names

        f = plotfunc(app.derby_game, **kwargs)

        app.plotname_image_map[plot_name] = f
        app.plotname_time_map[plot_name] = datetime.now() 
    f = app.plotname_image_map[plot_name]
    buf = io.BytesIO()
    f.savefig(buf, format="png")
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

