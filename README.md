# jamstats
Tools for doing statistics and making plots on data from [CRG derby scoreboard](https://github.com/rollerderby/scoreboard) JSON files.

Has some basic dependencies that I really need to document better:

* Seaborn
* Pandas

Supports both v4.x and v5.x JSON files.

## If you like these plot, you might like this set of tools

![Cumulative points per jam, by team, in a derby game](https://github.com/dhmay/jamstats/blob/main/resources/cumulative_score_by_jam.png)
![Barplot of points per jam, by team, in a derby game](https://github.com/dhmay/jamstats/blob/main/resources/jam_points_barplot.png)
![Plots summarizign lead by team, in a derby game](https://github.com/dhmay/jamstats/blob/main/resources/lead_summary.png)
![Plots summarizing jammers by team, in a derby game](https://github.com/dhmay/jamstats/blob/main/resources/jammer_summary.png)

## Using jamstats

Right now, this is purely a Python API -- there's no packaging or ability to do stuff from the commandline.
The very simplest thing you can do to check it out is to add the `src` directory to your PYTHONPATH, fire up
Python or Jupyter or whatever, and do something like:

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
