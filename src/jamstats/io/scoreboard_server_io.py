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
        
    def on_message(self, ws, message):
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
            logger.debug("About to try to load game state from message...")
            if "state" in message_dict:
                if "state" in self.game_json_dict:
                    for key in message_dict["state"]:
                        self.game_json_dict["state"][key] = message_dict["state"][key]
                else:
                    self.game_json_dict = message_dict
                # determine whether there was a meaningful change to the game state
                for key in message_dict["state"]:
                    if not key.startswith("ScoreBoard.CurrentGame.Clock"):
                        self.game_state_dirty = True
            logger.debug("Loaded game state from message.")
        except Exception as e:
            self.exceptions.append(e)
            formatted_lines = traceback.format_exc().splitlines()
            for line in formatted_lines:
                print("EXC: " + line)
        
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