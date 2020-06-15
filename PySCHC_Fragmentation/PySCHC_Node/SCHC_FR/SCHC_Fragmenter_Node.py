import _thread
import time

from SCHC_FR.SCHC_Message import SCHC_Message
from SCHC_FR.SCHC_Session_Node import SCHC_Session_Node


class SCHC_Fragmenter_Node:
    # protocol type
    protocol_type = None
    LoRaWAN = 1
    Sigfox = 2

    DIRECTION_UPLINK = 1
    DIRECTION_DOWNLINK = 2

    # functions
    callback = None
    lpwan_send_function = None
    lpwan_send_function_without_recv = None
    lpwan_recv_function = None

    # Session pool
    uplink_session_pool = {}
    downlink_session_pool = {}

    socket_lorawan = None

    total_times = []
    index = None
    tile_size = None

    def __init__(self, protocol):
        self.protocol_type = protocol
        self.index = 0

    def set_callback(self, callback_function):
        self.callback = callback_function

    def set_lpwan_send_function(self, send_function):
        self.lpwan_send_function = send_function

    def set_lpwan_send_function_without_recv(self, send_function_without_recv):
        self.lpwan_send_function_without_recv = send_function_without_recv

    def set_lpwan_recv_function(self, recv_function):
        self.lpwan_recv_function = recv_function

    def get_socket_lorawan(self):
        return self.socket_lorawan

    def set_socket_lorawan(self, socket):
        self.socket_lorawan = socket

    def set_data_rate(self, data_rate):
        self.data_rate = data_rate

    def set_tile_size(self, tile_size):
        self.tile_size = tile_size

    def initialize(self):
        # Se crea una sesion uplink y una sesion downlink. Son almacenadas en un pool de sesiones

        # +++++++++ UPLINK SESSION ++++++++++++++++
        # The session is created and stored in a session pool
        rule_id = 20
        uplink_session = SCHC_Session_Node(self.protocol_type, rule_id, self.DIRECTION_UPLINK, self.tile_size)

        if uplink_session is -1:
            return -1

        dtag = uplink_session.get_dtag()
        uplink_session.set_fragmenter(self)
        self.uplink_session_pool[(rule_id, dtag)] = uplink_session

        # +++++++++ DOwNLINK SESSION ++++++++++++++++
        # The session is created and stored in a session pool
        rule_id = 21
        downlink_session = SCHC_Session_Node(self.protocol_type, rule_id, self.DIRECTION_DOWNLINK, self.tile_size)

        if downlink_session is -1:
            return -1

        dtag = downlink_session.get_dtag()
        downlink_session.set_fragmenter(self)
        self.downlink_session_pool[(rule_id, dtag)] = downlink_session

    def send(self, buffer):
        # Se llama a la session creada en el metodo initialize. Se divide la data en N tiles. Se crea la maquina de
        # estados en la sesion

        print("Entering send()")
        rule_id = 20
        dtag = 0
        self.index = self.index + 1
        uplink_session = self.get_uplink_session(rule_id, dtag)

        # The SCHC Packet is divided in tiles
        n_tiles = uplink_session.divide_in_tiles(buffer)
        print("The SCHC Packet has been divided into %d tiles" % n_tiles)

        # The state machine is created and the start method is executed
        uplink_session.create_state_machine()
        uplink_session.execute()
        # args = ()
        # _thread.start_new_thread(uplink_session.sm.execute, args)

        if uplink_session.sm.current_state == uplink_session.sm.STATE_TX_END:
            print("Transmission Completed. Deleting session ID: %d" % id(uplink_session))
            self.terminate_uplink_session(rule_id, dtag)

        print("Leaving send()")

    def reception_msg(self, buffer, port):
        print("Entering reception_msg()")

        # Get the session
        rule_id = port
        dtag = SCHC_Message.get_dtag(buffer)
        if rule_id is 20:
            session = self.get_uplink_session(rule_id, dtag)
        elif rule_id is 21:
            session = self.get_downlink_session(rule_id, dtag)

        # Sending message to State Machine
        session.execute(buffer, rule_id)
        #_thread(session.sm.execute, args=(buffer,))

    def get_uplink_session(self, rule_id, dtag):
        if (rule_id, dtag) in self.uplink_session_pool:
            session = self.uplink_session_pool.get((rule_id, dtag))
            print("Get session from pool with ID: %d" % id(session))
            return session
        else:
            session = SCHC_Session_Node(self.protocol_type, rule_id, self.DIRECTION_UPLINK, self.tile_size)
            self.uplink_session_pool[(rule_id, dtag)] = session
            session.set_fragmenter(self)
            session.create_state_machine()
            print("Creating session with ID: %d" % id(session))
            return session

    def get_downlink_session(self, rule_id, dtag):
        if (rule_id, dtag) in self.downlink_session_pool:
            session = self.downlink_session_pool.get((rule_id, dtag))
            print("Get session from pool with ID: %d" % id(session))
            return session
        else:
            session = SCHC_Session_Node(self.protocol_type, rule_id, self.DIRECTION_DOWNLINK, self.tile_size)
            self.downlink_session_pool[(rule_id, dtag)] = session
            session.set_fragmenter(self)
            session.create_state_machine()
            print("Creating session with ID: %d" % id(session))
            return session

    def terminate_uplink_session(self, rule_id, dtag):
        if (rule_id, dtag) in self.uplink_session_pool:
            session = self.uplink_session_pool.get((rule_id, dtag))
            #print("Deleting session from pool with ID: %d" % id(session))
            self.uplink_session_pool.pop((rule_id, dtag))
            return
