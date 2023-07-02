
__author__ = "Damon May"

from jamstats.data.game_data import DerbyGame
import logging
from abc import ABCMeta, abstractmethod
import pandas as pd
from pandas.io.formats.style import Styler
from jamstats.plots.plot_util import DerbyElement

logger = logging.Logger(__name__)


class DerbyHTMLElement(DerbyElement):
    """Base class for all HTML elements
    """
    name: str = "DerbyHTMLElement"
    description: str = "A Derby HTML Element"
    can_render_html: bool = True

    def __init__(self, anonymize_names: bool = False,
                 anonymize_teams: bool = False) -> None:
        self.anonymize_names = anonymize_names
        self.anonymize_teams = anonymize_teams
        pass

    @abstractmethod
    def build_html(self, derby_game: DerbyGame) -> str: 
        """Build the HTML

        Args:
            derby_game (DerbyGame): Derby Game

        Returns:
            str: HTML
        """
        pass

class DerbyTable(DerbyHTMLElement):
    """Base class for all Tables.
    A DerbyTable is a special HTMLElement that represents the data in a Pandas DataFrame.
    """
    name = "DerbyTable"
    description = "A Derby Table"
    section = "Tables"
    def __init__(self, anonymize_names: bool = False,
                 anonymize_teams: bool = False) -> None:
        super(DerbyTable, self).__init__(anonymize_names=anonymize_names,
                         anonymize_teams=anonymize_teams)

    @abstractmethod
    def prepare_table_dataframe(self, derby_game: DerbyGame) -> pd.DataFrame: 
        pass

    def prepare_table_styler(self, derby_game: DerbyGame,
                             pdf_table: pd.DataFrame) -> Styler: 
        """Prepare the table styler. By default, this just hides the index.
        But subclasses can override this to do more.

        Args:
            derby_game (DerbyGame): Derby Game, in case it's needed
            pdf_table (pd.DataFrame): table to format

        Returns:
            Styler: styler
        """
        return pdf_table.style.hide_index()

    def build_html(self, derby_game: DerbyGame) -> str: 
        """Build the table HTML: prepare the data, then style it.

        Args:
            derby_game (DerbyGame): Derby Game

        Returns:
            Figure: matplotlib figure
        """
        pdf_table = self.prepare_table_dataframe(derby_game)
        styler = self.prepare_table_styler(derby_game, pdf_table)
        return styler.to_html()

