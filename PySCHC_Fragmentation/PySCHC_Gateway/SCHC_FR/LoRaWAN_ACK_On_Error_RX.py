import base64
import logging

from SCHC_FR.SCHC_Message import SCHC_Message


class LoRaWAN_ACK_On_Error_RX:

    STATE_RX_INIT = 0
    STATE_RX_RCV_WINDOW = 1
    STATE_RX_WAIT_x_MISSING_FRAGS = 2
    STATE_RX_WAIT_END = 3
    STATE_RX_END = 4
    STATE_RX_TERMINATE_ALL = 5

    session = None

    current_state = None
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
    current_tiles_pointer = None
    tiles_array = None
    tile_size_bytes = None

    schc_fragmenter = None

    last_ack_sended = None
    last_body_dic = None

    bitmap = None

    all_1_pointer = None

    def __init__(self, session, rule_id, window_size, tiles, tile_size, fragmenter):
        self.session = session
        self.current_state = self.STATE_RX_INIT
        self.current_window = 0
        self.current_data_rate = 3  # Spread Factor 12
        self.tile_size = tile_size  # bits
        self.tile_size_bytes = int(tile_size/8)
        self.current_tiles_pointer = 0
        self.rule_id = rule_id
        self.window_size = window_size
        self.flow = []
        self.flow.append("Sender               Receiver")
        self.schc_fragmenter = fragmenter

        w, h = window_size, 4
        self.tiles_array = [[None for x in range(w)] for y in range(h)]
        self.bitmap = [['0' for x in range(w)] for y in range(h)]

    def execute(self, buffer):
        if self.current_state is self.STATE_RX_INIT:
            self.RX_INIT_recv_fragment(buffer)
        elif self.current_state is self.STATE_RX_RCV_WINDOW:
            self.RX_RCV_WINDOW_recv_fragment(buffer)
        elif self.current_state is self.STATE_RX_WAIT_x_MISSING_FRAGS:
            self.RX_WAIT_x_MISSING_FRAGS_recv_fragment(buffer)
        elif self.current_state is self.STATE_RX_END:
            self.RX_END_recv_ack_req(buffer)
        else:
            logging.error("Wrong State")

    def RX_INIT_recv_fragment(self, buffer):
        logging.debug("Entering to RX_INIT_recv_fragment")
        logging.info("Changing STATE - From RX_INIT --> STATE_RX_RCV_WINDOW")
        self.current_state = self.STATE_RX_RCV_WINDOW
        self.execute(buffer)
        return

    def RX_RCV_WINDOW_recv_fragment(self, buffer):
        logging.debug("Entering to RX_RCV_WINDOW_recv_fragment")
        (msg_type, w, fcn, rcs, schc_payload) = SCHC_Message().decode_schc_msg(buffer, self.rule_id)

        if msg_type == SCHC_Message.SCHC_ACK_REQ_MSG:
            logging.info("Receiving a SCHC ACK Request")
            logging.info("|--- ACK REQ, W={0:1d} ---->|".format(w))
            msg = self.last_ack_sended
            body_dic = self.last_body_dic

            fragmenter = self.schc_fragmenter
            fragmenter.lpwan_send_function(body_dic, self.session.get_downlink_url())
            logging.info("Resending a SCHC ACK Msg")
            logging.info("|<-- ACK, -------------|")

        elif msg_type == SCHC_Message.SCHC_FRAGMENT_MSG and fcn == self.window_size and rcs is not None:
            logging.info("Receiving a All-1 SCHC Fragment")
            # Receiving fragments that are not the last fragments of the SCHC packet
            tiles_in_payload = int(len(schc_payload)/self.tile_size_bytes)
            dic_pointer = (self.window_size - 1) - fcn
            logging.info("|-----W={0:1d}, FCN={1:2d}----->| {2:2d} tiles recv".format(w, fcn, tiles_in_payload))

            for i in range(tiles_in_payload):
                pointer = i * self.tile_size_bytes
                self.tiles_array[self.current_window][dic_pointer] = schc_payload[pointer:pointer + self.tile_size_bytes]
                self.bitmap[self.current_window][dic_pointer] = '1'
                dic_pointer = dic_pointer + 1

            if SCHC_Message.integrity_check(self.tiles_array, rcs):
                logging.info("Sending a SCHC ACK Msg with Integrity Check success")
                c = 1
                msg = SCHC_Message.create_schc_ack(self.rule_id, 0, self.current_window, c, self.bitmap[self.current_window])
                logging.info("|<-- ACK, W={0:1d}, C={1:1d} ----|".format(w, c))
                logging.info("Changing STATE - From STATE_RX_RCV_WINDOW --> STATE_RX_END")
                self.current_state = self.STATE_RX_END
            else:
                logging.info("Sending a SCHC ACK Msg with Integrity Check failure")
                c = 0
                msg = SCHC_Message.create_schc_ack(self.rule_id, 0, self.current_window, c, self.bitmap[self.current_window])
                logging.info("|<-- ACK, W={0:1d}, C={1:1d} ----| {2:2s} (bitmap)".format(w, c, ''.join(self.bitmap[self.current_window])))

            body_dic = {}
            body_dic['payload_raw'] = base64.b64encode(msg).decode("utf-8")
            body_dic['dev_id'] = self.session.get_dev_id()
            body_dic['port'] = self.session.get_lorawan_port()
            body_dic['confirmed'] = False
            self.last_ack_sended = msg
            self.last_body_dic = body_dic

            fragmenter = self.schc_fragmenter
            fragmenter.lpwan_send_function(body_dic, self.session.get_downlink_url())

            # aux = []
            # for x in self.tiles_array:
            #     for y in x:
            #         if y != None:
            #             for j in y:
            #                 if j != None:
            #                     aux.append(hex(j)[2:])
            # schc_packet = ''.join(aux)

        elif msg_type == SCHC_Message.SCHC_FRAGMENT_MSG:
            logging.info("Receiving a Regular SCHC Fragment")
            # Receiving fragments that are not the last fragments of the SCHC packet
            tiles_in_payload = int(len(schc_payload)/self.tile_size_bytes)
            dic_pointer = (self.window_size - 1) - fcn
            self.all_1_pointer = dic_pointer + tiles_in_payload
            logging.info("|-----W={0:1d}, FCN={1:2d}----->| {2:2d} tiles recv".format(w, fcn, tiles_in_payload))

            for i in range(tiles_in_payload):
                pointer = i * self.tile_size_bytes
                try:
                    self.tiles_array[self.current_window][dic_pointer] = schc_payload[pointer:pointer + self.tile_size_bytes]
                except:
                    logging.error("self.current_window: " + str(self.current_window))
                    logging.error("dic_pointer: " + str(dic_pointer))
                    logging.error("pointer: " + str(pointer))
                    logging.error("self.tile_size_bytes: " + str(self.tile_size_bytes))

                self.bitmap[self.current_window][dic_pointer] = '1'
                dic_pointer = dic_pointer + 1

            if dic_pointer >= self.window_size:
                logging.info("Sending a SCHC ACK Msg")
                c = 0   # No se ha realizado integrity Check
                msg = SCHC_Message.create_schc_ack(self.rule_id, 0, self.current_window, c, self.bitmap[self.current_window])

                body_dic = {}
                body_dic['payload_raw'] = base64.b64encode(msg).decode("utf-8")
                body_dic['dev_id'] = self.session.get_dev_id()
                body_dic['port'] = self.session.get_lorawan_port()
                body_dic['confirmed'] = False
                self.last_ack_sended = msg
                self.last_body_dic = body_dic

                fragmenter = self.schc_fragmenter
                fragmenter.lpwan_send_function(body_dic, self.session.get_downlink_url())
                bitmap = ''.join(self.bitmap[self.current_window])
                logging.info("|<-- ACK, W={0:1d}, C={1:1d} ----| {2:2s} (bitmap)".format(w, c, bitmap))

                if bitmap.find('0') != -1:
                    logging.debug("There are errors in the SCHC Fragments received")
                    logging.info("Changing STATE - From STATE_RX_RCV_WINDOW --> STATE_RX_WAIT_x_MISSING_FRAGS")
                    self.current_state = self.STATE_RX_WAIT_x_MISSING_FRAGS
                else:
                    self.current_window = self.current_window + 1

        else:
            logging.error("Receiving a Incompatibility Message ")

        return

    def RX_WAIT_x_MISSING_FRAGS_recv_fragment(self, buffer):
        logging.debug("Calling to RX_WAIT_x_MISSING_FRAGS_recv_fragment")
        (msg_type, w, fcn, rcs, schc_payload) = SCHC_Message().decode_schc_msg(buffer, self.rule_id)

        if msg_type == SCHC_Message.SCHC_ACK_REQ_MSG:
            logging.info("Receiving a SCHC ACK Request")
            logging.info("|--- ACK REQ, W={0:1d} ---->|".format(w))
            msg = self.last_ack_sended
            body_dic = self.last_body_dic

            fragmenter = self.schc_fragmenter
            fragmenter.lpwan_send_function(body_dic, self.session.get_downlink_url())
            logging.info("Resending a SCHC ACK Msg")
            logging.info("|<-- ACK, -------------|")
        else:
            logging.info("Receiving a Regular SCHC Fragment")
            # Receiving fragments that are not the last fragments of the SCHC packet
            tiles_in_payload = int(len(schc_payload) / self.tile_size_bytes)
            dic_pointer = (self.window_size - 1) - fcn
            self.all_1_pointer = dic_pointer + tiles_in_payload
            logging.info("|-----W={0:1d}, FCN={1:2d}----->| {2:2d} tiles recv".format(w, fcn, tiles_in_payload))

            for i in range(tiles_in_payload):
                pointer = i * self.tile_size_bytes
                self.tiles_array[self.current_window][dic_pointer] = schc_payload[
                                                                     pointer:pointer + self.tile_size_bytes]
                self.bitmap[self.current_window][dic_pointer] = '1'
                dic_pointer = dic_pointer + 1

                bitmap_str = ''.join(self.bitmap[self.current_window])

            if bitmap_str.find('0') == -1:
                logging.info("Sending a SCHC ACK Msg")
                c = 0  # No se ha realizado integrity Check
                msg = SCHC_Message.create_schc_ack(self.rule_id, 0, self.current_window, c,
                                                   self.bitmap[self.current_window])

                body_dic = {}
                body_dic['payload_raw'] = base64.b64encode(msg).decode("utf-8")
                body_dic['dev_id'] = self.session.get_dev_id()
                body_dic['port'] = self.session.get_lorawan_port()
                body_dic['confirmed'] = False
                self.last_ack_sended = msg
                self.last_body_dic = body_dic

                fragmenter = self.schc_fragmenter
                fragmenter.lpwan_send_function(body_dic, self.session.get_downlink_url())
                bitmap = ''.join(self.bitmap[self.current_window])
                logging.info("|<-- ACK, W={0:1d}, C={1:1d} ----| {2:2s} (bitmap)".format(w, c, bitmap))

                if bitmap.find('0') != -1:
                    logging.debug("There are errors in the SCHC Fragments received")
                else:
                    logging.info("Changing STATE - From STATE_RX_WAIT_x_MISSING_FRAGS --> STATE_RX_RCV_WINDOW")
                    self.current_state = self.STATE_RX_RCV_WINDOW
                    self.current_window = self.current_window + 1




    def RX_END_recv_ack_req(self, buffer):
        logging.debug("Calling to RX_END_recv_ack_req")
        (msg_type, w, fcn, rcs, schc_payload) = SCHC_Message().decode_schc_msg(buffer, self.rule_id)

        if msg_type == SCHC_Message.SCHC_ACK_REQ_MSG:
            logging.info("Receiving a SCHC ACK Request")
            logging.info("|--- ACK REQ, W={0:1d} ---->|".format(w))
            msg = self.last_ack_sended
            body_dic = self.last_body_dic

            fragmenter = self.schc_fragmenter
            fragmenter.lpwan_send_function(body_dic, self.session.get_downlink_url())
            logging.info("Resending a SCHC ACK Msg")
            logging.info("|<-- ACK, -------------|")
            logging.info("Changing STATE - From STATE_RX_END --> STATE_RX_TERMINATE_ALL")
            self.current_state = self.STATE_RX_TERMINATE_ALL




