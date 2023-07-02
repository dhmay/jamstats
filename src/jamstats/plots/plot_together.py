__author__ = "Damon May"

from typing import List
from jamstats.data.game_data import DerbyGame
import logging
from jamstats.tables.jamstats_tables import (
    GameSummaryTable,
    GameTeamsSummaryTable,
    BothTeamsRosterWithJammerAndPivot,
)
from jamstats.plots.basic_plots import (
    CumScoreByJamPlot,
    JammerStatsPlotTeam1,
    JammerStatsPlotTeam2,
    SkaterStatsPlotTeam1,
    SkaterStatsPlotTeam2,
    PenaltyCountsPlotByTeam,
    SimpleLeadSummaryPlot,
)

from jamstats.plots.advanced_plots import (
    PerJamDataPeriod1Plot,
    PerJamDataPeriod2Plot,
    TimeToInitialPassPlot,
    JammersByTeamPlot,
)
from jamstats.plots.plot_util import prepare_to_plot, DEFAULT_THEME
from jamstats.util.resources import (
    get_jamstats_logo_image,
)
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import pyplot as plt
from PIL import Image
import io

ELEMENTS_CLASSES = [
    # basic tables
    GameSummaryTable,
    GameTeamsSummaryTable,
    # basic plots
    CumScoreByJamPlot,
    JammerStatsPlotTeam1,
    JammerStatsPlotTeam2,
    SkaterStatsPlotTeam1,
    SkaterStatsPlotTeam2,
    PenaltyCountsPlotByTeam,
    SimpleLeadSummaryPlot,
    # advanced plots
    PerJamDataPeriod1Plot,
    PerJamDataPeriod2Plot,
    TimeToInitialPassPlot,
    JammersByTeamPlot,
    # roster table
    BothTeamsRosterWithJammerAndPivot,
]

logger = logging.Logger(__name__)


def make_all_plots(derby_game: DerbyGame,
                   anonymize_names: bool = False,
                   theme: str = DEFAULT_THEME) -> List[plt.Figure]:
    prepare_to_plot(theme=theme)
    figures = []
    for element_class in ELEMENTS_CLASSES:
        element = element_class(anonymize_names=anonymize_names)
        f = element.plot(derby_game)
        figures.append(f)

    # add logo to tables.
    im_bytes = get_jamstats_logo_image()
    im = Image.open(io.BytesIO(im_bytes))
    for f, aclass in zip(*[figures, ELEMENTS_CLASSES]):
        # this check is brittle
        if aclass.section == "Tables":
            newax = f.add_axes([0.425,0.9,0.15,0.15], anchor='SE', zorder=1)
            newax.axis('off')
            newax.imshow(im)    
    return figures

def save_game_plots_to_pdf(derby_game: DerbyGame,
                           out_filepath: str,
                           anonymize_names: bool = False,
                           theme: str = DEFAULT_THEME) -> None:
    """Read in a jams .tsv file, make all the plots, write to a .pdf

    Args:
        in_filepath (str): jams .tsv filepath
        out_filepath (str): output .pdf filepath
        anonymize_names (bool): anonymize skater names
    """
    figures = make_all_plots(derby_game, anonymize_names=anonymize_names, theme=theme)

    pdfout = PdfPages(out_filepath)
    logging.debug(f"Saving {len(figures)} figures to {out_filepath}")
    for figure in figures:
        pdfout.savefig(figure)
    pdfout.close()
    logging.debug(f"Wrote {out_filepath}")
