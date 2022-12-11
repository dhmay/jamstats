
__author__ = "Damon May"

import seaborn as sns


def prepare_to_plot() -> None:
    """Prepare Seaborn to make pretty plots.
    """
    sns.set_context("talk")
    sns.set_style("white")