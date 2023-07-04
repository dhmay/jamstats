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
from jamstats.plots.plot_together import ELEMENTS_CLASSES

import matplotlib
import io
import logging


logger = logging.Logger(__name__)

app = Flask(__name__.split('.')[0])
app.jamstats_plots = None

#protect against very large file uploads -- 10MB
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024


ELEMENT_NAME_CLASS_MAP = {element_class.name: element_class for element_class in ELEMENTS_CLASSES}

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
            plotname_image_map = {}
            for plot_name in ELEMENT_NAME_CLASS_MAP.keys():
                element = ELEMENT_NAME_CLASS_MAP[plot_name]()
                try:
                    f = element.plot(app.derby_game)
                    buf = io.BytesIO()
                    f.savefig(buf, format="png")
                    buf.seek(0)
                    image = b64encode(buf.getvalue()).decode("utf-8")
                    plotname_image_map[plot_name] = image
                except Exception as e:
                    print(f"Error plotting {plot_name}: {e}")
                    plotname_image_map[plot_name] =  None
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
