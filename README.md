# Description

Python grubber for Greek public channels. Produces a custom aggregated xmltv formatted file for EPG. Custom generated xmltv formatted guide(s) produced for Greek tv channel guide data, available from [Digea.gr][digeagr
] and [Ert.gr][ertgr]. May be used in Plex, Kodi, or similar as a custom guide for setting up a dvr EPG. Generated files at this stage use greek language only, for programme names, descriptions and channel names, where available.

### Xmltv files with daily releases

Daily releases are published containing updated xmltv files for each day, instead of the previous workflow with daily commits. Compressed (`.gz`) versions for the xmltv files are included in daily releases. The files for local development will be kept as they were, for the ones wishing to produce xmltv files on their own.

![CD](https://github.com/chrisliatas/greek-xmltv/workflows/CD/badge.svg)
[![GitHub release](https://img.shields.io/github/v/release/chrisliatas/greek-xmltv)](https://github.com/chrisliatas/greek-xmltv/releases/)

# Usage

### Using the generated xmltv files

The generated `.xml` files published in [releases][grxmltvrels] are ready to be used by your applications that support these files.
 For example you can import one of the files to your Plex dvr as a custom guide (Please check [here][Plexguide] for
  instructions). The files are updated daily and compressed versions (`.gz`) of these files are also provided.  `xmltv_GREECE_el.xml`
   includes all channels from all regions available at [Digea.gr][digeagr] and all available national channels from [Ert.gr][ertgr].
    `grxmltv_nat_el.xml` includes all available national channels from [Ert.gr][ertgr] and [Digea.gr][digeagr] channel data for
     Nationwide channels and Attica (region `Attica-R-Z-9`).
Since, at the moment, generated xmltv files provide greek language names and descriptions, it may not be possible for your dvr to download richer information for shows and movies. So, in Plex live TV & DVR settings for example, might be beneficial to **not** use the "Enhanced Guide" feature.

### Producing your own file(s)

Assuming you are going to use an Ubuntu (or similar) system:

1. Clone the repository
2. Create a working directory `scrapy_export` at the application root (`greek-xmltv/scrapy_export`).
3. Assuming docker and docker-compose is installed, change directory to application root and run
```docker-compose up```

Additionally, `cron_xmltv.sh` will create a crontab entry to daily run the script in `getxmltv.sh`, which does a
 series of other operations (like copying, moving files, etc.) after grubbing the EPG data and generating the desired
  xmltv files.

# Disclaimer

This is an open-source project produced for personal/home use and not intended for commercial use. I do not own
 any of the  data used or gathered by the application. All EPG, channels, programmes data belong and are produced by
  [Digea.gr][digeagr] and [Ert.gr][ertgr]. The purpose of this repository is to provide an example for building an
  xmltv formatted file from collected data freely available. Source code and generated files are provided with the
   terms of the included licence.

[grxmltvrels]: https://github.com/chrisliatas/greek-xmltv/releases
[Plexguide]: https://support.plex.tv/articles/using-an-xmltv-guide/
[digeagr]: https://www.digea.gr/EPG/
[ertgr]: https://program.ert.gr/
