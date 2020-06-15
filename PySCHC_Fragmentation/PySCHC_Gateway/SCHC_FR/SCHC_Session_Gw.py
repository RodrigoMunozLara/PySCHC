import logging

from SCHC_FR.LoRaWAN_ACK_Always_TX import LoRaWAN_ACK_Always_TX
from SCHC_FR.LoRaWAN_ACK_On_Error_RX import LoRaWAN_ACK_On_Error_RX


class SCHC_Session_Gw:

    LoRaWAN = 1
    Sigfox = 2

    DIRECTION_UPLINK = 1
    DIRECTION_DOWNLINK = 2

    layer2_word_size = None  # in bits (The L2 word size used by LoRaWAN is 1 byte (8 bits))
    fragmenter = None

    # SCHC Headers
    rule_id = None
    dtag = None
    fcn = None

    # SCHC headers size
    dtag_size = None  # T bits
    w_size = None  # M bits
    fcn_size = None  # N bits
    window_size = None  # window_size <= 2^N
    tile_size = None  # in bits
    max_ack_requests = None
    retransmission_timer_value = None
    inactivity_timer_value = None
    direction = None
    protocol = None
    attempts_counter = None

    # State Machine
    sm = None

    tiles = {}

    def __init__(self, protocol, rule_id, direction):
        if protocol is self.LoRaWAN:
            self.layer2_word_size = 8
            self.dtag_size = 0
            self.w_size = 2
            self.fcn_size = 6
            self.window_size = 63  # window_size <= 2^N
            self.tile_size_bytes = 10  # in bytes
            self.tile_size = self.tile_size_bytes * 8  # in bits

            self.max_ack_requests = 8
            self.retransmission_timer_value = 0
            self.inactivity_timer_value = 12 * 60 * 60  # segundos
            self.direction = direction
            self.attempts_counter = 0
            self.dtag = 0
            self.rule_id = rule_id
            self.protocol = protocol
            self.tiles = {}
            self.current_data_rate = 3
            self.downlink_url = None
            self.dev_id = None
            self.lorawan_port = None

        logging.info("********** Tile Size: " + str(self.tile_size_bytes) + " bytes ***************")

    def get_dtag(self):
        return self.dtag

    def set_fragmenter(self, fragmenter):
        self.fragmenter = fragmenter

    def set_downlink_url(self, downlink_url):
        self.downlink_url = downlink_url

    def get_downlink_url(self):
        return self.downlink_url

    def set_dev_id(self, dev_id):
        self.dev_id = dev_id

    def get_dev_id(self):
        return self.dev_id

    def set_lorawan_port(self, lorawan_port):
        self.lorawan_port = lorawan_port

    def get_lorawan_port(self):
        return self.lorawan_port

    def create_state_machine(self):
        if self.protocol is self.LoRaWAN and self.direction is self.DIRECTION_UPLINK:
            self.sm = LoRaWAN_ACK_On_Error_RX(self, self.rule_id, self.window_size, self.tiles, self.tile_size, self.fragmenter)
        elif self.protocol is self.LoRaWAN and self.direction is self.DIRECTION_DOWNLINK:
            self.sm = LoRaWAN_ACK_Always_TX(self, self.rule_id, self.window_size, self.tiles, self.tile_size, self.fragmenter)
        else:
            logging.error("a state machine has not been defined for the session")
        return True

    def execute(self, buffer):
        self.sm.execute(buffer)
        return