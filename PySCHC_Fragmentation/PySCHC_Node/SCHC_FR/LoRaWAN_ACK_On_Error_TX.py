import math

from SCHC_FR.SCHC_Message import SCHC_Message
from machine import Timer
import time


class LoRaWAN_ACK_On_Error_TX:

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
    window_size = None
    n_windows = None

    schc_message = None

    # LoRaWAN parameters
    current_data_rate = None
    tile_size = None

    tiles_dic = None
    total_len_tiles = None
    current_tiles_pointer = None
    tiles_array = []

    schc_fragmenter = None

    ack_received = False

    chrono = None
    start_tx = None
    chrono_var = None
    end_first_msg = None

    times_array = {}

    def __init__(self, rule_id, window_size, tiles, tile_size, fragmenter):
        self.current_state = self.STATE_TX_INIT
        self.current_window = 0
        # self.current_data_rate = 2  # Spread Factor 12
        self.tiles_dic = tiles
        self.tile_size = tile_size
        self.current_tiles_pointer = 0
        self.rule_id = rule_id
        self.window_size = window_size
        self.schc_message = SCHC_Message()
        self.schc_fragmenter = fragmenter
        self.current_fcn = window_size - 1
        self.total_len_tiles = len(tiles)

        self.n_windows = math.ceil(len(tiles) / window_size)

        tiles_list = list(tiles.values())
        pointer = 0
        for x in range(0, self.n_windows):
            self.tiles_array.insert(x, tiles_list[pointer:pointer + window_size])
            pointer = pointer + window_size

        print("***** Sending {0} bytes in {1} tiles *******\n".format(int(len(tiles)*tile_size/8), len(tiles)))

        self.chrono = Timer.Chrono()
        self.chrono.start()
        self.chrono_var
        self.is_first_msg = True
        self.is_first_window = True
        self.sent_frag_counter = 0
        self.failed_frag_counter = 0
        self.times_array = {}

    def execute(self, buffer=None, rule_id=None):
        #print("Calling execute()")

        if buffer != None:
            (msg_type, w, c, rest, schc_payload) = SCHC_Message.decode_schc_msg(buffer, rule_id)
            if self.current_state is self.STATE_TX_WAIT_x_ACK and msg_type == SCHC_Message.SCHC_ACK_MSG and w > self.current_window:
                print("Discarting Message. The SCHC ACK does not match the session")
            elif self.current_state is self.STATE_TX_WAIT_x_ACK:
                self.TX_WAIT_x_ACK_received_ack(buffer)

        else:
            if self.current_state is self.STATE_TX_INIT:
                self.TX_INIT_send_fragment()
            elif self.current_state is self.STATE_TX_SEND:
                self.TX_SEND_send_fragment()
            elif self.current_state is self.STATE_TX_WAIT_x_ACK:
                self.TX_WAIT_x_ACK_received_ack(buffer)
            else:
                print("Wrong STATE")

        return

    def TX_INIT_send_fragment(self):
        print("")
        print("Calling TX_INIT_send_fragment")
        self.current_state = self.STATE_TX_SEND
        print("Changing STATE - From STATE_TX_INIT --> STATE_TX_SEND")
        self.execute()

    def TX_SEND_send_fragment(self):
        while True:
            # Given a data rate, the MTU of the LoRaWAN channel is obtained
            header_size_available, payload_size_available = self.schc_message.get_schc_payload_size_available(self.schc_fragmenter.data_rate)
            print("payload_size_available: " + str(payload_size_available))

            # Given the MTU and the Size of a tile, how many tiles can be sent in a SCHC Regular Message is obtained
            tiles_x_payload = math.floor(payload_size_available / self.tile_size)

            # Set counters
            fcn = self.current_fcn
            current_window = self.current_window

            # From the array of tiles, the tiles that will be sent in the SCHC Message are obtained
            window_length_in_tiles = len(self.tiles_array[self.current_window])
            payload = self.tiles_array[self.current_window][self.current_tiles_pointer:self.current_tiles_pointer+tiles_x_payload]
            self.current_tiles_pointer = self.current_tiles_pointer + tiles_x_payload


            if (self.current_tiles_pointer >= window_length_in_tiles) and (self.current_window < self.n_windows-1):
                # len(payload) < tiles_x_payload: Cuando len(payload) < tiles_x_payload se enviarám los ultimos tiles de la ventana actual.
                # self.current_tiles_pointer >= self.window_size: Significa que se estan enviando los ultimos tiles correspondientes a la actual ventana
                # self.current_window < self.n_windows-1: Con esto nos aseguramos que aun no nos hemos cambiado de ventana.
                # Evitamos asi enviar los tiles de la siguiente ventana
                # EN RESUMEN: Se estan enviando los ultimos tiles de la ventana (no es la ultima ventana)
                print("Sending last tiles for the window with ID: %d" % self.current_window)

                print("Sending %d tiles in a Regular SCHC Message" % len(payload))
                msg = self.schc_message.create_regular_schc_fragment(self.rule_id, 0, current_window, fcn, payload, self.tile_size)

                if self.is_first_msg:
                    self.chrono_var = self.chrono.read_ms()

                self.schc_fragmenter.lpwan_send_function(self.schc_fragmenter.get_socket_lorawan(), msg, self.rule_id)

                if self.is_first_msg:
                    self.end_first_msg = self.chrono.read_ms()
                    self.start_tx = self.chrono_var
                    self.times_array['iteracion'] = self.schc_fragmenter.index
                    self.times_array['tf'] = self.end_first_msg - self.start_tx - 2000 - 100.352
                    self.is_first_msg = False

                if self.is_first_window:
                    self.sent_frag_counter = self.sent_frag_counter + 1

                self.current_state = self.STATE_TX_WAIT_x_ACK
                print("Changing STATE - From STATE_TX_SEND --> STATE_TX_WAIT_x_ACK")

                print("Sending SCHC ACK Request")
                msg = self.schc_message.create_schc_ack_request(self.rule_id, self.current_window)
                self.schc_fragmenter.lpwan_send_function(self.schc_fragmenter.get_socket_lorawan(), msg, self.rule_id)

                return

            elif (self.current_tiles_pointer >= window_length_in_tiles) and (self.current_window == self.n_windows-1):
                # len(payload) < tiles_x_payload: Cuando len(payload) < tiles_x_payload se enviarám los ultimos tiles de la ventana actual.
                # self.current_tiles_pointer >= self.window_size: Significa que se estan enviando los ultimos tiles correspondientes a la actual ventana
                # self.current_window == self.n_windows-1: Con esto nos aseguramos que se envian los tiles de la ULTIMA ventana
                # EN RESUMEN: Se estan enviando los ULTIMOS tiles de la ULTIMA ventana
                print("Sending last tiles of SCHC packet for LAST window with ID: %d" % self.current_window)

                if len(payload)-1 != 0:
                    print("Sending %d tiles in a Regular SCHC Message" % len(payload[0:len(payload)-1]))
                    msg = self.schc_message.create_regular_schc_fragment(self.rule_id, 0, current_window, fcn, payload[0:len(payload)-1], self.tile_size)

                    if self.is_first_msg:
                        self.chrono_var = self.chrono.read_ms()

                    self.schc_fragmenter.lpwan_send_function(self.schc_fragmenter.get_socket_lorawan(), msg, self.rule_id)

                    if self.is_first_msg:
                        self.end_first_msg = self.chrono.read_ms()
                        self.start_tx = self.chrono_var
                        self.times_array['iteracion'] = self.schc_fragmenter.index
                        self.times_array['tf'] = self.end_first_msg - self.start_tx - 2000 - 100.352
                        self.is_first_msg = False

                    if self.is_first_window:
                        self.sent_frag_counter = self.sent_frag_counter + 1

                    print("Sending %d tiles in a All-1 SCHC Message" % len(payload[len(payload)-1:len(payload)]))
                    msg = self.schc_message.create_all_1_schc_fragment(self.rule_id, 0, current_window, 63, payload[len(payload)-1:len(payload)])
                    self.schc_fragmenter.lpwan_send_function(self.schc_fragmenter.get_socket_lorawan(), msg, self.rule_id)
                else:
                    print("Sending %d tiles in a All-1 SCHC Message" % len(payload[len(payload)-1:len(payload)]))
                    msg = self.schc_message.create_all_1_schc_fragment(self.rule_id, 0, current_window, 63, payload[len(payload)-1:len(payload)])

                    if self.is_first_msg:
                        self.chrono_var = self.chrono.read_ms()

                    self.schc_fragmenter.lpwan_send_function(self.schc_fragmenter.get_socket_lorawan(), msg, self.rule_id)

                    if self.is_first_msg:
                        self.end_first_msg = self.chrono.read_ms()
                        self.start_tx = self.chrono_var
                        self.times_array['iteracion'] = self.schc_fragmenter.index
                        self.times_array['tf'] = self.end_first_msg - self.start_tx - 2000 - 100.352
                        self.is_first_msg = False

                    if self.is_first_window:
                        self.sent_frag_counter = self.sent_frag_counter + 1


                self.current_state = self.STATE_TX_WAIT_x_ACK
                print("Changing STATE - From STATE_TX_SEND --> STATE_TX_WAIT_x_ACK")

                print("Sending SCHC ACK Request")
                msg = self.schc_message.create_schc_ack_request(self.rule_id, self.current_window)
                self.schc_fragmenter.lpwan_send_function(self.schc_fragmenter.get_socket_lorawan(), msg, self.rule_id)

                return

            elif len(payload) != 0:
                print("Sending %d tiles in a Regular SCHC Message" % len(payload))
                msg = self.schc_message.create_regular_schc_fragment(self.rule_id, 0, current_window, fcn, payload, self.tile_size)
                self.current_fcn = self.current_fcn - tiles_x_payload
                self.current_state = self.STATE_TX_SEND

                if self.is_first_msg:
                    self.chrono_var = self.chrono.read_ms()

                ### **************** Para generar error forzado *******************
                #if fcn != 62:
                self.schc_fragmenter.lpwan_send_function(self.schc_fragmenter.get_socket_lorawan(), msg, self.rule_id)
                ### **************** Para generar error forzado *******************

                if self.is_first_msg:
                    self.end_first_msg = self.chrono.read_ms()
                    self.start_tx = self.chrono_var
                    self.times_array['iteracion'] = self.schc_fragmenter.index
                    self.times_array['tf'] = self.end_first_msg - self.start_tx - 2000 - 100.352
                    self.is_first_msg = False

                if self.is_first_window:
                    self.sent_frag_counter = self.sent_frag_counter + 1



    def TX_WAIT_x_ACK_received_ack(self, buffer):
        print("")
        #print("Calling TX_WAIT_x_ACK_received_ack()")

        (w, c, bitmap_list) = SCHC_Message.decode_schc_ack(buffer, self.window_size)
        print("SCHC ACK received for window ID: " + str(w) + "!!!")

        if w != self.current_window:
            print("The received SCHC ACK window does not match the current SCHC ACK window. SCHC ACK discarded")
            return
        elif self.ack_received:
            print("Resending missing fragments in process. SCHC ACK discarded")
            return

        self.ack_received = True
        if self.current_window is w and c is 0:
            tiles_failed_array = []
            tiles_failed_array_reversed = []
            for x in range(0,len(bitmap_list)):
                if bitmap_list[x] == '0':
                    tiles_failed_array.append((self.window_size - 1 - x, [self.tiles_array[self.current_window][x]]))

            if len(tiles_failed_array) == 0:
                if self.is_first_window:
                    end_time_for_window = self.chrono.read_ms()
                    self.times_array['total_time_for_window'] = end_time_for_window - self.start_tx
                    self.is_first_window = False

                print("All tiles received OK for windows ID: " + str(self.current_window))
                self.current_window = self.current_window + 1
                self.current_tiles_pointer = 0
                self.current_fcn = self.window_size - 1
                self.current_state = self.STATE_TX_SEND
                print("Changing STATE - From STATE_TX_WAIT_x_ACK --> STATE_TX_SEND")
                print("")
                self.ack_received = False
                self.execute()
            else:
                #print("****** tiles_failed_array ****: " + str(tiles_failed_array))
                while len(tiles_failed_array) != 0:
                    # Given a data rate, the MTU of the LoRaWAN channel is obtained
                    header_size_available, payload_size_available = self.schc_message.get_schc_payload_size_available(
                        self.schc_fragmenter.data_rate)

                    # Given the MTU and the Size of a tile, how many tiles can be sent in a SCHC Regular Message is obtained
                    tiles_x_payload = math.floor(payload_size_available / self.tile_size)

                    consecutive_tiles = SCHC_Message.get_consecutive_filed_tiles(tiles_failed_array)

                    if consecutive_tiles > tiles_x_payload:
                        consecutive_tiles = tiles_x_payload

                    failed_tiles = []
                    first_fcn, first_tile = tiles_failed_array[0]
                    for x in range(0,consecutive_tiles):
                        fcn, tile = tiles_failed_array.pop()
                        failed_tiles.append(tile[0])

                    print("Re-Sending %d tiles in a Regular SCHC Message" % len(failed_tiles))
                    msg = self.schc_message.create_regular_schc_fragment(self.rule_id, 0, self.current_window, first_fcn, failed_tiles, self.tile_size)
                    self.schc_fragmenter.lpwan_send_function(self.schc_fragmenter.get_socket_lorawan(), msg, self.rule_id)

                    if self.is_first_window:
                        self.failed_frag_counter = self.failed_frag_counter + 1


                self.ack_received = False
                print("Sending SCHC ACK Request")
                msg = self.schc_message.create_schc_ack_request(self.rule_id, self.current_window)
                self.schc_fragmenter.lpwan_send_function(self.schc_fragmenter.get_socket_lorawan(), msg,
                                                         self.rule_id)

        elif self.current_window is w and c is 1:
            print("All tiles received OK for SCHC Packet")
            self.current_state = self.STATE_TX_END
            print("Changing STATE - From STATE_TX_WAIT_x_ACK --> STATE_TX_END")
            end_time = self.chrono.read_ms()

            if self.is_first_window:
                self.times_array['total_time_for_window'] = end_time - self.start_tx
                self.is_first_window = False

            self.times_array['total_time_for_schc_packet'] = end_time - self.start_tx
            self.times_array['failed_fragments'] = self.failed_frag_counter
            self.times_array['sent_fragments'] = self.sent_frag_counter
            self.schc_fragmenter.total_times.append(self.times_array)


        return
