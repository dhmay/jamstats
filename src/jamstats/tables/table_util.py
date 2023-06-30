
__author__ = "Damon May"

from jamstats.data.game_data import DerbyGame
import logging
from abc import ABCMeta, abstractmethod
import pandas as pd
from pandas.io.formats.style import Styler

logger = logging.Logger(__name__)

class DerbyTable(DerbyHTMLElement):
    """Base class for all Tables.
    A DerbyTable is a special HTMLElement that represents the data in a Pandas DataFrame.
    """
    def __init__(self, anonymize_names: bool = False,
                 anonymize_teams: bool = False) -> None:
        super().__init__(self, anonymize_names=anonymize_names,
                         anonymize_teams=anonymize_teams)
        self.name = "DerbyTable"
        self.description = "A Derby Table"


    @abstractmethod
    def prepare_table_dataframe(self, derby_game: DerbyGame) -> pd.DataFrame: 
        pass

    def prepare_table_styler(self, derby_game: DerbyGame,
                             pdf_table: pd.DataFrame) -> Styler: 
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


class DerbyHTMLElement(ABCMeta):
    """Base class for all HTML elements
    """
    def __init__(self, anonymize_names: bool = False,
                 anonymize_teams: bool = False) -> None:
        self.name = "DerbyHTMLElement"
        self.anonymize_names = anonymize_names
        self.anonymize_teams = anonymize_teams
        pass

    def get_name(self) -> str:
        """Get the name of the table.
        Returns:
            str: name
        """
        return self.name

    @abstractmethod
    def build_html(self, derby_game: DerbyGame) -> str: 
        """Build the HTML

        Args:
            derby_game (DerbyGame): Derby Game

        Returns:
            str: HTML
        """
        pass