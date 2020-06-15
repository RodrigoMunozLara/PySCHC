import ubinascii
import struct


class SCHC_Message:
    DR_AUS915 = {
        0: 51,
        1: 51,
        2: 51,
        3: 115,
        4: 222,
        5: 222
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
    def create_schc_ack_request(rule_id, w):
        w_new = w << 6
        fcn = 0
        header = w_new | fcn
        header_bf = struct.pack('>B', header)
        # print("W + FCN: " + binascii.hexlify(header_bf).__str__())

        #msg = b''.join([header_bf, payload])
        msg = header_bf
        print("| FPort  | LoRaWAN payload |")
        print("+ ------ + ----------------+")
        print("| RuleID |   W    |  FCN   |")
        print("+ ------ + ------ + ------ + ")
        print('|{0:6d}  |{1:4d}    |{2:4d}    |'.format(rule_id, w, fcn))
        print("")
        # print("Regular SCHC Fragment Msg: " + str(binascii.hexlify(msg)))
        return msg

    @staticmethod
    def create_regular_schc_fragment(rule_id, dtag, w, fcn, payload, tile_size):
        # Regular SCHC Fragment header
        w_new = w << 6
        header = w_new | fcn
        header_bf = struct.pack('>B', header)
        # print("W + FCN: " + binascii.hexlify(header_bf).__str__())

        msg = b''.join([header_bf, b''.join(payload)])

        print("| FPort  |  LoRaWAN payload          |")
        print("+ ------ + ------------------------- +")
        print("| RuleID |   W    |  FCN   | Payload |")
        print("+ ------ + ------ + ------ + ------- +")
        print('|{0:6d}  |{1:4d}    |{2:4d}    |{3:3d} bytes|'.format(rule_id, w, fcn, len(payload)*int(tile_size/8)))
        print("")
        # print("Regular SCHC Fragment Msg: " + str(binascii.hexlify(msg)))
        return msg

    @staticmethod
    def create_all_1_schc_fragment(rule_id, dtag, w, fcn, payload):
        # All-1 SCHC Fragment header
        # Mask definition
        header_mask_high = int('C0', 16)
        header_mask_low = int('3F', 16)

        w_new = w << 6
        fcn_new = fcn & header_mask_low
        header = w_new | fcn
        header_bf = struct.pack('>B', header)
        # print("W + FCN: " + binascii.hexlify(header_bf).__str__())

        rcs = '0xacde3214'
        rcs_int = int(rcs, 16)
        rcs_bf = struct.pack('>I', rcs_int)

        msg = b''.join([header_bf, rcs_bf, b''.join(payload)])
        print("| FPort  | LoRaWAN payload                                  |")
        print("+ ------ + ------------------------------------------------ +")
        print("| RuleID |   W    | FCN=All-1 |  RCS    | Payload           |")
        print("+ ------ + ------ + --------- + ------- + ----------------- +")
        print("| 8 bits | 2 bits | 6 bits    | 32 bits | Last tile, if any |")
        print('|{0:6d}  |   {1:0d}    |   {2:0d}      | {3} |{4:3d} tile |'.format(rule_id, w, fcn, rcs, len(payload)))
        print("")


        #print("SCHC All-1 Msg: " + str(ubinascii.hexlify(msg)))
        return msg

    @staticmethod
    def decode_schc_msg(msg, rule_id):
        msg_len = len(msg)
        buffer = list(msg)

        schc_header = buffer[0]

        # Mask definition
        header_mask_high = int('C0', 16)
        header_mask_medium = int('20', 16)
        header_mask_low = int('1F', 16)

        w = (schc_header & header_mask_high) >> 6
        c = (schc_header & header_mask_medium) >> 5
        rest = (schc_header & header_mask_low)

        if rule_id == 20 and c==1 and w==4 and rest==31:
            print("Receiving Receiver-Abort msg")
            return (SCHC_Message.SCHC_RECEIVER_ABORT, w, c, rest, None)
            #(msg_type, w, c, rest, schc_payload)
        else :
            print("Receiving SCHC ACK msg")
            return (SCHC_Message.SCHC_ACK_MSG, w, c, rest, None)
            #(msg_type, w, c, rest, schc_payload)


    @staticmethod
    def decode_schc_ack(msg, window_size):
        msg_len = len(msg)
        #print("SCHC ACK len: %d" % msg_len)
        buffer = list(msg)

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

        bitmap = '{0:05b}'.format(schc_header & header_mask_low)
        #print("****** TEST ******: bitmap: " + str(bitmap))
        for x in range(1,len(buffer)):
            bitmap = bitmap + '{0:08b}'.format(buffer[x])

        bitmap_total_lengh = window_size - len(bitmap)
        for y in range(bitmap_total_lengh):
            bitmap = bitmap + '1'

        bitmap_list = list(bitmap)
        #print("******************** bitmap_list: " + str(bitmap_list) )
        #print("******************** len(bitmap_list): " + str(len(bitmap_list)) )
        return w, c, bitmap_list

    @staticmethod
    def get_rule_id(buffer):
        return 20

    @staticmethod
    def get_dtag(buffer):
        return 0

    @staticmethod
    def padding_in_word(buff, word_size_bits, prefix_bits):
        if len(buff) <= prefix_bits:
            resto = prefix_bits-len(buff)
            for x in range(1, resto + 1):
                buff.append('1')
            pre_bitmap = ''.join(buff[0:prefix_bits])
            new_buffer = ''
        else:
            pre_bitmap = ''.join(buff[0:prefix_bits])
            new_buffer = ''.join(buff[prefix_bits:len(buff)]) + '1' * (word_size_bits - (len(buff[prefix_bits:len(buff)]) % word_size_bits))

        print("pre_bitmap: %s" % pre_bitmap)
        print("new_buffer: %s" % new_buffer)
        return pre_bitmap, new_buffer

    @staticmethod
    def get_consecutive_filed_tiles(filed_tiles):
        fcn, tile = filed_tiles[0]
        for x in range(1,len(filed_tiles)):
            fcn_next, tile_next = filed_tiles[x]
            if fcn-x != fcn_next:
                return x

        return (x+1)
