from SCHC_FR.LoRaWAN_ACK_Always_RX import LoRaWAN_ACK_Always_RX
from SCHC_FR.LoRaWAN_ACK_On_Error_TX import LoRaWAN_ACK_On_Error_TX


class SCHC_Session_Node:
    LoRaWAN = 1
    Sigfox = 2

    DIRECTION_UPLINK = 1
    DIRECTION_DOWNLINK = 2

    layer2_word_size = None  # in bits (The L2 word size used by LoRaWAN is 1 byte (8 bits))

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

    fragmenter = None

    def __init__(self, protocol, rule_id, direction, tile_size_byte):
        if protocol is self.LoRaWAN:
            self.layer2_word_size = 8

            self.dtag_size = 0
            self.w_size = 2
            self.fcn_size = 6
            self.window_size = 63  # window_size <= 2^N
            self.tile_size = tile_size_byte * 8  # in bits

            self.max_ack_requests = 8
            self.retransmission_timer_value = 0
            self.inactivity_timer_value = 12 * 60 * 60  # segundos
            self.direction = direction
            self.attempts_counter = 0
            self.dtag = 0
            self.rule_id = rule_id
            self.protocol = protocol
            self.tiles = {}
            #            self.current_data_rate = 0

            '''
            8.4.3.1.  Sender behavior

               At the beginning of the fragmentation of a new SCHC Packet,

               o  the fragment sender MUST select a Rule ID and DTag value pair for
                  this SCHC Packet.  A Rule MUST NOT be selected if the values of M
                  and WINDOW_SIZE for that Rule are such that the SCHC Packet cannot
                  be fragmented in (2^M) * WINDOW_SIZE tiles or less.
            '''
            min_frag_size = (2 ** self.w_size) * self.window_size
            if len(self.tiles) > min_frag_size:
                print(
                    "ERROR: The SCHC standard does not allow fragmentation because it does not meet the maximum amount "
                    "of tiles")
                return

    def get_dtag(self):
        return self.dtag

    def set_fragmenter(self, fragmenter):
        self.fragmenter = fragmenter

    def divide_in_tiles(self, schc_packet):
        schc_packet_len = len(schc_packet)
        tile_size_byte = int(self.tile_size / 8)  # Tile Size en bytes
        j = 1
        for i in range(0, schc_packet_len, tile_size_byte):
            self.tiles[j] = schc_packet[i:i + tile_size_byte]
            j = j + 1
        return j - 1

    def create_state_machine(self):
        if self.protocol is self.LoRaWAN and self.direction is self.DIRECTION_UPLINK:
            self.sm = LoRaWAN_ACK_On_Error_TX(self.rule_id, self.window_size, self.tiles, self.tile_size,
                                              self.fragmenter)
        elif self.protocol is self.LoRaWAN and self.direction is self.DIRECTION_DOWNLINK:
            self.sm = LoRaWAN_ACK_Always_RX(self.rule_id, self.window_size, self.tiles, self.tile_size)
        else:
            print("Undefined State Machine", "a state machine has not been defined for the "
                                                     "session")
        return True

    def execute(self, buffer=None, rule_id=None):

        if self.sm.current_state == self.sm.STATE_TX_SEND and len(buffer) != 0:
            print("Discarting message. In this state it is not allowed to receive messages")
        else:
            self.sm.execute(buffer,rule_id)
