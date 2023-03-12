__author__ = "Damon May"

from flask import (Flask, request, render_template_string, render_template, send_file)
from jamstats.data.game_data import DerbyGame
from jamstats.plots.plot_util import prepare_to_plot
from jamstats.util.resources import (
    get_jamstats_logo_image, get_jamstats_version
)
from jamstats.data.json_to_pandas import load_json_derby_game
from jamstats.io.scoreboard_server_io import ScoreboardClient, GameStateListener
import inspect
import time
import _thread
import traceback
from engineio.async_drivers import gevent

from jamstats.plots.jamplots import (
        get_game_summary_html,
        get_game_teams_summary_html,
        plot_cumulative_score_by_jam,
        plot_jam_lead_and_scores_period1,    
        plot_jam_lead_and_scores_period2,
        plot_jammers_by_team,
        plot_lead_summary,
        histogram_jam_duration,
        plot_team_penalty_counts,
        get_recent_penalties_html,
        get_bothteams_roster_html,
        get_current_skaters_html,
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
import socket
import sys, os
import webbrowser
from flask_socketio import SocketIO

#attempt to fix windows issue
#from gevent import monkey
#monkey.patch_all()

GAME_STATE_UPDATE_MINSECS = 5

logger = logging.Logger(__name__)

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("src"), "jamstats", relative_path)

# This is necessary for pyinstaller to find the templates folder
static_folder = resource_path('static')
template_folder = resource_path('templates')
print(f"static_folder={static_folder}, template_folder={template_folder}")

app = Flask(__name__.split('.')[0], static_url_path="", static_folder=static_folder,
            template_folder=template_folder)
print("Flask app built.")
app.jamstats_plots = None

PLOT_SECTION_NAME_FUNC_MAP = {
    "Tables": {
        #"Game Summary": get_game_summary_html,
        "Current Skaters": get_current_skaters_html,
        "Teams Summary": get_game_teams_summary_html,
        "Recent Penalties": get_recent_penalties_html,
        "Roster": get_bothteams_roster_html,
    },
    "Basic Plots": {
        "Score by Jam": plot_cumulative_score_by_jam,
        "Team Penalty Counts": plot_team_penalty_counts,
        "Team 1 Jammers": plot_jammer_stats_team1,
        "Team 2 Jammers": plot_jammer_stats_team2,
        "Team 1 Skaters": plot_skater_stats_team1,
        "Team 2 Skaters": plot_skater_stats_team2,
    },
    "Advanced Plots": {
        "Lead Summary": plot_lead_summary,
        "Jam Details (Period 1)": plot_jam_lead_and_scores_period1,
        "Jam Details (Period 2)": plot_jam_lead_and_scores_period2,
        "Jammer Summary": plot_jammers_by_team,
    }
    #    "Jam Duration": histogram_jam_duration,
}
PLOT_NAME_FUNC_MAP = {}
for section_name, amap in PLOT_SECTION_NAME_FUNC_MAP.items():
    for name, func in amap.items():
        PLOT_NAME_FUNC_MAP[name] = func
PLOT_SECTION_NAMES_MAP = {
    section: list(amap.keys()) for section, amap in PLOT_SECTION_NAME_FUNC_MAP.items()
}
ALL_PLOT_NAMES = list(PLOT_NAME_FUNC_MAP.keys())

HTML_PLOT_NAMES = [
    "Game Summary",
    "Current Skaters",
    "Teams Summary",
    "Recent Penalties",
    "Roster",
]
PLOT_NAME_TYPE_MAP = {
    plot_name: "html" if plot_name in HTML_PLOT_NAMES else "figure"
    for plot_name in ALL_PLOT_NAMES
}

class UpdateWebclientGameStateListener(GameStateListener):
    def __init__(self, min_refresh_secs, socketio):
        self.last_update_time = datetime.now()
        self.min_refresh_secs = min_refresh_secs
        self.socketio = socketio

    def on_game_state_changed(self) -> None:
        """Called when the game state changes

        """
        logger.debug("UpdateWebclientGameStateListener.on_game_state_changed")
        # if enough time has passed, update the web client
        if self.socketio is not None:
            logger.debug("Emitting game_state_changed")
            self.socketio.emit("game_state_changed", {})
        else:
            logger.warning("Got game state change, but socketio is None!")


def start(port: int, scoreboard_client: ScoreboardClient = None,
          scoreboard_server: str = None,
          scoreboard_port: int = None,
          jamstats_ip: str = None, debug: bool = True, anonymize_names=False,
          theme="white", min_refresh_secs=GAME_STATE_UPDATE_MINSECS) -> None:
    """

    Args:
        port (int): port to start the jamstats server on
        scoreboard_client: scoreboard client to use to get game data
        jamstats_ip (str, optional): IP address to start on. Defaults to None. If None, will infer
        debug (bool, optional): _description_. Defaults to True.
        scoreboard_server (str, optional): _description_. Defaults to None.
        scoreboard_port (int, optional): _description_. Defaults to None.
        anonymize_names (bool, optional): _description_. Defaults to False.
        theme (str, optional): _description_. Defaults to "white".
    """
    matplotlib.use('Agg')
    app.plotname_image_map = {}
    app.plotname_time_map = {}
    prepare_to_plot(theme=theme)
    app.scoreboard_client = scoreboard_client
    app.scoreboard_server = scoreboard_server
    app.scoreboard_port = scoreboard_port
    app.min_refresh_secs = min_refresh_secs
    if jamstats_ip:
        app.ip = jamstats_ip
    else:
        app.ip = socket.gethostbyname(socket.gethostname())
    app.port = port
    app.anonymize_names=anonymize_names

    print("")
    print(f"Starting jamstats server...")
    print(f"Point your browser to:  http://{app.ip}:{app.port}")
    print("")
    # for communicating with clients
    
    print("Starting SocketIO Flask app...")
    app.socketio = SocketIO(app)

    # add listener to update webclient when game state changes
    if scoreboard_client is not None:
        print("Adding game state listener to scoreboard client")
        scoreboard_client.add_game_state_listener(UpdateWebclientGameStateListener(app.min_refresh_secs, app.socketio))

    print("Flask app started")
    app.socketio.run(app, host=app.ip, port=port, debug=debug)
    #app.run(host=app.ip, port=port, debug=debug)



def set_game(derby_game: DerbyGame):
    app.derby_game = derby_game
    app.game_update_time = datetime.now()


@app.route("/")
def index():
    logger.debug("Index page requested")
    if app.scoreboard_server is not None:
        logger.debug(f"Scoreboard server is {app.scoreboard_server}")
        # if we've got a client but that client isn't connected, we don't have a client.
        if app.scoreboard_client is not None and not app.scoreboard_client.is_connected_to_server:
            app.scoreboard_client = None
        if app.scoreboard_client is None:
            logger.debug("No scoreboard client. Creating one...")
            try:
                app.scoreboard_client = ScoreboardClient(app.scoreboard_server, app.scoreboard_port)
                # add listener to update webclient when game state changes
                app.scoreboard_client.add_game_state_listener(
                    UpdateWebclientGameStateListener(app.min_refresh_secs))
                _thread.start_new_thread(app.scoreboard_client.start, ())
                print("Connected to server. Waiting for game data...")
                time.sleep(2)
                if app.scoreboard_client.is_connected_to_server:
                    derby_game = load_json_derby_game(app.scoreboard_client.game_json_dict)
                    set_game(derby_game)
                    logger.debug("Updated derby game.")
                else:
                    app.scoreboard_client = None
                    return show_error("Error getting game from server. Will retry.")
            except Exception as e:
                app.scoreboard_client = None
                logger.error("Failed to download in-game data from server "
                            f"{app.scoreboard_server}:{app.scoreboard_port}: {e}")
                try:
                    traceback.print_stack()
                except Exception as e2:
                    print(f"Exception while printing stack: {e2}")
                return show_error("Exception while connecting to server. Will retry")
        else:
            logger.debug("Scoreboard client already exists. Checking for new game data...")
            if app.scoreboard_client.game_state_dirty:
                logger.debug("Game state is dirty. Rebuilding game.")
                # there's new game data. rebuild the game
                try:
                    derby_game = load_json_derby_game(app.scoreboard_client.game_json_dict)
                    app.scoreboard_client.game_state_dirty = False
                    set_game(derby_game)
                    logger.info("Updated game data from server.")
                except Exception as e:
                    logger.warning(f"Failed to update game data from server: {e}")
                    formatted_lines = traceback.format_exc().splitlines()
                    for line in formatted_lines:
                        print("EXC: " + line)
                    return show_error("Error connecting to server. Will retry")
            else:
                logger.debug("No new game data. Using existing game data.")

    game_update_time_str = app.game_update_time.strftime("%Y-%m-%d, %H:%M:%S")

    plot_name = request.args["plot_name"] if "plot_name" in request.args else "Roster"

    plotname_displayname_map = {
        plotname: (plotname.replace("Team 1", app.derby_game.team_1_name)
                   .replace("Team 2", app.derby_game.team_2_name))
        for plotname in ALL_PLOT_NAMES
    }

    return render_template("jamstats_gameplots.html", jamstats_version=get_jamstats_version(),
                           game_update_time_str=game_update_time_str,
                           jamstats_ip=app.ip, jamstats_port=app.port,
                           plot_name=plot_name,
                           section_name_map=PLOT_SECTION_NAMES_MAP,
                           plotname_displayname_map=plotname_displayname_map,
                           plotname_type_map=PLOT_NAME_TYPE_MAP,
                           plotname_func_map=PLOT_NAME_FUNC_MAP,
                           derby_game=app.derby_game,
                           min_refresh_secs=app.min_refresh_secs,
                           anonymize_names=app.anonymize_names)


def show_error(error_message: str):
    """show an error response

    Args:
        error_message (str): error message
    """
    return render_template_string(f'''<!DOCTYPE html>
    <html>
        <head title="Jamstats -- error">
            <script type="text/javascript">
            setTimeout(function () {{
                  location.reload();
                }}, {1000 * 15});
            </script>
            <noscript>
                <meta http-equiv="refresh" content="{15}" />
            </noscript>
        </head>
        <body>
            <p>
                <img src="logo" width="200">
                <br>
                Jamstats version {get_jamstats_version()}
            </p>
            <p>
            <H2>{error_message}</H2>
            </p>
        </body>
    </html>
                '''
                )


@app.route("/logo")
def show_logo():
    # add logo to table plots
    return send_file(io.BytesIO(get_jamstats_logo_image()), mimetype='image/png')


def generate_figure_html(app, plot_name: str) -> str:
    """Generate HTML for a figure.

    If a derby game isn't loaded, return a message saying so.

    Args:
        app: server app
        plot_name (str): name of plot to generate

    Returns:
        str: HTML for the plot
    """
    if app.derby_game is None:
        return "No derby game available..."

    return (f"<p><H2>{plot_name}</H2></p>\n" +
            f'<p><img src="fig/{plot_name}" width="1000"/></p>\n')


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