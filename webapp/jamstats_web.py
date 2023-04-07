__author__ = "Damon May"

from flask import (Flask, render_template, request, send_file, render_template_string)
from jamstats.data.game_data import DerbyGame
from jamstats.plots.plot_util import prepare_to_plot
from jamstats.util.resources import (
    get_jamstats_logo_image, get_jamstats_version
)
from jamstats.io.scoreboard_json_io import load_json_derby_game
import json
from base64 import b64encode
from jamstats.plots.plot_together import make_all_plots
from matplotlib.backends.backend_pdf import PdfPages
from io import BytesIO
from flask import make_response
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
import matplotlib
from datetime import datetime
import io
import logging
import socket


logger = logging.Logger(__name__)

app = Flask(__name__.split('.')[0])
app.jamstats_plots = None

#protect against very large file uploads -- 10MB
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

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

def start(debug: bool = False) -> None:
    """

    Args:
        port (int): port to start the jamstats server on
        jamstats_ip (str, optional): IP address to start on. Defaults to None. If None, will infer
        debug (bool, optional): _description_. Defaults to True.
    """
    matplotlib.use('Agg')
    prepare_to_plot()
    app.run(debug=debug)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == 'POST':
        print("displaying game plots")
        print(request.files)
        try:
            game_file_contents = request.files['game_file'].read().decode("utf-8", errors="replace") 
            game_json = json.loads(game_file_contents)
            app.derby_game = load_json_derby_game(game_json)
        except Exception as e:
            print(e)
            return render_template_string("""
                <html>
                <head><title>Error</title></head>
                <body>Error loading game file. Please check that the file is a valid JSON file.
                </body>
                </html>
                """)
        if request.form.get("mode") == "web":
            plotname_image_map = {
                plot_name: plot_figure(plot_name)
                for plot_name in PLOT_NAME_FUNC_MAP.keys()
            }
            return render_template("display_game_plots.html",
                                plotname_image_map=plotname_image_map,
                                jamstats_version=get_jamstats_version())
        else:
            figures = make_all_plots(app.derby_game)
            pdf_bytesio = BytesIO()
            pdfout = PdfPages(pdf_bytesio)
            for figure in figures:
                pdfout.savefig(figure)
            pdfout.close()
            response = make_response(pdf_bytesio.getvalue())
            # name the pdf
            json_filename = request.files['game_file'].filename
            pdf_filename = json_filename.replace(".json", ".pdf")
            if not pdf_filename.endswith(".pdf"):
                pdf_filename += ".pdf"
            response.headers.set('Content-Disposition', 'attachment', filename=pdf_filename)
            response.headers.set('Content-Type', 'application/pdf')
            return response
    else:
        return render_template("upload_game.html",
                               jamstats_version=get_jamstats_version())


@app.route("/logo")
def show_logo():
    # add logo to table plots
    return send_file(io.BytesIO(get_jamstats_logo_image()), mimetype='image/png')

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

    logger.debug(f"Rebuilding {plot_name}")

    plotfunc = PLOT_NAME_FUNC_MAP[plot_name]

    # add anonymize arg if the function has it
    kwargs = {}
    sig = inspect.signature(plotfunc)
    #if "anonymize_names" in sig.parameters:
    #    kwargs["anonymize_names"] = False
    #    print("****ANON FALSE")

    try:
        f = plotfunc(app.derby_game, **kwargs)
        buf = io.BytesIO()
        f.savefig(buf, format="png")
        buf.seek(0)
        image = b64encode(buf.getvalue()).decode("utf-8")
        return image
    except Exception as e:
        print(f"Error plotting {plot_name}: {e}")
        return None

