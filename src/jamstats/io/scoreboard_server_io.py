import websocket
import json
import logging
import traceback

logger = logging.getLogger(__name__)


class ScoreboardClient:
    def __init__(self, scoreboard_server: str, scoreboard_port: int):
        """init

        Args:
            scoreboard_server (str): server to connect to
            scoreboard_port (int): port to connect to
        """
        self.n_messages_received = 0
        self.game_json_dict = {}
        self.exceptions = []
        self.scoreboard_server = scoreboard_server
        self.scoreboard_port = scoreboard_port
        self.is_connected_to_server = False
        self.scoreboard_version = None 
        # keep track of the game id so we can detect when a new game starts
        self.game_id = None

        # indicator of whether the game state has changed since the last time
        # we checked
        self.game_state_dirty = False

        
    def start(self):
        """Start the websocket client
        """
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(f"ws://{self.scoreboard_server}:{self.scoreboard_port}/WS",
                                    on_open=self.on_open,
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close,
                                    on_ping=self.on_ping)

        ws.run_forever(ping_interval=30)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
        self.ws = ws
        
    def on_message(self, ws, message) -> None:
        """Attempt to parse a message. If it contains game state,
        update the game state.

        Args:
            ws (_type_): websocket
            message (_type_): message from the server
        """
        self.n_messages_received += 1
        try:
            message_dict = json.loads(message)
            # ignore clock updates
            #message_dict = {
            #    key: message_dict[key]
            #    for key in message_dict
            #    if not key.startswith("ScoreBoard.CurrentGame.Clock")}
            #logger.debug("About to try to load game state from message...")
            if "state" in message_dict: # we got a valid message with game state
                message_game_state_dict = message_dict["state"]

                # store scoreboard version separately, because it doesn't get resent for a new game
                if "ScoreBoard.Version(release)" in message_game_state_dict:
                    self.scoreboard_version = message_game_state_dict["ScoreBoard.Version(release)"]
                if "ScoreBoard.CurrentGame.Game" in message_game_state_dict:
                    message_game_id = message_game_state_dict["ScoreBoard.CurrentGame.Game"]
                    if self.game_id is not None and self.game_id != message_game_id:
                        # new game! GIVE UP. Say we are not connected to the server,
                        # so we will reconnect and get a new game state.
                        # This is necessary because the server doesn't send all the information
                        # I think it should when a new game starts.
                        #self.game_state_dirty = True
                        #self.game_json_dict = {}
                        logger.debug(f"New game! {message_game_id}")
                        logger.warning("New game! Giving up on this connection.")
                        self.is_connected_to_server = False
                        return
                    self.game_id = message_game_id
                if "state" in self.game_json_dict: # if we already have a game state...
                     # Update the game json.
                    # first, remove any keys that are overwritten by null values in the message.
                    # This gets a bit complicated. Frank says:
                    # A key being set to null should delete
                    # * an exact match
                    # * anything that starts with the key followed by a . (Keys sent will not end with a .)
                    if "ScoreBoard.Version(release)" in message_game_state_dict:
                        self.scoreboard_version = message_game_state_dict["ScoreBoard.Version(release)"]
                    nullvalue_message_keys = [key for key in message_game_state_dict
                                              if message_game_state_dict[key] is None] 
                    for key in nullvalue_message_keys:
                        print(f"*** Nulling out {key}")
                        if key in self.game_json_dict["state"]:
                            del self.game_json_dict["state"][key]
                        for state_key in self.game_json_dict["state"]:
                            if state_key.startswith(key + "."):
                                del self.game_json_dict["state"][state_key]
                    # now, add all the new data from the message.
                    for key in message_game_state_dict:
                        if message_game_state_dict[key] is not None:
                            self.game_json_dict["state"][key] = message_game_state_dict[key]
                else:
                    logger.debug("Replacing game_json_dict with message_dict")
                    self.game_json_dict = message_dict
                # determine whether there was a meaningful change to the game state
                for key in message_game_state_dict:
                    if not key.startswith("ScoreBoard.CurrentGame.Clock") and key != "ScoreBoard.Version(release)":
                        self.game_state_dirty = True
                        logger.debug(f"Setting game state dirty because {key}.")
                        break
            #logger.debug("Loaded game state from message.")
        except Exception as e:
            self.exceptions.append(e)
            formatted_lines = traceback.format_exc().splitlines()
            for line in formatted_lines:
                print("EXC: " + line)
        # if game doesn't have a scoreboard version, but we do, add it to the game state
        if "ScoreBoard.Version(release)" not in self.game_json_dict["state"]:
            logger.debug(f"game state missing scoreboard version. In hand: {self.scoreboard_version}")
            if self.scoreboard_version is not None:
                logger.debug(f"Adding scoreboard version to message: {self.scoreboard_version}")
                self.game_json_dict["state"]["ScoreBoard.Version(release)"] = self.scoreboard_version

        
    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print("### closed ###")
        self.is_connected_to_server = False
        
    def on_ping(self, ws):
        print("on_ping")
        self.send_custom_message(ws, { "action": "Ping" })

    def on_open(self, ws):
        """Send the registration message to the server

        Args:
            ws (_type_): websocket
        """
        print("Opened connection")
        self.send_custom_message(ws,
        {
          "action": "Register",
          "paths": [
              "ScoreBoard.Version(release)",
              "ScoreBoard.CurrentGame",
          ]
        })
        self.is_connected_to_server = True
        print("Sent registration message")

    def send_custom_message(self, ws, msg):
        msg_json = json.dumps(msg)
        if ws and ws.sock.connected:
            ws.send(msg_json)
        else:
            print("ws api is not connected.")