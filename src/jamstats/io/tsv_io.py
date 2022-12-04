__author__ = "Damon May"

import pandas as pd
from typing import Dict, Any
import csv
from jamstats.data.game_data import DerbyGame, DerbyGameFactory

class TsvDerbyGameFactory(DerbyGameFactory):
    """Build DerbyGame objects from a .tsv file
    """
    def __init__(self, filepath):
        self.game_data_dict = read_jams_tsv_header_dict(filepath)
        self.pdf_jams_data = read_jams_tsv_to_pandas(filepath)
        
    def get_derby_game(self) -> DerbyGame:
        """Build the derby game

        Returns:
            DerbyGame: derby game
        """
        return DerbyGame(self.pdf_jams_data, self.game_data_dict)

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
