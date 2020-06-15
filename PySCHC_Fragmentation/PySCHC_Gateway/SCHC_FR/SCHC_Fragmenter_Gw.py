import logging

from SCHC_FR.SCHC_Message import SCHC_Message
from SCHC_FR.SCHC_Session_Gw import SCHC_Session_Gw


class SCHC_Fragmenter_Gw:
    # protocol type
    protocol_type = None
    LoRaWAN = 1
    Sigfox = 2

    DIRECTION_UPLINK = 1
    DIRECTION_DOWNLINK = 2

    # functions
    callback = None
    lpwan_send_function = None
    lpwan_recv_function = None

    # Session pool
    downlink_session_pool = {}
    uplink_session_pool = {}

    def __init__(self, protocol):
        self.protocol_type = protocol

    def set_callback(self, callback_function):
        self.callback = callback_function

    def set_lpwan_send_function(self, send_function):
        self.lpwan_send_function = send_function

    def set_lpwan_recv_function(self, recv_function):
        self.lpwan_recv_function = recv_function

    def initialize(self):
        # formato = "%(levelname)s:%(asctime)s: %(thread)d %(module)s.%(funcName)s: %(message)s"
        # logging.basicConfig(format=formato, level=logging.DEBUG,
        #                     datefmt="%H:%M:%S")

        # +++++++++ UPLINK SESSION ++++++++++++++++
        # The session is created and stored in a session pool
        rule_id = 20
        uplink_session = SCHC_Session_Gw(self.protocol_type, rule_id, self.DIRECTION_UPLINK)

        if uplink_session == -1:
            return -1

        dtag = uplink_session.get_dtag()
        uplink_session.set_fragmenter(self)
        self.uplink_session_pool[(rule_id, dtag)] = uplink_session

        # The state machine is created and the start method is executed
        uplink_session.create_state_machine()

        # +++++++++ DOwNLINK SESSION ++++++++++++++++
        # The session is created and stored in a session pool
        rule_id = 21
        downlink_session = SCHC_Session_Gw(self.protocol_type, rule_id, self.DIRECTION_DOWNLINK)

        if downlink_session == -1:
            return -1

        dtag = downlink_session.get_dtag()
        downlink_session.set_fragmenter(self)
        self.downlink_session_pool[(rule_id, dtag)] = downlink_session

        # The state machine is created and the start method is executed
        downlink_session.create_state_machine()

    def process_request(self, buffer, downlink_url, dev_id, rule_id):
        logging.debug("Entering to process_request...")
        session = None
        if len(buffer) > 0:
            # Get the session
            dtag = SCHC_Message.get_dtag(buffer)
            if rule_id == 20:
                session = self.get_uplink_session(rule_id, dtag)
                session.set_downlink_url(downlink_url)
                session.set_dev_id(dev_id)
                session.set_lorawan_port(rule_id)
            elif rule_id == 21:
                session = self.get_downlink_session(rule_id, dtag)
                session.set_downlink_url(downlink_url)
            else:
                logging.error("Rule ID not correct!!!!")
                return

            # Sending message to State Machine
            session.execute(buffer)
            # hilo = threading.Thread(target=session.sm.execute, args=(buffer,))
            # hilo.start()
            # logging.warning("Thread Active Count: %d" % threading.active_count())

            if session.sm.current_state == session.sm.STATE_RX_TERMINATE_ALL:
                logging.info("Reception complete. Deleting session ID: %d" % id(session))
                self.terminate_uplink_session(rule_id, dtag)
                print("")
                print("")
                print("")

            logging.debug("Leaving to process_request...")


    def get_uplink_session(self, rule_id, dtag):
        if (rule_id, dtag) in self.uplink_session_pool:
            session = self.uplink_session_pool.get((rule_id, dtag))
            logging.debug("Get session from pool with ID: %d" % id(session))
            return session
        else:
            session = SCHC_Session_Gw(self.protocol_type, rule_id, self.DIRECTION_UPLINK)
            self.uplink_session_pool[(rule_id, dtag)] = session
            session.set_fragmenter(self)
            session.create_state_machine()
            logging.debug("Creating session with ID: %d" % id(session))
            return session

    def get_downlink_session(self, rule_id, dtag):
        if (rule_id, dtag) in self.downlink_session_pool:
            session = self.downlink_session_pool.get((rule_id, dtag))
            logging.debug("Get session from pool with ID: %d" % id(session))
            return session
        else:
            session = SCHC_Session_Gw(self.protocol_type, rule_id, self.DIRECTION_DOWNLINK)
            self.downlink_session_pool[(rule_id, dtag)] = session
            session.set_fragmenter(self)
            session.create_state_machine()
            logging.debug("Creating session with ID: %d" % id(session))
            return session

    def terminate_uplink_session(self, rule_id, dtag):
        if (rule_id, dtag) in self.uplink_session_pool:
            session = self.uplink_session_pool.get((rule_id, dtag))
            logging.debug("Deleting session from pool with ID: %d" % id(session))
            self.uplink_session_pool.pop((rule_id, dtag))
            return
