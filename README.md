# jamstats
Tools for doing statistics and making plots on data from [CRG derby scoreboard](https://github.com/rollerderby/scoreboard) JSON files.

Has some basic dependencies that I really need to document better:

* Seaborn
* Pandas

Currently seems to work on v4.x scoreboard files, because that's all I've got to play with.
Once I get my hands on some v5.x files, I'll make the necessary changes and either support both versions or, if
they're too incompatible, dump 4.x support.

Right now, this is purely a Python API -- there's no packaging or ability to do stuff from the commandline.
The very simplest thing you can do to check it out is to add the `src` directory to your PYTHONPATH, fire up
Python or Jupyter or whatever, and do something like:

```python
from jamstats.io.scoreboard_json_io import ScoreboardJsonFileDerbyGameFactory
from jamstats.plots import jamplots

in_json_filepath = "period2.json"
out_tsv_filepath = "jam_data.tsv"
out_pdf_filepath = "game_plots.pdf"

# parse a scoreboard json file
game_factory = ScoreboardJsonFileDerbyGameFactory(in_filepath)
derby_game = game_factory.get_derby_game()

# Write out a .tsv file with jam data.
tsv_io.write_game_data_tsv(derby_game, out_tsv_filepath)
                                       
# Write a .pdf with a bunch of plots
jamplots.save_game_plots_to_pdf(derby_game, out_pdf_filepath)
```
