import os
import csv

# Relevant filenames
METADATA_FILE = "20200912-NSH-ATL_886b2a47-3249-4e95-8200-f7cdd8fbbf46_SecondSpectrum_Metadata.json"
TRACKING_FILE = "20200912-NSH-ATL_886b2a47-3249-4e95-8200-f7cdd8fbbf46_SecondSpectrum_Data.jsonl"
OUTPUT_FILE = "20200912-NSH-ATL-timestampped-on-ball-pressures.csv"

VALIDATION_ERR_MESSAGE = f"""
=================\nERROR DETECTED\n=================\n
The entered filename does not exist in the current folder.\n
Potential solutions include:
\t* ensure that the desired file is in the same directory that this script is in
\t* copy-paste the filename (including extension/file format) exactly
\nPlease restart the script and try again!\n
=================\nERROR DETECTED\n=================\n
"""

# Other constants
JSON_EXT = ".json"
JSONL_EXT = ".jsonl"
CSV_EXT = ".csv"

# there are this many yards in 1m; divide #meters by this number to get #yards
METERS_TO_YARDS_DIVISOR = 1.0936133


# get_metadata_file()
# description -- prompts user for the full filename of the metadata file
# @param -- temp:       default filename set
# @return -- mf:        final metadata filename
def get_metadata_file(temp=METADATA_FILE):
    mf = input(f"Enter complete filename for METADATA file including the .json extension (enter nothing for default): ")
    if len(mf) < 1 + len(JSON_EXT) or mf[-len(JSON_EXT):] != JSON_EXT:
        print(f"\tYour input of <{mf}> was of an invalid format. "
              f"\n\tThe default file of <{temp}> will be used instead.")
        return temp
    return mf


# get_tracking_file()
# description -- prompts user for the full filename of the tracking file
# @param -- temp:       default filename set
# @return -- tf:        final tracking filename
def get_tracking_file(temp=TRACKING_FILE):
    tf = input(f"Enter complete filename for TRACKING file including the .jsonl extension (enter nothing for default):")
    if len(tf) < 1 + len(JSON_EXT) or tf[-len(JSON_EXT):] != JSON_EXT:
        print(f"\tYour input of <{tf}> was of an invalid format. "
              f"\n\tThe default file of <{temp}> will be used instead.")
        return temp
    return tf


# validate_files()
# description -- data validation; ensures that the entered files exist in current/appropriate directory
# @return -- meta:          filename for metadata file
# @return -- track:         filename for tracking file
# @return -- full_meta:     absolute path for metadata file
# @return -- full_track:    absolute path for tracking file
def validate_files():
    cur_directory = os.getcwd()
    meta = get_metadata_file()
    full_meta = os.path.join(cur_directory, meta)
    if not os.path.isfile(full_meta):
        print(VALIDATION_ERR_MESSAGE)
        exit(1)

    track = get_tracking_file()
    full_track = os.path.join(cur_directory, track)
    if not os.path.isfile(full_track):
        print(VALIDATION_ERR_MESSAGE)
        exit(1)

    return meta, track, full_meta, full_track


# generate_output_file()
# description -- prompts user for their desired filename for output file and also initializes column headings
# @return -- output:        filename entered (or default file if nothing entered)
def generate_output_file():
    output = input("Enter the desired filename for the output file (do NOT include the .csv file extension): ")
    if len(output) <= len(CSV_EXT) or output[-len(CSV_EXT):] == CSV_EXT:
        print(f"\tYour input of <{output}> was either empty or of an invalid format."
              f"\n\tThe default file of <{OUTPUT_FILE}> will be used instead.")
        output = OUTPUT_FILE
    else:
        output += CSV_EXT

    # Write column headers
    with open(output, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["Timestamps", "", "", "", "Player in Possession", "", "", "",
                            "Pressuring Player", "", "", "", ""])
        csvwriter.writerow(["Frame Index", "Actual Time (UNIX)", "Period", "Time Since Period Start (s)",
                            "Affiliated Team", "Player Name", "Player Number", "Player ID",
                            "Affiliated Team", "Player Name", "Player Number", "Player ID", "Distance to Ball (yards)"])

    return output
