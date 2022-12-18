__author__ = "Damon May"

import json
from typing import Dict, Any
from jamstats.data.game_data import DerbyGame
from jamstats.data.json_to_pandas import load_json_derby_game
import urllib
import logging
import io

logger = logging.Logger(__name__)

def load_derby_game_from_json_file(filepath) -> DerbyGame:
    """Load the derby game from a JSON file

    Args:
        filepath (str): file to load from

    Returns:
        DerbyGame: derby game
    """
    game_json = read_game_data_json_file(filepath)
    derby_game = load_json_derby_game(game_json)
    derby_game.game_data_dict["source_filepath"] = filepath
    return derby_game

def read_game_data_json_file(filepath: str) -> Dict[str, Any]:
    """Read game data from a json file.

    This method is trivial, just loads the json. Putting it here in case more
    complicated things tneed to happen later.

    Returns:
        Dict[str, Any]: Game JSON
    """
    try:
        with open(filepath) as game_file:
            game_json = json.load(game_file)
            return game_json
    except Exception as e:
        logger.warn("Failed to parse game JSON file. Trying Windows encoding...")
        with io.open(filepath, 'r', encoding='windows-1252') as game_file:
            game_json = json.load(game_file)
            return game_json

def load_inprogress_game_from_server(server: str, port: int) -> DerbyGame:
    """Connect to server at server:port, download the in-game JSON, make DerbyGame

    Args:
        server: server name, e.g., localhost
        port: server port, e.g., 8000

    Returns:
        DerbyGame: Derby game
    """
    game_json = load_game_json_from_server(server, port)
    derby_game = load_json_derby_game(game_json)
    derby_game.game_data_dict["source_filepath"] = "scoreboard-0-secs-ago.json"
    return derby_game

def load_game_json_from_server(
    server: str, port: int) -> Dict[str, Any]:
    """Read game data from the in-progress game on a server.

    Args:
        server: server name, e.g., localhost
        port: server port, e.g., 8000

    Returns:
        Dict[str, Any]: Game JSON
    """
    with urllib.request.urlopen(
        f"http://{server}:{port}/SaveJSON/scoreboard-0-secs-ago.json") as response:
        game_json = json.load(response,
            encoding=response.headers.get_content_charset())
    return game_json