
__author__ = "Damon May"

from jamstats.data.game_data import DerbyGame
import logging
from abc import ABCMeta, abstractmethod
import pandas as pd

logger = logging.Logger(__name__)


class DerbyTable(ABCMeta):
    """Base class for all Tables
    """
    def __init__(self) -> None:
        self.name = "DerbyTable"
        pass

    def get_name(self) -> str:
        """Get the name of the table.
        Returns:
            str: name
        """
        return self.name

    @abstractmethod
    def prepare_table_dataframe(self, derby_game: DerbyGame) -> pd.DataFrame: 
    

    @abstractmethod
    def plot(self, derby_game: DerbyGame) -> Figure: 
        """Plot the plot using the passed-in DerbyGame.

        Args:
            derby_game (DerbyGame): Derby Game

        Returns:
            Figure: matplotlib figure
        """
        pass