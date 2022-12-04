__author__ = "Damon May"

import json
import pandas as pd
from typing import Dict, Any, Tuple
from jamstats.data.game_data import DerbyGameFactory, DerbyGame
from jamstats.data.json_to_pandas import JsonDerbyGameFactory

class ScoreboardJsonFileDerbyGameFactory(DerbyGameFactory):
    """Build DerbyGame objects from a .json file
    """
    def __init__(self, filepath):
        game_json = read_game_data_json_file(filepath)
        self.json_derby_game_factory = JsonDerbyGameFactory(game_json)
        
    def get_derby_game(self) -> DerbyGame:
        """Build the derby game

        Returns:
            DerbyGame: derby game
        """
        return self.json_derby_game_factory.get_derby_game()


def read_game_data_json_file(filepath: str) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """Read game data from a json file.

    This method is trivial, just loads the json. Putting it here in case more
    complicated things tneed to happen later.

    Returns:
        Tuple[Dict[str, Any], pd.DataFrame]: Game data dict and jam-level data
    """
    with open(filepath) as game_file:
        game_json = json.load(game_file)
        return game_json