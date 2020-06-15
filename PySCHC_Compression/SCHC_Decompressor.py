import struct

from Gateway.SCHC_CD.SCHC_Parser import SCHC_Parser


class SCHC_Decompressor:
    def __init__(self, rm):
        self.rule_manager = rm
        self.context = rm.context
        self.parser = SCHC_Parser()
        self.headers = {}

        self.DecompressionActions = {
            "not-sent": self.da_not_sent,
            "value-sent": self.da_value_sent,
            "mapping-sent": self.da_mapping_sent,
            "LSB": self.da_lsb,
            "compute-length": self.da_compute_length,
            "compute-checksum": self.da_compute_checksum
        }

    def da_not_sent(self, fid, fl, fp, tv, schc_packet = None):
        self.headers[fid] = tv
        return True

    def da_value_sent(self, fid, fl, fp, tv, schc_packet = None):
        aux = schc_packet
        aux.reverse()
        length_cociente = fl // 8
        length_resto = fl % 8
        value_hex = ''

        # len(data) < 8
        if length_cociente == 0:
            value = aux.pop()
            value_bf = struct.pack('>B', value)
            value_hex = value_hex + value_bf.hex()
            aux.reverse()
            temp = int(value_hex, 16)
            self.headers[fid] = temp
            return

        for i in range(0,length_cociente):
            value = aux.pop()
            value_bf = struct.pack('>B', value)
            value_hex = value_hex + value_bf.hex()

        if length_resto != 0:
            mask = 0xFF
            value = aux.pop()
            value_bf = struct.pack(">B", value)
            value_hex = value_hex + value_bf.hex()

        aux.reverse()
        temp = int(value_hex,16)
        self.headers[fid] = temp
        return

    def da_mapping_sent(self, fid, fl, fp, tv, schc_packet = None):
        pass

    def da_lsb(self, fid, fl, fp, tv, schc_packet = None):
        pass

    def da_compute_length(self, fid, fl, fp, tv, schc_packet = None):
        if fid == "IPv6.payloadLength":
            self.headers[fid] = len(schc_packet) + 2 + 2 + 2 + 2 # 2 bytes source port + 2 bytes dest port + 2 bytes checksum + 2 bytes length
        if fid == "UDP.length":
            self.headers[fid] = len(schc_packet) + 2 + 2 + 2 + 2
        return True

    def da_compute_checksum(self, fid, fl, fp, tv, schc_packet = None):
        if fid == "UDP.checksum":
            ipv6_source_address_up = self.headers["IPv6.prefixES"] << 64
            ipv6_source_address_down = self.headers["IPv6.iidES"]
            ipv6_source_address = hex(ipv6_source_address_up | ipv6_source_address_down)[2:]

            ipv6_destination_address_up = self.headers["IPv6.prefixLA"] << 64
            ipv6_destination_address_down = self.headers["IPv6.iidLA"]
            ipv6_destination_address = hex(ipv6_destination_address_up | ipv6_destination_address_down)[2:]

            ipv6_pseudo_header = SCHC_Decompressor.build_pseudo_header(ipv6_source_address, ipv6_destination_address, self.headers["IPv6.nextHeader"], self.headers["UDP.length"])
            buff = ''
            for i in schc_packet:
                buff = buff + struct.pack('>B',i).hex()
            udp_checksum = SCHC_Decompressor.checksum(ipv6_pseudo_header, self.headers["UDP.length"], self.headers["UDP.devPort"], self.headers["UDP.appPort"], buff)
            self.headers[fid] = udp_checksum

    def decompress(self, schc_packet, direction):
        # Get RuleID from SCHC Packet
        schc_packet_buff = list(schc_packet)
        rule_id = schc_packet_buff[0]

        # Get Rule object from RuleID
        rule = self.rule_manager.get_rule_from_id(rule_id)

        # The package is reconstructed using the identifier of the rule
        self.builder(schc_packet_buff, rule, direction)

        return

    def builder(self, schc_packet, rule, direction):
        rules_calc = []
        rule_id = schc_packet.pop(0)
        for r in rule['content']:
            fid = r[0]
            fl = r[1]
            fp = r[2]
            di = r[3]
            tv = r[4]
            cda = r[6]

            if cda == 'compute-length' or cda == 'compute-checksum':
                rules_calc.append(r)
                continue

            if (di is 'Bi') or (di is direction):
                self.DecompressionActions.get(cda)(fid, fl, fp, tv, schc_packet)

        for r in rules_calc:
            fid = r[0]
            fl = r[1]
            fp = r[2]
            di = r[3]
            tv = r[4]
            cda = r[6]

            if (di is 'Bi') or (di is direction):
                self.DecompressionActions.get(cda)(fid, fl, fp, tv, schc_packet)

    @staticmethod
    def checksum(pseudo_header, udp_length, udp_source_port, udp_destination_port, udp_data):
        if (len(udp_data)%4) == 3:
            udp_data = udp_data + '0'
        elif (len(udp_data)%4) == 2:
            udp_data = udp_data + '00'
        elif (len(udp_data)%4) == 1:
            udp_data = udp_data + '000'

        udp_data_sum = 0
        for i in range(0, int(len(udp_data) // 4) ):
            udp_data_sum = int(udp_data[i * 4:i * 4 + 4], 16) + udp_data_sum

        sum_udp = udp_source_port + udp_destination_port + udp_length + udp_data_sum
        sum_total = pseudo_header + sum_udp
        sum_sup = sum_total & 0xFFFF0000
        sum_inf = sum_total & 0x0000FFFF
        sum_final = (sum_sup >> 16) + sum_inf
        result = sum_final ^ int('FFFF', 16)
        return struct.pack('>H', result)

    @staticmethod
    def build_pseudo_header(src_ip, dest_ip, next_header, payload_len):
        sum_ipv6_sa = 0
        for i in range(0,int(len(src_ip)//4)):
            sum_ipv6_sa = int(src_ip[i*4:i*4+4],16) + sum_ipv6_sa

        sum_ipv6_da = 0
        for i in range(0,int(len(dest_ip)//4)):
            sum_ipv6_da = int(dest_ip[i*4:i*4+4],16) + sum_ipv6_da

        sum_phdr = sum_ipv6_sa + sum_ipv6_da + next_header + payload_len
        return sum_phdr