__author__ = "Damon May"

from typing import List
from matplotlib.figure import Figure
from jamstats.data.game_data import DerbyGame
import logging
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
from jamstats.plots.plot_util import prepare_to_plot, DEFAULT_THEME
from matplotlib.backends.backend_pdf import PdfPages


logger = logging.Logger(__name__)

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
    prepare_to_plot(theme=theme)
    figures = make_all_plots(derby_game, anonymize_names=anonymize_names)
    pdfout = PdfPages(out_filepath)
    logging.debug(f"Saving {len(figures)} figures to {out_filepath}")
    for figure in figures:
        pdfout.savefig(figure)
    pdfout.close()
    logging.debug(f"Wrote {out_filepath}")


def make_all_plots(derby_game: DerbyGame,
                   plot_skaterplots: bool = True,
                   anonymize_names: bool = True) -> List[Figure]:
    """Build all plots, suitable for exporting to a .pdf

    Args:
        derby_game (DerbyGame): a derby game
        plot_skaterplots (bool): Plot the plots with individually identifying skater info?
    Returns:
        List[Figure]: figures
    """
    figures = []
    plots_to_run = [
        plot_game_summary_table,
        plot_game_teams_summary_table,
        plot_cumulative_score_by_jam,
        plot_jam_lead_and_scores_period1,
    ]
    if max(derby_game.pdf_jams_data.PeriodNumber) >= 2:
        plots_to_run.append(plot_jam_lead_and_scores_period2)
    plots_to_run.extend([
        plot_jammers_by_team,
        plot_lead_summary])
    plots_to_run.append(histogram_jam_duration)

    for plot_func in plots_to_run:
        try:
            f = plot_func(derby_game)
            figures.append(f)
        except Exception as e:
            logger.warn(f"Failed to make jam plot {plot_func.__name__}: {e}")

    try:
        f = plot_team_penalty_counts(derby_game)
        figures.append(f)
    except Exception as e:
            logger.warn(f"Failed to make penalty plots: {e}")

    if plot_skaterplots:
        for plot_func in [plot_jammer_stats_team1, plot_jammer_stats_team2,
                          plot_skater_stats_team1, plot_skater_stats_team2]:
            try:
                f = plot_func(derby_game, anonymize_names=anonymize_names)
                figures.append(f)
            except Exception as e:
                logger.warn(f"Failed to make skater plot {plot_func.__name__}: {e}")
    return figures