import os
import socket

from Node.SCHC_FR.SCHC_Fragmenter_Node import SCHC_Fragmenter_Node


# *********************** Transmission Code ********************************

host_ex = "127.0.0.1"
port_ex = 6667
sock_ex = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("Socket Created")
sock_ex.bind((host_ex, port_ex))
print("socket bind complete")
sock_ex.listen(1)
print("socket now listening")


def send_tx_side(msg):
    print("Calling LPWAN send function TX side")
    host = "127.0.0.1"
    port = 6666
    sockTx = socket.socket()
    sockTx.connect((host, port))
    sockTx.send(msg)
    sockTx.close()


def recv_tx_side():
    print("Calling LPWAN recv function TX side")
    conn, addr = sock_ex.accept()
    data = conn.recv(1024)
    return data


def callback_tx_side():
    print("Calling callback function TX side")


schc_packet = os.urandom(550)  # in bytes

fragmenter = SCHC_Fragmenter_Node(SCHC_Fragmenter_Node.LoRaWAN)
fragmenter.set_callback(callback_tx_side)
fragmenter.set_lpwan_send_function(send_tx_side)
fragmenter.set_lpwan_recv_function(recv_tx_side)
fragmenter.initialize()
fragmenter.send(schc_packet)
fragmenter.reception_loop()
