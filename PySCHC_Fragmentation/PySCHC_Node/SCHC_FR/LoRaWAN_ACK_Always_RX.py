from SCHC_FR.SCHC_Message import SCHC_Message


class LoRaWAN_ACK_Always_RX:
    STATE_TX_INIT = 0
    STATE_TX_SEND = 1
    STATE_TX_WAIT_x_ACK = 2
    STATE_TX_RESEND_MISSING_FRAG = 3
    STATE_TX_ERROR = 4
    STATE_TX_END = 5

    current_state = None
    session = None
    current_window = None
    current_fcn = None
    rule_id = None

    schc_message = None

    # LoRaWAN parameters
    current_data_rate = None

    def __init__(self, rule_id, window_size, tiles, tile_size):
        self.current_state = self.STATE_TX_INIT
        self.current_window = 0
        self.current_fcn = window_size
        self.rule_id = rule_id
        self.schc_message = SCHC_Message()
        self.tiles = tiles
        self.tile_size = tile_size

    def execute(self, msg):
        if self.current_state is self.STATE_TX_INIT:
            self.TX_INIT_send_fragment(msg)
        elif self.current_state is self.STATE_TX_SEND:
            self.TX_SEND_send_fragment(msg)
        else:
            print("Wrong STATE")

    def TX_INIT_send_fragment(self, msg):
        pass

    def TX_SEND_send_fragment(self, msg):
        pass
