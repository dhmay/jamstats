__author__ = "Damon May"

import pandas as pd
from typing import Dict, Any
import csv

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


def get_team_number_name_map(jams_metadata_dict: Dict[str, str]) -> Dict[int, str]:
    """Convenience method to extract a map from team number to team name
    from the jams metadata dictionary.

    Args:
        jams_metadata_dict (Dict[str, str]): _description_

    Returns:
        Dict[int, str]: _description_
    """
    team_1 = jams_metadata_dict["team_1"]
    team_2 = jams_metadata_dict["team_2"]

    team_number_name_map = {
        1: team_1,
        2: team_2
    }
    return team_number_name_map


def write_game_data_tsv(game_data_dict: Dict[str, Any],
                        pdf_jam_data: pd.DataFrame,
                        filepath: str) -> None:
    """Write game data to a .tsv file. Put some data into comments in the header.

    Args:
        game_data_dict (Dict[str, Any]): basic game info dict
        pdf_jam_data (pd.DataFrame): jam-level data
        filepath (str): path to write
    """
    with open(filepath, "w") as f:
        for key in game_data_dict:
            f.write(f"# {key}={game_data_dict[key]}\n")
        pdf_jam_data.to_csv(f, sep="\t", index=False)
