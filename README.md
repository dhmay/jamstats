<p align="center">
    <img src="https://github.com/dhmay/jamstats/blob/main/resources/jamstats_logo.png" width="300">
</p>

Tools for doing statistics and making plots on data from the [CRG roller derby scoreboard](https://github.com/rollerderby/scoreboard). Read in completed game files or connect to a running scoreboard. Write plots out as PDF files, or start a webserver that anyone on the network can connect to to view plots.

Installation options include a Windows executable that can build PDFs via drag-and-drop. Supports both v4.x and v5.x scoreboard versions. 

* [Installation](#installation)
* [Usage](#usage)

## Let's see some plots!

If you like these plots, you might like this set of tools

![Cumulative points per jam, by team, in a derby game](https://github.com/dhmay/jamstats/blob/main/resources/cumulative_score_by_jam.png)
![Barplot of points per jam, by team, in a derby game](https://github.com/dhmay/jamstats/blob/main/resources/jam_points_barplot.png)
![Plots summarizign lead by team, in a derby game](https://github.com/dhmay/jamstats/blob/main/resources/lead_summary.png)
![Plots summarizing jammers by team, in a derby game](https://github.com/dhmay/jamstats/blob/main/resources/jammer_summary.png)
![Plots with individual anonymized jammer stats, in a derby game](https://github.com/dhmay/jamstats/blob/main/resources/jammer_stats.png)
![Plots with individual anonymized skater stats, in a derby game](https://github.com/dhmay/jamstats/blob/main/resources/skater_stats.png)

## Installation

#### Option 1: Windows executable

Go to the [latest release](https://github.com/dhmay/jamstats/releases) and download the file `jamstats.exe`.

#### Option 2: On any platform, with Python 3.7 or later

`pip install jamstats`

## Usage

### Drag-and-drop (Windows only)

On Windows, to generate a plots PDF, you can simply drag your game JSON file onto the jamstats.exe file. That will generate a .pdf file in the same directory as your `.json` file, with the same name but with the `.json` extension replaced with `.pdf`.

### Commandline

Get full help for the `jamstats` (or `jamstats.exe` on Windows) command by running it with the `--help` argument.

Basic usage is:

`jamstats <input> [output]`

`<input>` can be:

* a JSON file from a completed or in-progress game
    * jamstats will build the plots representing that game
* the server and port number (e.g., `127.0.0.1:8000`) of a running scoreboard
    * jamstats will connect to the scoreboard and download the latest game state
        * if `[output]` is to a webserver, jamstats will poll the scoreboard every 30 seconds, keeping your plots up to date

`[output]` is optional.

* If omitted, plots will be written to a PDF file with the same name as the JSON input file but with extension `.json` instead of `.pdf`
* If provided:
    * if it is an integer (e.g., `8080`), jamstats will start a webserver on that port number. Browse to, e.g., `http://locoalhost:8080` to view plots in your browser
    * if it has a `.txt` or `.tsv` extension, jamstats will write tab-delimited game data file that can be loaded in Excel or R
    * otherwise, jamstats will write plots to a PDF file with that name

### Using jamstats from Python

This example Python code parses a scoreboard json file, writes it out as a TSV file, makes a bunch of plots and saves them to a PDF file.

```python
from jamstats.io.scoreboard_json_io import load_derby_game_from_json_file
from jamstats.plots import plot_together

in_json_filepath = "period2.json"
out_tsv_filepath = "jam_data.tsv"
out_pdf_filepath = "game_plots.pdf"

# parse a scoreboard json file
derby_game = load_derby_game_from_json_file(in_json_filepath)

# Write out a .tsv file with jam data.
tsv_io.write_game_data_tsv(derby_game, out_tsv_filepath)
                                       
# Write a .pdf with a bunch of plots
plot_together.save_game_plots_to_pdf(derby_game, out_pdf_filepath)
```
