import binascii

from Node.PacketGenerator import PacketGenerator
from Gateway.SCHC_CD.SCHC_Compressor import SCHC_Compressor
from Gateway.SCHC_CD.SCHC_Decompressor import SCHC_Decompressor
from Gateway.SCHC_CD.SCHC_RuleManager import SCHC_RuleManager

"""Ahora comienza el codigo para descomprimir. Esto debe estar en el Device Side"""

package = PacketGenerator.generate()
#                           fID                  Pos  DI  TV                  MO           CDA
rule_64 = {"ruleid": 63,
          "devid": None,
          "content": [["IPv6.version", 4, 1, "Bi", 6, "equal", "not-sent"],
                      ["IPv6.trafficClass", 8, 1, "Bi", 0x95, "equal", "not-sent"],
                      ["IPv6.flowLabel", 20, 1, "Bi", 0xFDFD3, "equal", "not-sent"],
                      ["IPv6.payloadLength", 16, 1, "Bi", None, "ignore", "compute-length"],
                      ["IPv6.nextHeader", 8, 1, "Bi", 17, "equal", "not-sent"],
                      ["IPv6.hopLimit", 8, 1, "Up", 64, "equal", "not-sent"],
                      ["IPv6.prefixES", 64, 1, "Bi", 0xfc0c000000000000, "equal", "not-sent"],
                      ["IPv6.iidES", 64, 1, "Bi", 0x0000000000000094, "equal", "not-sent"],
                      ["IPv6.prefixLA", 64, 1, "Bi", 0xfc0c000000000000, "equal", "not-sent"],
                      ["IPv6.iidLA", 64, 1, "Bi", 0x0000000000000008, "equal", "not-sent"],
                      ["UDP.devPort", 16, 1, "Bi", 32513, "equal", "not-sent"],
                      ["UDP.appPort", 16, 1, "Bi", 32640, "equal", "not-sent"],
                      ["UDP.length", 16, 1, "Bi", None, "ignore", "compute-length"],
                      ["UDP.checksum", 16, 1, "Bi", None, "ignore", "compute-checksum"]
                      ]}

rule_32 = {"ruleid": 31,
          "devid": None,
          "content": [["IPv6.version", 4, 1, "Bi", 6, "equal", "not-sent"],
                      ["IPv6.trafficClass", 8, 1, "Bi", None, "ignore", "value-sent"],
                      ["IPv6.flowLabel", 20, 1, "Bi", 0xFDFD3, "equal", "not-sent"],
                      ["IPv6.payloadLength", 16, 1, "Bi", None, "ignore", "compute-length"],
                      ["IPv6.nextHeader", 8, 1, "Bi", 17, "equal", "not-sent"],
                      ["IPv6.hopLimit", 8, 1, "Up", 64, "equal", "not-sent"],
                      ["IPv6.prefixES", 64, 1, "Bi", 0xfc0c000000000000, "equal", "not-sent"],
                      ["IPv6.iidES", 64, 1, "Bi", 0x0000000000000094, "equal", "not-sent"],
                      ["IPv6.prefixLA", 64, 1, "Bi", 0xfc0c000000000000, "equal", "not-sent"],
                      ["IPv6.iidLA", 64, 1, "Bi", 0x0000000000000008, "equal", "not-sent"],
                      ["UDP.devPort", 16, 1, "Bi", 32513, "equal", "not-sent"],
                      ["UDP.appPort", 16, 1, "Bi", 32640, "equal", "not-sent"],
                      ["UDP.length", 16, 1, "Bi", None, "ignore", "compute-length"],
                      ["UDP.checksum", 16, 1, "Bi", None, "ignore", "compute-checksum"]
                      ]}

rule_62 = {"ruleid": 61,
          "devid": None,
          "content": [["IPv6.version", 4, 1, "Bi", 6, "equal", "not-sent"],
                      ["IPv6.trafficClass", 8, 1, "Bi", 0x95, "equal", "not-sent"],
                      ["IPv6.flowLabel", 20, 1, "Bi", 0xFDFD3, "equal", "not-sent"],
                      ["IPv6.payloadLength", 16, 1, "Bi", None, "ignore", "compute-length"],
                      ["IPv6.nextHeader", 8, 1, "Bi", 17, "equal", "not-sent"],
                      ["IPv6.hopLimit", 8, 1, "Up", 64, "equal", "not-sent"],
                      ["IPv6.prefixES", 64, 1, "Bi", 0xfc0c000000000000, "equal", "not-sent"],
                      ["IPv6.iidES", 64, 1, "Bi", 0x0000000000000094, "equal", "not-sent"],
                      ["IPv6.prefixLA", 64, 1, "Bi", 0xfc0c000000000000, "equal", "not-sent"],
                      ["IPv6.iidLA", 64, 1, "Bi", 0x0000000000000008, "equal", "not-sent"],
                      ["UDP.devPort", 16, 1, "Bi", None, "ignore", "value-sent"],
                      ["UDP.appPort", 16, 1, "Bi", 32640, "equal", "not-sent"],
                      ["UDP.length", 16, 1, "Bi", None, "ignore", "compute-length"],
                      ["UDP.checksum", 16, 1, "Bi", None, "ignore", "compute-checksum"]
                      ]}

rule_63 = {"ruleid": 62,
          "devid": None,
          "content": [["IPv6.version", 4, 1, "Bi", 6, "equal", "not-sent"],
                      ["IPv6.trafficClass", 8, 1, "Bi", 0x95, "equal", "not-sent"],
                      ["IPv6.flowLabel", 20, 1, "Bi", 0xFDFD3, "equal", "not-sent"],
                      ["IPv6.payloadLength", 16, 1, "Bi", None, "ignore", "compute-length"],
                      ["IPv6.nextHeader", 8, 1, "Bi", 17, "equal", "not-sent"],
                      ["IPv6.hopLimit", 8, 1, "Up", 64, "equal", "not-sent"],
                      ["IPv6.prefixES", 64, 1, "Bi", 0xfc0c000000000000, "equal", "not-sent"],
                      ["IPv6.iidES", 64, 1, "Bi", 0x0000000000000094, "equal", "not-sent"],
                      ["IPv6.prefixLA", 64, 1, "Bi", 0xfc0c000000000000, "equal", "not-sent"],
                      ["IPv6.iidLA", 64, 1, "Bi", 0x0000000000000008, "equal", "not-sent"],
                      ["UDP.devPort", 16, 1, "Bi", 32513, "equal", "not-sent"],
                      ["UDP.appPort", 16, 1, "Bi", None, "ignore", "value-sent"],
                      ["UDP.length", 16, 1, "Bi", None, "ignore", "compute-length"],
                      ["UDP.checksum", 16, 1, "Bi", None, "ignore", "compute-checksum"]
                      ]}

rule_30 = {"ruleid": 29,
          "devid": None,
          "content": [["IPv6.version", 4, 1, "Bi", 6, "equal", "not-sent"],
                      ["IPv6.trafficClass", 8, 1, "Bi", None, "ignore", "value-sent"],
                      ["IPv6.flowLabel", 20, 1, "Bi", 0xFDFD3, "equal", "not-sent"],
                      ["IPv6.payloadLength", 16, 1, "Bi", None, "ignore", "compute-length"],
                      ["IPv6.nextHeader", 8, 1, "Bi", 17, "equal", "not-sent"],
                      ["IPv6.hopLimit", 8, 1, "Up", 64, "equal", "not-sent"],
                      ["IPv6.prefixES", 64, 1, "Bi", 0xfc0c000000000000, "equal", "not-sent"],
                      ["IPv6.iidES", 64, 1, "Bi", 0x0000000000000094, "equal", "not-sent"],
                      ["IPv6.prefixLA", 64, 1, "Bi", 0xfc0c000000000000, "equal", "not-sent"],
                      ["IPv6.iidLA", 64, 1, "Bi", 0x0000000000000008, "equal", "not-sent"],
                      ["UDP.devPort", 16, 1, "Bi", None, "ignore", "value-sent"],
                      ["UDP.appPort", 16, 1, "Bi", 32640, "equal", "not-sent"],
                      ["UDP.length", 16, 1, "Bi", None, "ignore", "compute-length"],
                      ["UDP.checksum", 16, 1, "Bi", None, "ignore", "compute-checksum"]
                      ]}

rule_31 = {"ruleid": 30,
          "devid": None,
          "content": [["IPv6.version", 4, 1, "Bi", 6, "equal", "not-sent"],
                      ["IPv6.trafficClass", 8, 1, "Bi", None, "ignore", "value-sent"],
                      ["IPv6.flowLabel", 20, 1, "Bi", 0xFDFD3, "equal", "not-sent"],
                      ["IPv6.payloadLength", 16, 1, "Bi", None, "ignore", "compute-length"],
                      ["IPv6.nextHeader", 8, 1, "Bi", 17, "equal", "not-sent"],
                      ["IPv6.hopLimit", 8, 1, "Up", 64, "equal", "not-sent"],
                      ["IPv6.prefixES", 64, 1, "Bi", 0xfc0c000000000000, "equal", "not-sent"],
                      ["IPv6.iidES", 64, 1, "Bi", 0x0000000000000094, "equal", "not-sent"],
                      ["IPv6.prefixLA", 64, 1, "Bi", 0xfc0c000000000000, "equal", "not-sent"],
                      ["IPv6.iidLA", 64, 1, "Bi", 0x0000000000000008, "equal", "not-sent"],
                      ["UDP.devPort", 16, 1, "Bi", 32513, "equal", "not-sent"],
                      ["UDP.appPort", 16, 1, "Bi", None, "ignore", "value-sent"],
                      ["UDP.length", 16, 1, "Bi", None, "ignore", "compute-length"],
                      ["UDP.checksum", 16, 1, "Bi", None, "ignore", "compute-checksum"]
                      ]}

rule_48 = {"ruleid": 47,
          "devid": None,
          "content": [["IPv6.version", 4, 1, "Bi", 6, "equal", "not-sent"],
                      ["IPv6.trafficClass", 8, 1, "Bi", 0x95, "equal", "not-sent"],
                      ["IPv6.flowLabel", 20, 1, "Bi", None, "ignore", "value-sent"],
                      ["IPv6.payloadLength", 16, 1, "Bi", None, "ignore", "compute-length"],
                      ["IPv6.nextHeader", 8, 1, "Bi", 17, "equal", "not-sent"],
                      ["IPv6.hopLimit", 8, 1, "Up", 64, "equal", "not-sent"],
                      ["IPv6.prefixES", 64, 1, "Bi", 0xfc0c000000000000, "equal", "not-sent"],
                      ["IPv6.iidES", 64, 1, "Bi", 0x0000000000000094, "equal", "not-sent"],
                      ["IPv6.prefixLA", 64, 1, "Bi", 0xfc0c000000000000, "equal", "not-sent"],
                      ["IPv6.iidLA", 64, 1, "Bi", 0x0000000000000008, "equal", "not-sent"],
                      ["UDP.devPort", 16, 1, "Bi", 32513, "equal", "not-sent"],
                      ["UDP.appPort", 16, 1, "Bi", 32640, "equal", "not-sent"],
                      ["UDP.length", 16, 1, "Bi", None, "ignore", "compute-length"],
                      ["UDP.checksum", 16, 1, "Bi", None, "ignore", "compute-checksum"]
                      ]}

rule_16 = {"ruleid": 15,
          "devid": None,
          "content": [["IPv6.version", 4, 1, "Bi", 6, "equal", "not-sent"],
                      ["IPv6.trafficClass", 8, 1, "Bi", None, "ignore", "value-sent"],
                      ["IPv6.flowLabel", 20, 1, "Bi", None, "ignore", "value-sent"],
                      ["IPv6.payloadLength", 16, 1, "Bi", None, "ignore", "compute-length"],
                      ["IPv6.nextHeader", 8, 1, "Bi", 17, "equal", "not-sent"],
                      ["IPv6.hopLimit", 8, 1, "Up", 64, "equal", "not-sent"],
                      ["IPv6.prefixES", 64, 1, "Bi", 0xfc0c000000000000, "equal", "not-sent"],
                      ["IPv6.iidES", 64, 1, "Bi", 0x0000000000000094, "equal", "not-sent"],
                      ["IPv6.prefixLA", 64, 1, "Bi", 0xfc0c000000000000, "equal", "not-sent"],
                      ["IPv6.iidLA", 64, 1, "Bi", 0x0000000000000008, "equal", "not-sent"],
                      ["UDP.devPort", 16, 1, "Bi", 32513, "equal", "not-sent"],
                      ["UDP.appPort", 16, 1, "Bi", 32640, "equal", "not-sent"],
                      ["UDP.length", 16, 1, "Bi", None, "ignore", "compute-length"],
                      ["UDP.checksum", 16, 1, "Bi", None, "ignore", "compute-checksum"]
                      ]}


rm_device = SCHC_RuleManager()
rm_device.add_rule(rule_63)
rm_device.add_rule(rule_48)


compressor = SCHC_Compressor(rm_device)
headers_compressed = compressor.compress(package,"Up")
udp_payload = package[1]
schc_packet = b''.join([headers_compressed, udp_payload])

print('SCHC Packet: ' + str(binascii.hexlify(schc_packet)))
print('Lenght SCHC Packet: ' + str(len(schc_packet)))
print("Largo Paquete sin comprimir: " + str(len(package[2])) + " bytes")
print("Largo Paquete comprimido: " + str(len(headers_compressed)-1) + " bytes")
hc_len = len(headers_compressed)-1
pkg_len = len(package[2])
temp = (pkg_len - hc_len) * 100 / pkg_len
print('Porcentaje de compresion: %.2f%%' % temp)





"""Ahora comienza el codigo para descomprimir. Esto debe estar en el Network Side"""
rm_network = SCHC_RuleManager()
rm_network.add_rule(rule_64)
rm_network.add_rule(rule_32)
rm_network.add_rule(rule_62)
rm_network.add_rule(rule_63)
rm_network.add_rule(rule_30)
rm_network.add_rule(rule_31)
rm_network.add_rule(rule_48)
rm_network.add_rule(rule_16)


decompressor = SCHC_Decompressor(rm_network)
decompressor.decompress(schc_packet, "Up")