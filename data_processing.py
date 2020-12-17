from file_preprocessing import *
import json
import jsonlines


# STATIC METHODS
# calculate_distance()
# description -- calculates distance between any player's position and the ball's position
# @param -- player_position:        list containing x,y,z coordinates of player's position
# @param -- ball_position:          list containing x,y,z coordinates of ball's position
# @return -- float type variable:   actual distance between player and ball measured in yards
def calculate_distance(player_position, ball_position):
    x_squared = pow(player_position[0] - ball_position[0], 2)
    y_squared = pow(player_position[1] - ball_position[1], 2)
    z_squared = pow(player_position[2] - ball_position[2], 2)

    return pow(x_squared+y_squared+z_squared, 0.5)


# who_is_on_the_ball()
# description -- figure out which player on the team that last touched the ball is closest to it currently
# @param -- frame_obj:          current frame (row/entry in .jsonl tracking file)
# @param -- team_on_the_ball:   either "homePlayers" or "awayPlayers"
# @return -- closest_distance:  the actual distance of the player on the team "in possession" closest to the ball
def who_is_on_the_ball(frame_obj, team_on_the_ball):
    closest_distance, closest_player = float('inf'), {}
    ball_xyz = frame_obj["ball"]["xyz"]

    for player in frame_obj[team_on_the_ball]:
        cur_dist = calculate_distance(player["xyz"], ball_xyz)
        if cur_dist < closest_distance:
            closest_distance = cur_dist
            closest_player = player

    return closest_distance, closest_player


class CurrentMatch:
    def __init__(self):
        self.TARGET_RADIUS = 5.0 / METERS_TO_YARDS_DIVISOR
        self.METADATA_FILE = ""
        self.TRACKING_FILE = ""
        self.ABS_METADATA = ""
        self.ABS_TRACKING = ""
        self.OUTPUT_FILE = ""

        self.ACTUAL_METADATA = {}
        self.HOME_TEAM = ""
        self.AWAY_TEAM = ""
        self.MATCH_DATE = ""
        self.PLAYER_DATA = {}

        self.OUTPUT_FILE = ""
        self.ROWS_TO_ADD = []
        self.TOTAL_FRAMES = 0
        self.NUM_LIVE_FRAMES = 0
        self.NUM_ENTRIES = 0

        # reset filename and absolute path values
        self.METADATA_FILE, self.TRACKING_FILE, self.ABS_METADATA, self.ABS_TRACKING = validate_files()
        print(f"\nThe metadata file to be used:\t{self.METADATA_FILE}\n"
              f"The tracking file to be used:\t{self.TRACKING_FILE}\n")
        self.OUTPUT_FILE = generate_output_file()

        # sort out who is who for home and away
        # load JSON file contents
        f = open(self.ABS_METADATA)
        self.ACTUAL_METADATA = json.load(f)
        f.close()

        desc = self.ACTUAL_METADATA["description"].split()
        self.HOME_TEAM, self.AWAY_TEAM = desc[0], desc[2]
        if len(desc) >= 5:
            self.MATCH_DATE = desc[4]

        # populate a dictionary of all players with data fields relevant to the output
        for player in self.ACTUAL_METADATA["homePlayers"]:
            self.PLAYER_DATA[player["optaId"]] = {
                "team": self.HOME_TEAM,
                "name": player["name"],
                "number": player["number"],
            }

        for player in self.ACTUAL_METADATA["awayPlayers"]:
            self.PLAYER_DATA[player["optaId"]] = {
                "team": self.AWAY_TEAM,
                "name": player["name"],
                "number": player["number"],
            }

    # write_output()
    # description -- writes all the discovered data to the designated output file
    # @param -- duration:       time taken to process the file
    def write_output(self, duration=0):
        with open(self.OUTPUT_FILE, 'a+', newline="") as write_object:
            csv_writer = csv.writer(write_object)
            for entry in self.ROWS_TO_ADD:
                csv_writer.writerow(entry)
                self.NUM_ENTRIES += 1

        reportSummary = f"There is a total of {self.NUM_ENTRIES} discovered instances of when a defending player " \
                        f"pressed an opponent and was within {self.TARGET_RADIUS}m of the ball.\nThe final report was "\
                        f"generated in {duration} seconds and can be found in <{self.OUTPUT_FILE}>.\nThank you!"
        print(reportSummary)

    # process_jsonl_file()
    # description -- primary function that calls most other helper functions
    # bird's eye -- processes JSONL file to populate private data structure with formatted entries
    def process_jsonl_file(self):
        with jsonlines.open(self.TRACKING_FILE) as reader:
            for frame in reader:
                self.TOTAL_FRAMES += 1
                if frame["live"] and frame["ball"]["xyz"]:  # if play is live and ball is inside field
                    TIP = frame["lastTouch"]  # TIP = team in possession
                    TIP_formatted = "homePlayers" if TIP == "home" else "awayPlayers"
                    other_team = "homePlayers" if TIP == "away" else "awayPlayers"
                    data_to_add = self.calculate_every_player(frame, TIP_formatted, other_team)
                    if len(data_to_add) > 0:
                        for row in data_to_add:
                            self.ROWS_TO_ADD.append(row)

                    self.NUM_LIVE_FRAMES += 1

        reportSummary = f"\n====================\n|| REPORT SUMMARY ||\n====================\n" \
                        f"The script successfully searched through:" \
                        f"\n\t1. Total Frames: \t\t{self.TOTAL_FRAMES}" \
                        f"\n\t2. Live Frames: \t\t{self.NUM_LIVE_FRAMES}\n"
        print(reportSummary)

    # calculate_every_player()
    # description -- in a given frame, determines which opponents (if any) are within pressuring range
    # @param -- frame_obj:          current frame
    # @param -- team_on_the_ball:   the team in possession
    # @param -- team_defending:     the other team (candidates for entries into output file)
    # @return -- players_within_target_radius_in_frame:  list with all relevant fields when all conditions met
    def calculate_every_player(self, frame_obj, team_on_the_ball, team_defending):
        players_within_target_radius_in_frame = []
        ball_xyz = frame_obj["ball"]["xyz"]
        for player in frame_obj[team_defending]:
            player_dist_to_ball = calculate_distance(player["xyz"], ball_xyz)
            if player_dist_to_ball < self.TARGET_RADIUS:
                temp, potb = who_is_on_the_ball(frame_obj, team_on_the_ball)

                # create new row entry
                new_entry = [frame_obj["frameIdx"], frame_obj["wallClock"], frame_obj["period"], frame_obj["gameClock"]]
                self.append_player(new_entry, potb, team_defending)
                self.append_player(new_entry, player, team_defending, player_dist_to_ball, True)

                # add to total list for current frame
                players_within_target_radius_in_frame.append(new_entry)

        return players_within_target_radius_in_frame

    # def append_player()
    # description -- helper function to format a new row entry
    # @param -- array:              the list that will end up being a new row entry
    # @param -- cur_player:         the player in question
    # @param -- team_on_defense:    who the defending team is
    # @param -- distance_to_ball:   only required if the defender flag is True
    # @param -- defender:           boolean flag that determines if the distance_to_ball should be added
    def append_player(self, array, cur_player, team_on_defense, distance_to_ball=0.0, defender=False):
        if defender:
            affiliated_team = self.AWAY_TEAM if team_on_defense == "awayPlayers" else self.HOME_TEAM
        else:
            affiliated_team = self.HOME_TEAM if team_on_defense == "awayPlayers" else self.AWAY_TEAM

        # player team, player name, player number, player id
        array.append(affiliated_team)

        # player name, player number, player id
        player = self.PLAYER_DATA[cur_player["playerId"]]
        array.append(player["name"])
        array.append(player["number"])
        array.append(cur_player["playerId"])

        if defender:
            array.append(distance_to_ball)
