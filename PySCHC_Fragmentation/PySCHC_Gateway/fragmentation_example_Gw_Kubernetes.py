import base64
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

import requests

from SCHC_FR.SCHC_Fragmenter_Gw import SCHC_Fragmenter_Gw


class S(BaseHTTPRequestHandler):
    fragmenter = None

    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        #logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        logging.debug("Receiving GET method")
        self._set_response()
        self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):
        logging.debug("Receiving POST method")
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        #logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n", str(self.path), str(self.headers), post_data.decode('utf-8'))

        if len(post_data) != 0:
            body_decoded = post_data.decode('utf-8')
            body_dic = json.loads(body_decoded)

            logging.debug("downlink_url: %s", str(body_dic["downlink_url"]))
            buffer = base64.b64decode(body_dic["payload_raw"])
            logging.info("Buffer: %s", buffer)

            if len(buffer) == 0:
                logging.error("Len(buffer) is 0")
            else:
                self.fragmenter.process_request(buffer, body_dic["downlink_url"], body_dic["dev_id"], body_dic["port"])
                #self.fragmenter.process_request(buffer, body_dic["downlink_url"], body_dic["dev_id"], 2)

        self._set_response()
        # self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

    def log_message(self, format, *args):
        return


def run(server_class, handler_class, port, myfragmenter):
    logging.basicConfig(level=logging.DEBUG)
    server_address = ('', port)
    handler_class.fragmenter = myfragmenter
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')


def send_rx_side(msg, downlink_url):
    logging.debug("Calling LPWAN send function RX side")
    r = requests.post(downlink_url + '', data=json.dumps(msg), headers = {'content-type': 'application/json'})
    logging.debug(r.status_code)
    return



def recv_rx_side():
    print("Calling LPWAN recv function RX side")


def callback_rx_side():
    print("Calling callback function RX side")


if __name__ == '__main__':
    formato = "%(levelname)s:%(asctime)s: %(thread)d %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(format=formato, level=logging.INFO, datefmt="%H:%M:%S")

    logging.info("Starting fragmenter....")
    fragmenter = SCHC_Fragmenter_Gw(SCHC_Fragmenter_Gw.LoRaWAN)
    fragmenter.set_callback(callback_rx_side)
    fragmenter.set_lpwan_send_function(send_rx_side)
    fragmenter.set_lpwan_recv_function(recv_rx_side)
    fragmenter.initialize()
    run(HTTPServer, S, 8080, fragmenter)
