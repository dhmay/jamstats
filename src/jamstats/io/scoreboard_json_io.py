__author__ = "Damon May"

import json
import pandas as pd
from typing import Dict, Any, Tuple
from jamstats.data.game_data import DerbyGame
from jamstats.data.json_to_pandas import load_json_derby_game

def load_derby_game_from_json_file(filepath) -> DerbyGame:
    """Load the derby game from a JSON file

    Args:
        filepath (str): file to load from

    Returns:
        DerbyGame: derby game
    """
    game_json = read_game_data_json_file(filepath)
    return load_json_derby_game(game_json)


def read_game_data_json_file(filepath: str) -> Dict[str, Any]:
    """Read game data from a json file.

    This method is trivial, just loads the json. Putting it here in case more
    complicated things tneed to happen later.

    Returns:
        Tuple[Dict[str, Any], pd.DataFrame]: Game data dict and jam-level data
    """
    with open(filepath) as game_file:
        game_json = json.load(game_file)
        return game_json