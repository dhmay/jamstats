<p align="center">
    <img src="https://github.com/dhmay/jamstats/blob/main/resources/jamstats_logo.png" width="300">
</p>

Tools for making plots with roller derby game data from the [CRG scoreboard](https://github.com/rollerderby/scoreboard) (versions 4.x and 5.x). 

Build jamstats plots online! Check out [jamstats.net](https://jamstats.net). The main reason to run Jamstats locally is to connect to a running scoreboard.

#### Features

* Visualize points per jam, lead, mean net points, calloffs, time to initial pass, penalties and much more
* Read in JSON files from completed games or connect to a running scoreboard
* Save plots as PDF files, or start a webserver that anyone on your network can browse to
* On Windows, build PDFs with **drag-and-drop**

#### Instructions

* **[Installation](#installation)** (Windows and Mac)
* **[Usage](#usage)**

#### Testimonials

* *"I really appreciate this data, and it's where I pulled my practice plans"* -- a coach in our league
* *"BLESS YOUUUUU"* --somebody on Reddit
* *"Go you! This is great!"* --somebody on the Facebook scoreboard group

## Sample plots

<p align="left"><img src="https://github.com/dhmay/jamstats/blob/main/resources/cumulative_score_by_jam.png" width="500"></p>

<p align="left"><img src="https://github.com/dhmay/jamstats/blob/main/resources/jammer_stats.png" width="500"></p>

What penalties got you down the most?

<p align="left"><img src="https://github.com/dhmay/jamstats/blob/main/resources/team_penalty_counts.png" width="500"></p>

<p align="left"><img src="https://github.com/dhmay/jamstats/blob/main/resources/skater_stats.png" width="500"></p>

<p align="left"><img src="https://github.com/dhmay/jamstats/blob/main/resources/jam_points_barplot.png" width="500"></p>

Use the colors defined for each team in the scoreboard file, or provide your own on the command line.

<p align="left"><img src="https://github.com/dhmay/jamstats/blob/main/resources/lead_summary.png" width="500"></p>

<p align="left"><img src="https://github.com/dhmay/jamstats/blob/main/resources/jammer_summary.png" width="500"></p>

Want to do your own analytics? Save down a spreadsheet and do your own thing with it!

<p align="left"><img src="https://github.com/dhmay/jamstats/blob/main/resources/tsv_output_screenshot.png" width="500"></p>

[Full guide to plot interpretation (PDF)](https://github.com/dhmay/jamstats/blob/main/resources/jamstats_plot_interpretation.pdf)

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

### GUI

Double-click on the jamstats executable to open a graphical window to specify all parameters.

### Commandline

The command you'll use is the same as the name of the file you downloaded (e.g., `jamstats-v0.3.4-alpha.exe` on Windows, or `jamstats-mac-v0.3.4-alpha` on Mac).

*In the usage below, I'm replacing that with simply `jamstats`. If you want the command to be `jamstats`, rename your file to `jamstats`.*

Get full commandline help running the command with the `--help` argument.

Basic usage is:

`jamstats --jsonfile <JSON file> [some arguments to define the output]`

where:

* `<JSON file>` is the path to a scoreboard JSON file
* `<some arguments to define the output>` tells jamstats what to do:
    * `--jamstatsport <port number>` will make jamstats start a webserver on the indicate port (e.g., 8080)
    * `--outfile <output file>` will make jamstats write output to a file. If the file has extension `.pdf`, will build plots. If `.tsv` or `.txt`, will write a tab-separated-values file you can load with Excel, R, etc.
    * If you don't tell it what to do, jamstats will try to write plots to a PDF with the same name as your JSON file but exension `.pdf` 

or

`jamstats --scoreboardserver <server:port> <some arguments to define the output>`

where:

* `<server:port>` is the server and port number (e.g., `127.0.0.1:8000`) of a running scoreboard. jamstats will connect to the scoreboard and download the current game state. If `[output]` is to a webserver, jamstats will throttle itself to downloading the latest game state no more often than every 30 seconds
* `<some arguments to define the output>`: same as above


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
