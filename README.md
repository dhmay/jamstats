<p align="center">
    <img src="https://github.com/dhmay/jamstats/blob/main/resources/jamstats_logo.png" width="300">
</p>

Tools for making plots with roller derby game data from the [CRG scoreboard](https://github.com/rollerderby/scoreboard) (versions 4.x and 5.x).

#### Features

* Visualize points per jam, lead, mean net points, calloffs, time to initial pass, penalties and much more
* Read in JSON files from completed games or connect to a running scoreboard
* Save plots as PDF files, or start a webserver that anyone on your network can browse to
* On Windows, build PDFs with **drag-and-drop**

#### Instructions

* **[Installation](#installation)** (Windows and Mac)
* **[Usage](#usage)**

## Sample plots

![Cumulative points per jam, by team, in a derby game](https://github.com/dhmay/jamstats/blob/main/resources/cumulative_score_by_jam.png)

Key attributes of every jam.

![Barplot of points per jam, by team, in a derby game](https://github.com/dhmay/jamstats/blob/main/resources/jam_points_barplot.png)

Use the colors defined for each team in the scoreboard file, or provide your own on the command line.

![Plots summarizign lead by team, in a derby game](https://github.com/dhmay/jamstats/blob/main/resources/lead_summary.png)

![Plots with individual anonymized jammer stats, in a derby game](https://github.com/dhmay/jamstats/blob/main/resources/jammer_stats.png)

What penalties 
ged you down the most?

![Plots with individual anonymized skater stats, in a derby game](https://github.com/dhmay/jamstats/blob/main/resources/skater_stats.png)

![Plots summarizing jammers by team, in a derby game](https://github.com/dhmay/jamstats/blob/main/resources/jammer_summary.png)


## Installation

#### Option 1: executable file

Go to the [latest release](https://github.com/dhmay/jamstats/releases) and download the appropriate file for your operating system:
* Windows: `jamstats-<version>.exe`
* Mac: `jamstats-mac-<version>`

#### Option 2: On any platform, with Python 3.7 or later

`pip install jamstats`

This will put the `jamstats` executable on your path.

## Usage

### Drag-and-drop (Windows only)

On Windows, to generate a plots PDF, you can simply **drag and drop** your game JSON file onto the jamstats.exe file. That will generate a .pdf file in the same directory as your `.json` file, with the same name but with the `.json` extension replaced with `.pdf`.

### Commandline

The command you'll use is the same as the name of the file you downloaded (e.g., `jamstats-v0.3.4-alpha.exe` on Windows, or `jamstats-mac-v0.3.4-alpha` on Mac).

*In the usage below, I'm replacing that with simply `jamstats`. If you want the command to be `jamstats`, rename your file to `jamstats`.*

Get full commandline help running the command with the `--help` argument.

Basic usage is:

`jamstats <input> [output]`

`<input>` can be:

* a JSON file from a completed or in-progress game
    * jamstats will build the plots representing that game
* the server and port number (e.g., `127.0.0.1:8000`) of a running scoreboard
    * jamstats will connect to the scoreboard and download the latest game state
        * if `[output]` is to a webserver, jamstats will throttle itself to downloading the latest game state no more often than every 30 seconds

`[output]` is optional.

* If omitted, plots will be written to a PDF file with the same name as the JSON input file but with extension `.json` instead of `.pdf`
* If provided:
    * if it is an integer (e.g., `8080`), jamstats will start a webserver\* on that port number. Browse to, e.g., `http://locoalhost:8080` to view plots in your browser
        * to update a plot with the latest game state, refresh your browser or click the link to the plot you want in the left sidebar
    * if it has a `.txt` or `.tsv` extension, jamstats will write tab-delimited game data file that can be loaded in Excel or R
    * otherwise, jamstats will write plots to a PDF file with that name
    
\* *I am not a web security expert, and I make no guarantees whatsoever about webserver security. If you're concerned and can help make it more secure, please open an issue!*

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
