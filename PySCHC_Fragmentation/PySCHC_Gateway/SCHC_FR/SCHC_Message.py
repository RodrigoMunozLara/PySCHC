import binascii
import logging
import struct
from math import ceil


class SCHC_Message:
    DR_AUS915 = {
        0: 51,
        1: 51,
        2: 51,
        3: 115,
        4: 222,
        5: 222,
        6: 222,
        8: 33,
        9: 109,
        10: 222,
        11: 222,
        12: 222,
        13: 222,
    }

    SCHC_FRAGMENT_MSG = 0
    SCHC_ACK_MSG = 1
    SCHC_ACK_REQ_MSG = 2
    SCHC_SENDER_ABORT = 3
    SCHC_RECEIVER_ABORT = 4

    def __init__(self):
        pass

    def get_schc_payload_size_available(self, data_rate):
        #
        # +-------------+-----------------------------------------------------------------------------------------------+------------+
        # |             |                                       MAC payload (bits)                                      |            |
        # |             +------------------------------------------------------------+--------------+-------------------+            |
        # | MHDR (bits) |                         FHDR (bits)                        |              |                   | MIC (bits) |
        # |             +----------------+--------------+-------------+--------------+ Fport (bits) | FRMPayload (bits) |            |
        # |             | DevAddr (bits) | FCtrl (bits) | FCnt (bits) | Fopts (bits) |              |                   |            |
        # +-------------+----------------+--------------+-------------+--------------+--------------+-------------------+------------+
        # |      8      |       32       |       8      |      16     |       0      |       8      |         n         |     32     |
        # +-------------+----------------+--------------+-------------+--------------+--------------+-------------------+------------+

        MACPayload_size = self.DR_AUS915[data_rate] * 8  # in bits
        FHDR_size = 64  # in bits
        FPort_size = 8  # in bits
        FRMPayload_size = MACPayload_size - FHDR_size - FPort_size  # in bits

        SCHC_header_size = 8  # in bits
        SCHC_payload_size_available = FRMPayload_size - SCHC_header_size  # in bits

        # mac_payload_size_bites = MACPayload_size * 8
        # print("MAC payload size: %d bytes" %MACPayload_size)
        # print("MAC payload size: %d bits" % mac_payload_size_bites)
        # print("FRM payload size: %d bits" % FRMPayload_size)
        # print("SCHC payload size: %d bits" % SCHC_payload_size_available)
        # print("SCHC payload size: %d bytes" % int(SCHC_payload_size_available/8))

        return SCHC_header_size, SCHC_payload_size_available

    @staticmethod
    def create_regular_schc_fragment(rule_id, dtag, w, fcn, payload):
        # Regular SCHC Fragment header
        w_new = w << 6
        header = w_new | fcn
        header_bf = struct.pack('>B', header)
        # print("W + FCN: " + binascii.hexlify(header_bf).__str__())

        # msg = b''.join([header_bf, payload])
        msg = b''.join([header_bf, b''.join(payload)])
        logging.info("| FPort  |  LoRaWAN payload          |")
        logging.info("+ ------ + ------------------------- +")
        logging.info("| RuleID |   W    |  FCN   | Payload |")
        logging.info("+ ------ + ------ + ------ + ------- +")
        logging.info('|{0:6d}  |{1:4d}    |{2:4d}    |{3:3d} bytes|'.format(rule_id, w, fcn, len(payload)*10))
        logging.info("")
        # print("Regular SCHC Fragment Msg: " + str(binascii.hexlify(msg)))
        return msg

    @staticmethod
    def create_all_1_schc_fragment(rule_id, dtag, w, fcn, payload):
        # All-1 SCHC Fragment header
        w_new = w << 6
        header = w_new | fcn
        header_bf = struct.pack('>B', header)
        # print("W + FCN: " + binascii.hexlify(header_bf).__str__())

        # msg = b''.join([header_bf, payload])
        msg = b''.join([header_bf, b''.join(payload)])
        logging.info("| FPort  |  LoRaWAN payload          |")
        logging.info("+ ------ + ------------------------- +")
        logging.info("| RuleID |   W    |  FCN   | Payload |")
        logging.info("+ ------ + ------ + ------ + ------- +")
        logging.info('|{0:6d}  |{1:4d}    |{2:4d}    |{3:3d} bytes|'.format(rule_id, w, fcn, len(payload)*10))
        logging.info("")
        # print("Regular SCHC Fragment Msg: " + str(binascii.hexlify(msg)))
        return msg

    @staticmethod
    def create_schc_ack(rule_id, dtag, w, c, bitmap):
        # SCHC ACK header
        w_new = w << 6
        c_new = c << 5
        ack_msg = None
        if c == 1:
            header = w_new | c_new
            header_bf = struct.pack('>B', header)
            logging.debug("W + FCN: " + binascii.hexlify(header_bf).__str__())
            ack_msg = header_bf
            logging.debug("| FPort   |  LoRaWAN payload          |")
            logging.debug("+--- ... -+- ... -+---+---------------+")
            logging.debug("| Rule ID |    W  | C | 00000 (bits)  |")
            logging.debug("+--- ... -+- ... -+---+---------------+")
            logging.debug('|{0:6d}   | {1:4d}  | 1 | 00000 (bits)  |'.format(rule_id, w))
            logging.debug("")
        elif c == 0:
            offset = 3
            bitmap_comp = SCHC_Message.bitmap_compression(bitmap, offset)
            ack_bin_format = '{0:02b}'.format(w) + '{0:01b}'.format(c) + ''.join(bitmap_comp)

            ack_hex = []
            for x in range(int(len(ack_bin_format)/4)):
                ack_hex.append(hex(int(ack_bin_format[x*4:x*4+4], 2))[2])
            ack_msg = binascii.unhexlify(''.join(ack_hex))

            logging.debug("| FPort   |  LoRaWAN payload          |")
            logging.debug("+--- ... -+- ... -+---+---------------+")
            logging.debug("| Rule ID |    W  | C | bitmap (bits) |")
            logging.debug("+--- ... -+- ... -+---+---------------+")
            logging.debug('|{0:6d}   | {1:4d}  | 0 | {2:1s}  '.format(rule_id, w, ''.join(bitmap_comp)))
            logging.debug("")

        logging.debug("SCHC ACK Msg: " + str(binascii.hexlify(ack_msg)))
        return ack_msg

    @staticmethod
    def decode_schc_msg(msg, rule_id):
        msg_len = len(msg)
        buffer = list(msg)

        if rule_id == 20 and msg_len == 1:
            logging.debug("Rule_id: 20 and msg_len: 1 byte")
            schc_header = buffer[0]
            header_mask_low = int('3F', 16)
            header_mask_high = int('C0', 16)
            fcn = (schc_header & header_mask_low)
            w = (schc_header & header_mask_high) >> 6
            if fcn == 0:
                logging.debug("Receiving SCHC ACK Request msg")
                return (SCHC_Message.SCHC_ACK_REQ_MSG, w, None, None, None)
        elif rule_id == 20 and msg_len > 1:
            logging.debug("Rule_id: 20 and msg_len > 1 byte")
            schc_header = buffer[0]
            header_mask_low = int('3F', 16)
            fcn = (schc_header & header_mask_low)
            if fcn == 63:
                logging.debug("Receiving SCHC Regular All-1 msg")
                (w, fcn, rcs, schc_payload) = SCHC_Message().decode_schc_fragment(buffer)
                return (SCHC_Message.SCHC_FRAGMENT_MSG, w, fcn, rcs, schc_payload)
            elif fcn != 0:
                logging.debug("Receiving SCHC Regular Fragment msg")
                (w, fcn, rcs, schc_payload) = SCHC_Message().decode_schc_fragment(buffer)
                return (SCHC_Message.SCHC_FRAGMENT_MSG, w, fcn, rcs, schc_payload)

    @staticmethod
    def decode_schc_fragment(msg):
        msg_len = len(msg)
        buffer = list(msg)

        schc_header = buffer[0]
        schc_header_bf = struct.pack('>B', buffer[0])

        # Mask definition
        header_mask_high = int('C0', 16)
        header_mask_low = int('3F', 16)

        w = (schc_header & header_mask_high) >> 6
        # w_bf = struct.pack('>B', w)

        fcn = (schc_header & header_mask_low)
        # fcn_bf = struct.pack('>B', fcn)

        if fcn == 63:
            rcs = buffer[1:5]
            schc_payload = buffer[5:msg_len]
        else:
            rcs = None
            schc_payload = buffer[1:msg_len]

        logging.debug("decode_schc_fragment --> w: " + str(w))
        logging.debug("decode_schc_fragment --> fcn: " + str(fcn))
        logging.debug("decode_schc_fragment --> rcs: " + str(rcs))
        logging.debug("decode_schc_fragment --> schc_payload: " + str(schc_payload))

        return w, fcn, rcs, schc_payload

    @staticmethod
    def decode_schc_ack(msg):
        msg_len = len(msg)
        logging.debug("message len: %d" % msg_len)
        buffer = list(msg)
        logging.debug("buffer[0]: %d" % buffer[0])
        logging.debug("buffer[1]: %d" % buffer[1])
        logging.debug("buffer[2]: %d" % buffer[2])
        logging.debug("Hex buffer[0]: %s" % hex(buffer[0]))
        logging.debug("Hex buffer[1]: %s" % hex(buffer[1]))
        logging.debug("Hex buffer[2]: %s" % hex(buffer[2]))
        logging.debug("Bin buffer[0]: %s" % bin(buffer[0]))
        logging.debug("Bin buffer[1]: %s" % bin(buffer[1]))
        logging.debug("Bin buffer[2]: %s" % bin(buffer[2]))

        schc_header = buffer[0]
        # schc_header_bf = struct.pack('>B', buffer[0])

        # Mask definition
        header_mask_high = int('C0', 16)
        header_mask_medium = int('20', 16)
        header_mask_low = int('1F', 16)

        w = (schc_header & header_mask_high) >> 6
        # w_bf = struct.pack('>B', w)

        c = (schc_header & header_mask_medium) >> 5
        # c_bf = struct.pack('>B', c)

        bitmap = (schc_header & header_mask_low)
        bitmap_str = bin(bitmap)[2:]
        for x in range(1, msg_len):
            bitmap_str = bitmap_str + bin(buffer[x])[2:]
        logging.debug("Bitmap: %s" % bitmap_str)
        bitmap_list = list(bitmap_str)

        return w, c, bitmap_list

    @staticmethod
    def get_rule_id(buffer):
        return 20

    @staticmethod
    def get_dtag(buffer):
        return 0

    @staticmethod
    def bitmap_compression(bitmap, offset):
        l2_word_size = 8  # tamaño de una palabra LoRaWAN en bits

        for x in range(len(bitmap)-1, -1, -1):
            if bitmap[x] == '0':
                actual_len = (x + 1) + offset
                bitcomp_array = bitmap[0:x+1]
                k = ceil((len(bitcomp_array) + offset) / l2_word_size)  # cantidad de palabras LoRaWAN que abarcan un offset + bitmap
                for y in range(k*l2_word_size-actual_len):
                    bitcomp_array.append('1')
                return bitcomp_array

        bitcomp_array = []
        for y in range(l2_word_size - offset):
            bitcomp_array.append('1')
        return bitcomp_array

    @staticmethod
    def integrity_check(tiles, rcs):
        return True
