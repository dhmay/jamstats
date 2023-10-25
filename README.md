
<p align="center">
    <img src="https://github.com/dhmay/jamstats/blob/main/resources/jamstats_logo.png" width="300">
</p>

Tools for displaying roller derby game data from the [CRG scoreboard](https://github.com/rollerderby/scoreboard) (versions 4.x and later). 

You can build jamstats plots from game JSON files **online!** No need to install anything. Check out [jamstats.net](https://jamstats.net). 

So, why download Jamstats and run it on your laptop? To connect to a live game on a running scoreboard! 

**Jamstats is great for announcers!** See **who's on the track** (including positions and penalties), vital game stats and **rosters** for both teams and officials. You can even connect to a live scoreboard [from anywhere on the Internet](https://github.com/dhmay/jamstats#connecting-to-a-proxied-scoreboard-from-the-internet) using wsproxy!

#### Features

* Get up-to-date game data from a live scoreboard
* Visualize points per jam, lead, mean net points, calloffs, time to initial pass, penalties and much more
* Read in JSON files from completed games or connect to a running scoreboard
* Save plots as PDF files, or start a webserver that anyone on your network can browse to

Do you already love Jamstats? [Tell us about it!](https://github.com/dhmay/jamstats/issues/new?assignees=&labels=testimonial&template=testimonial.md&title=)

Jamstats was developed by [TheDM](https://github.com/dhmay), with [Seattle Derby Brats](https://www.seattlederbybrats.com/donations/). Like Jamstats? Consider a donation to SDB, a 501(c)(3) organization!
<p align="left"><a href="https://www.seattlederbybrats.com/donations/"><img src="https://github.com/dhmay/jamstats/blob/main/resources/sdb_logo_whitebkgrnd.png" width="150"></a></p>



#### Instructions

Quickstart: download [the latest release](https://github.com/dhmay/jamstats/releases) and run it.

In more detail:

* **[Installation](#installation)**
* **[Usage](#usage)**

## Sample plots

<p align="left"><img src="https://github.com/dhmay/jamstats/blob/main/resources/current_skaters.png" width="500"></p>

<p align="left"><img src="https://github.com/dhmay/jamstats/blob/main/resources/cumulative_score_by_jam.png" width="500"></p>

<p align="left"><img src="https://github.com/dhmay/jamstats/blob/main/resources/jammer_stats.png" width="500"></p>

What penalties got you down the most?

<p align="left"><img src="https://github.com/dhmay/jamstats/blob/main/resources/team_penalty_counts.png" width="500"></p>

<p align="left"><img src="https://github.com/dhmay/jamstats/blob/main/resources/skater_stats.png" width="500"></p>

<p align="left"><img src="https://github.com/dhmay/jamstats/blob/main/resources/jam_points_barplot.png" width="500"></p>

Use the colors defined for each team in the scoreboard file, or provide your own on the command line.

<p align="left"><img src="https://github.com/dhmay/jamstats/blob/main/resources/lead_summary.png" width="500"></p>

Want to do your own analytics? Save down a spreadsheet and do your own thing with it!

<p align="left"><img src="https://github.com/dhmay/jamstats/blob/main/resources/tsv_output_screenshot.png" width="500"></p>


## Installation

* Windows: go to the [latest release](https://github.com/dhmay/jamstats/releases) and download `jamstats-<version>.exe`
* Mac: go to the [latest release](https://github.com/dhmay/jamstats/releases) and download `jamstats-mac-<version>.zip`, then unzip that file into your Applications directory (or wherever you want to run Jamstats from)
    * Note that the Mac app is particularly slow to start up
* Any platform: install Python 3.9 or higher, then run `pip install jamstats`. That will put `jamstats` on your path so you can run it from the command line.

## Usage

[Full user manual (PDF)](https://github.com/dhmay/jamstats/blob/main/resources/jamstats_user_manual.pdf), including how to start Jamstats up and how to interpret all the plots.

### Drag-and-drop

On Windows or Mac, to generate a plots PDF, you can simply **drag and drop** your game JSON file onto the jamstats.exe file or Jamstats app. That will generate a `.pdf` file in the same directory as your `.json` file, with the same name but with the `.json` extension replaced with `.pdf`.

### GUI

Double-click on the jamstats executable to open a graphical window to specify your parameters. 

To connect to a scoreboard, all you need to specify is `scoreboardserver` -- give that the combined IP address and port number of your scoreboard server (e.g., `172.21.12.7:8000`), as reported in the scoreboard GUI.

With that usage, Jamstats will start its own server on your laptop, and the output in the GUI window will tell you where to point your browser. By default, that's `http://localhost:8080`, which will make Jamstats available only on your own machine. If you want to make Jamstats available to other browsers on your network, set `jamstatsip` to your computer's IP address.

You can also use the GUI to specify all other arguments you could specify from the commandline.

### Connecting to a proxied scoreboard from the Internet

It's possible to use Jamstats from anywhere in the world to connect to a running scoreboard! This lets **remote announcers** use Jamstats to help with calling games. Here's how:

#### At the track: setting up a proxy

1. Download [wsproxy](https://github.com/DerbyStats/wsproxy) and follow its instructions to set up a proxy. This will feed your scoreboard data, read-only, to the Internet
    * If you're using the default scoreboard settings, the default wsproxy settings will work fine. 
    * If not, pay attention to the port you're running your scoreboard on, and change from 8000 to that same port in wsproxy's config.ini file
2. Your proxy can send your scoreboard data wherever you tell it to. On the other end, there needs to be another copy of wsproxy running.
    * With the default configuration, your proxy data will be sent to a new subdomain of `derbystats.eu`
        * e.g., `https://jammer-lane.derbystats.eu/`, but it will *not be that*, it will be something else unique to your scoreboard
    * When you start wsproxy, it will tell you where the data is going. 
        * For example, `Display URL: https://jammer-lane.derbystats.eu`
        * Give this to the person who'll be running Jamstats remotely.
        
#### Remotely: running Jamstats to connect to a proxy

1. Get the "Display URL" from the person who set up wsproxy
    * For example, `https://jammer-lane.derbystats.eu`
2. Start up Jamstats and give it two arguments (either through the GUI or on the command line):
    * `scoreboardserver`: make this the full subdomain of the "Display URL", without the `https://` part, with `:443` added to the end
        * For example: `jammer-lane.derbystats.eu:443`
    * `ssl`: set this to `true` (default is `false`)

Example of how this looks on the commandline:

`python bin/jamstats --scoreboardserver=jammer-lane.derbystats.eu:443 --ssl`

Example of how this looks in the GUI:

![image](https://user-images.githubusercontent.com/714077/229311685-b44359dc-5501-435b-ae44-9039317f2f09.png)

That's it! If that setup all worked correctly, Jamstats should now behave exactly as though you were right there at the track.

### Commandline

The command you'll use is the same as the name of the file you downloaded (e.g., `jamstats-v0.3.4-alpha.exe` on Windows, or `jamstats-mac-v0.3.4-alpha` on Mac).

*In the usage below, I'm replacing that with simply `jamstats`. If you want the command to be `jamstats`, rename your file to `jamstats`.*

Get full commandline help running the command with the `--help` argument.

#### Option 1: get game data from a JSON file

`jamstats --jsonfile <JSON file> [optional arguments]`

where:

* `<JSON file>` is the path to a scoreboard JSON file
* `[optional arguments]`: by default, Jamstats will write the output to the same path as the input file, but with ".json" replaced with ".pdf". You can adjust that behavior by specifying an output `--outfile` file or using the `--mode=web` argument to start a webserver (see below), instead.
    * there are also several options, explained in the help message, that affect the charts that are built.

#### Option 2: connect to a running scoreboard server

`jamstats --scoreboardserver <server:port> [optional arguments]`

where:

* `<server:port>` is the server and port number (e.g., `127.0.0.1:8000`) of a running scoreboard. jamstats will connect to the scoreboard and download the current game state.
* `<some arguments to define the output>`: same as above. You can route the output to a PDF file by specifying `--mode=pdf`.


\* *I am not a web security expert, and I make no guarantees whatsoever about webserver security. If you're concerned and want to help make it more secure, please open an issue!*
