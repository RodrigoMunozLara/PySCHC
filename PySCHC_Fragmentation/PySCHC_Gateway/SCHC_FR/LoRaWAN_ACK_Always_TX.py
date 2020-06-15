import logging

from SCHC_FR.SCHC_Message import SCHC_Message


class LoRaWAN_ACK_Always_TX:
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

    def __init__(self, session, rule_id, window_size, tiles, tile_size, fragmenter):
        self.current_state = self.STATE_TX_INIT
        self.current_window = 0
        self.current_fcn = window_size
        self.rule_id = rule_id
        self.schc_message = SCHC_Message()

    def execute(self, buffer):
        if self.current_state is self.STATE_TX_INIT:
            self.TX_INIT_send_fragment(buffer)
        elif self.current_state is self.STATE_TX_SEND:
            self.TX_SEND_send_fragment(buffer)
        else:
            logging.error("Wrong State")

    def TX_INIT_send_fragment(self, buffer):
        logging.debug("Entrando en TX_INIT_send_fragment")
        return

    def TX_SEND_send_fragment(self, buffer):
        logging.debug("Entrando en TX_SEND_send_fragment")
        return
