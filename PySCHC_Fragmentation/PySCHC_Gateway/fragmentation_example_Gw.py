import socket

from SCHC_FR.SCHC_Fragmenter_Gw import SCHC_Fragmenter_Gw

# *********************** Reception Code ********************************

host = "127.0.0.1"
port = 6666
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# print("Socket Created")
sock.bind((host, port))
# print("socket bind complete")
sock.listen(1)
# print("socket now listening")



def send_rx_side(msg):
    # print("Calling LPWAN send function RX side")
    host = "127.0.0.1"
    port = 6667
    sockTx = socket.socket()
    sockTx.connect((host, port))
    sockTx.send(msg)
    # print("send_rx_side: " + str(binascii.hexlify(msg)))
    sockTx.close()

def recv_rx_side():
    # print("Calling LPWAN recv function RX side")
    conn, addr = sock.accept()
    data = conn.recv(1024)
    # print("******************************************** recv: ", data)
    # print("******************************************** length: ", len(data))
    return data


def callback_rx_side():
    print("Calling callback function RX side")
# *********************** Reception Code ********************************

fragmenter = SCHC_Fragmenter_Gw(SCHC_Fragmenter_Gw.LoRaWAN)
fragmenter.set_callback(callback_rx_side)
fragmenter.set_lpwan_send_function(send_rx_side)
fragmenter.set_lpwan_recv_function(recv_rx_side)
fragmenter.initialize()
fragmenter.reception_loop()







