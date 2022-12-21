__author__ = "Damon May"

import pandas as pd
from typing import Dict
import csv
from jamstats.data.game_data import DerbyGame

def load_derby_game_from_tsv(filepath) -> DerbyGame:
    """Load a derby game from a TSV file.

    Args:
        filepath (str): filepath

    Returns:
        DerbyGame: derby game
    """
    game_data_dict = read_jams_tsv_header_dict(filepath)
    pdf_jams_data = read_jams_tsv_to_pandas(filepath)
    # todo: handle penalties and team colors
    derby_game = DerbyGame(pdf_jams_data, game_data_dict, None, None)
    derby_game.game_data_dict["source_filepath"] = filepath
    return derby_game

def read_jams_tsv_header_dict(filepath: str) -> Dict[str, str]:
    """Read the key-value pairs from '# ' comments at the top of the jams .tsv

    Args:
        filepath (str): filepath

    Returns:
        Dict[str, str]: key-value pairs
    """
    jams_metadata_dict = {}

    with open(filepath) as f:
        reader = csv.reader(f, delimiter="\t")
        while True:
            line = next(reader)[0]
            if line.startswith("# "):
                key, value = [x.strip() for x in line[2:].split("=")]
                jams_metadata_dict[key] = value
            else:
                break

    return jams_metadata_dict


def read_jams_tsv_to_pandas(filepath: str) -> pd.DataFrame:
    """Read a jams .tsv file into a Pandas dataframe.
    This is nearly trivial; making it a function to preserve
    flexibility for future format changes.

    Args:
        filepath (str): filepath

    Returns:
        pd.DataFrame: jams dataframe
    """
    pdf_jam_data = pd.read_csv(filepath, sep="\t", comment="#")
    return pdf_jam_data


def write_game_data_tsv(derby_game: DerbyGame, filepath: str) -> None:
    """Write game data to a .tsv file. Put some data into comments in the header.

    Args:
        game_data_dict (Dict[str, Any]): basic game info dict
        pdf_jam_data (pd.DataFrame): jam-level data
        filepath (str): path to write
    """
    with open(filepath, "w") as f:
        for key in derby_game.game_data_dict:
            f.write(f"# {key}={derby_game.game_data_dict[key]}\n")
        derby_game.pdf_jams_data.to_csv(f, sep="\t", index=False)
