
# Tools

# aisdump.py
Parse and dump data from NMEA AIS data. 

Usage:
'''
usage: aisdump.py [-h] -r READ [-t TYPE] [-i] [--version]

Dump data from NMEA AIS messages.

options:
  -h, --help            show this help message and exit
  -r READ, --read READ  Input filename.
  -t TYPE, --type TYPE  Filter by message type.
  -i, --id-only         Dump ID data only (MMSIs, Names, Call Signs).
  --version             show program's version number and exit
'''

Most AIS message types are supported. The raw data will be provided for message types that have not yet been implemented.

# aiscraft.py
Allows for the creation of custom AIS type 5 messages (so far). The message contents are defined in a json file. The tool will encode the contents of the file and output NMEA messages.

'''
usage: aiscraft.py [-h] -r READ [--version]

Build custom AIS type 5 message.

options:
  -h, --help            show this help message and exit
  -r READ, --read READ  NMEA AIS message contents JSON file.
  --version             show program's version number and exit
'''

# Issues, Bugs, & TODO

## aisdump.py
 - Very accuracy of decoded lat and long coordinates.
 - Part B of AIS Type 24 messages are not correctly detected and parsed.
 - ChatGPT generated pasers have not all been checked and tweaked. Message types > 17 may be missing fields.

## aiscraft.py
 - Add more message types.

# Author
Dylan Smyth
