class SCHC_Parser:

    def __init__(self):
        self.header_fields = {}
        self.udp_data = []

    def parser(self, buffer):
        data_buffer = list(buffer)

        # Mask definition
        mask_high = int('F0', 16)
        mask_low = int('0F', 16)

        # validating if it is an ipv6 package
        if (data_buffer[0] >> 4) == 6:
            self.header_fields["IPv6.version", 1] = [data_buffer[0] >> 4, "fixed"]
            self.header_fields["IPv6.trafficClass", 1] = [(data_buffer[0] << 4) & mask_high | (data_buffer[1] >> 4) & mask_low, "fixed"]
            self.header_fields["IPv6.flowLabel", 1] = [(data_buffer[1] & mask_low) << 16 | data_buffer[2] << 8 | data_buffer[3], "fixed"]
            self.header_fields["IPv6.payloadLength", 1] = [data_buffer[4] << 8 | data_buffer[5], "fixed"]
            self.header_fields["IPv6.nextHeader", 1] = [data_buffer[6], "fixed"]
            self.header_fields["IPv6.hopLimit", 1] = [data_buffer[7], "fixed"]
            self.header_fields["IPv6.prefixES", 1] = [data_buffer[8] << 56 | data_buffer[9] << 48 | data_buffer[10] << 40 | data_buffer[11] << 32 | data_buffer[12] << 24 | data_buffer[13] << 16 | data_buffer[14] << 8 | data_buffer[15], "fixed"]
            self.header_fields["IPv6.iidES", 1] = [data_buffer[16] << 56 | data_buffer[17] << 48 | data_buffer[18] << 40 | data_buffer[19] << 32 | data_buffer[20] << 24 | data_buffer[21] << 16 | data_buffer[22] << 8 | data_buffer[23], "fixed"]
            self.header_fields["IPv6.prefixLA", 1] = [data_buffer[24] << 56 | data_buffer[25] << 48 | data_buffer[26] << 40 | data_buffer[27] << 32 | data_buffer[28] << 24 | data_buffer[29] << 16 | data_buffer[30] << 8 | data_buffer[31], "fixed"]
            self.header_fields["IPv6.iidLA", 1] = [data_buffer[32] << 56 | data_buffer[33] << 48 | data_buffer[34] << 40 | data_buffer[35] << 32 | data_buffer[36] << 24 | data_buffer[37] << 16 | data_buffer[38] << 8 | data_buffer[39], "fixed"]

            if self.header_fields["IPv6.nextHeader", 1][0] == 17:
                self.header_fields["UDP.devPort", 1] = [data_buffer[40] << 8 | data_buffer[41], "fixed"]
                self.header_fields["UDP.appPort", 1] = [data_buffer[42] << 8 | data_buffer[43], "fixed"]
                self.header_fields["UDP.length", 1] = [data_buffer[44] << 8 | data_buffer[45], "fixed"]
                self.header_fields["UDP.checksum", 1] = [data_buffer[46] << 8 | data_buffer[47], "fixed"]
                self.udp_data = [data_buffer[48:len(data_buffer)], "variable"]

            else:
                print("Unsupported L4 protocol")
        else:
            print("The message is not an IPv6 package")
            return False

        return True
