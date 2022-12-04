__author__ = "Damon May"

import json
import pandas as pd
from typing import Dict, Any, Tuple


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