from network import LoRa
import socket
import ubinascii
import struct
import network
from machine import Timer
import time


class LoRaWAN_Pycom:
    data_rate = None
    myLora = None
    fragmenter = None

    def __init__(self, dr):
        self.data_rate = dr
        self.chrono = Timer.Chrono()
        self.chrono.start()

    def get_spread_factor(self, data_rate):
        dic = {0:12, 1:11, 2:10, 3:9, 4:8, 5:7}
        return dic.get(data_rate)

    def set_fragmenter(self, frag):
        self.fragmenter = frag

    def lora_cb(self, lora):
        #print('Calling lora_cb()')
        events = lora.events()
        if events & LoRa.RX_PACKET_EVENT:
            #print('Lora packet received')
            pass
        if events & LoRa.TX_PACKET_EVENT:
            #print('Lora packet sent')
            pass

    def initialize_lorawan_link(self):
        #print(ubinascii.hexlify(network.LoRa().mac()))

        # Initialise LoRa in LORAWAN mode.
        # Please pick the region that matches where you are using the device:
        # Asia = LoRa.AS923
        # Australia = LoRa.AU915
        # Europe = LoRa.EU868
        # United States = LoRa.US915
        lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.AU915, adr=False)
        self.myLora = lora

        # create an ABP authentication params
        dev_addr = struct.unpack(">l", ubinascii.unhexlify('260211EE'))[0]
        nwk_swkey = ubinascii.unhexlify('AB189EFE29DCF9F9830F3A564DC1844E')
        app_swkey = ubinascii.unhexlify('A55931ACC412DE51171CEDA45BE6B319')

        #for channel in range(0, 72):
        #    lora.add_channel(channel, frequency=916800000, dr_min=0, dr_max=5)
        #lora.add_channel(0, frequency=923300000, dr_min=0, dr_max=5)

        for i in range(8, 72):
            lora.remove_channel(i)

        start = 916800000
        f_inc = 200000
        curr  = start

        for i in range(8):
            #print(curr)
            lora.add_channel(index=i, frequency=curr, dr_min=0, dr_max=5)
            curr += f_inc

        #lora.callback(trigger=(LoRa.RX_PACKET_EVENT | LoRa.TX_PACKET_EVENT), handler=self.lora_cb)

        # join a network using ABP (Activation By Personalization)
        lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey))

        #print(lora.has_joined())

        # wait until the module has joined the network
        while not lora.has_joined():
            time.sleep(2.5)
            print('Not yet joined...')

        #print("Has joined!!!!!")

        # create a LoRa socket
        s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

        # set the LoRaWAN data rate
        s.setsockopt(socket.SOL_LORA, socket.SO_DR, self.data_rate)
        s.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, False)

        return s

    def send_tx_side(self, s, msg, rule_id):
        #print("Calling send_tx_side")

        # set rule_id in port header
        s.bind(rule_id)

        # make the socket blocking
        # (waits for the data to be sent and for the 2 receive windows to expire)
        s.setblocking(True)

        # send some data
        # s.send(bytes([0x03, 0x02, 0x03]))
        print(msg)
        #chrono_var_1 = self.chrono.read_ms()
        #print("*******************: Antes del send(): " + str(chrono_var_1))
        s.send(msg)
        #(rx_timestamp, rssi, snr, sftx, sfrx, tx_trials, tx_power, tx_time_on_air, tx_counter, tx_frequency) = self.myLora.stats()
        #print("Time on Air: %f ms" %tx_time_on_air)
        #chrono_var_2 = self.chrono.read_ms()
        #print("*******************: Despues del send(): " + str(chrono_var_2))
        #print("*******************: Diferencia: " + str(chrono_var_2 - chrono_var_1))


        # make the socket non-blocking
        # (because if there's no data received it will block forever...)
        s.setblocking(False)

        # get any data received (if any...)
        #chrono_var_3 = self.chrono.read_ms()
        #print("*******************: Antes del recvfrom(): " + str(chrono_var_3))
        data, rule_id = s.recvfrom(64)
        #chrono_var_4 = self.chrono.read_ms()
        #print("*******************: Despues del recvfrom(): " + str(chrono_var_4))
        #print("*******************: Diferencia: " + str(chrono_var_4 - chrono_var_3))
        #data = s.recv(64)
        #rule_id = 20

        if len(data)>0:
            #print("************ llego data ************: " + str(data))
            self.fragmenter.reception_msg(data, rule_id)
        return

    def send_tx_side_without_recv(self, s, msg, rule_id):
        #print("Calling send_tx_side_without_recv")

        # set rule_id in port header
        s.bind(rule_id)

        # make the socket blocking
        # (waits for the data to be sent and for the 2 receive windows to expire)
        s.setblocking(True)

        # send some data
        # s.send(bytes([0x03, 0x02, 0x03]))
        s.send(msg)


        # make the socket non-blocking
        # (because if there's no data received it will block forever...)
        s.setblocking(False)

        return


    def recv_tx_side(self):
        print("Calling LPWAN recv function TX side")

    def get_data_rate(self):
        return self.data_rate
