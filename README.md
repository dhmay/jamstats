# jamstats
Tools for doing statistics and making plots on data from [CRG roller derby scoreboard](https://github.com/rollerderby/scoreboard) JSON files.

Supports both v4.x and v5.x JSON files. Supports completed-game and in-progress game files.

## Installation

With Python 3.x installed, type:

`pip install jamstats`

## Usage

Installation gives you two commands, one for making a PDF with plots derived from a derby game json file:

`jamstats-plot-pdf <game.json> [plots.pdf]`

and one for converting a derby game json file to a TSV (tab-separated value) file that can be used in Excel, R, etc.:

`jamstats-convert-tsv <game.json> [game.tsv]`

If output files aren't specified, output will be written to the same path as the input file, with .json replaced with .pdf or .txt, respectively.

## Let's see some plots!

If you like these plots, you might like this set of tools

![Cumulative points per jam, by team, in a derby game](https://github.com/dhmay/jamstats/blob/main/resources/cumulative_score_by_jam.png)
![Barplot of points per jam, by team, in a derby game](https://github.com/dhmay/jamstats/blob/main/resources/jam_points_barplot.png)
![Plots summarizign lead by team, in a derby game](https://github.com/dhmay/jamstats/blob/main/resources/lead_summary.png)
![Plots summarizing jammers by team, in a derby game](https://github.com/dhmay/jamstats/blob/main/resources/jammer_summary.png)

## Using jamstats from Python

This example Python code parses a scoreboard json file, writes it out as a TSV file, makes a bunch of plots and saves them to a PDF file.

```python
from jamstats.io.scoreboard_json_io import load_derby_game_from_json_file
from jamstats.plots import jamplots

in_json_filepath = "period2.json"
out_tsv_filepath = "jam_data.tsv"
out_pdf_filepath = "game_plots.pdf"

# parse a scoreboard json file
derby_game = load_derby_game_from_json_file(in_json_filepath)

# Write out a .tsv file with jam data.
tsv_io.write_game_data_tsv(derby_game, out_tsv_filepath)
                                       
# Write a .pdf with a bunch of plots
jamplots.save_game_plots_to_pdf(derby_game, out_pdf_filepath)
```
