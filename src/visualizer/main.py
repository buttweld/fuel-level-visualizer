import numpy as np
import serial
from .serial_protocol import SerialProtocol, PacketType

class FuelLevelVisualizer:
    def __init__(self,
                 com_port: str = None,
                 baud: int = 9600,
                 emulate: bool = False):

        url = com_port if not emulate else "loop://"
        self.emulate = emulate
        self.port = serial.serial_for_url(url, baudrate=baud, timeout=1)
        self.protocol = SerialProtocol()

        self.protocol.build_packet(packet_type=PacketType.QUERY, n_samples=60)
        print(f"Query Packet: {self.protocol.packet.byte_array.hex(" ").upper()}")

    def visualize(self, duration: int) -> None:
        # query
        self.protocol.build_packet(packet_type=PacketType.QUERY, n_samples=duration)
        self.port.write(self.protocol.packet.byte_array)
        # read
        if self.emulate:
            # emulate the response
            response = self.protocol.emulate_response()
        else:
            response=self.port.read()
        # parse
        self.protocol.parse_packet(bytearray(response))
        # visualize
        print(f"Fuel Levels: {self.protocol.data.samples}")


def main():
    f = FuelLevelVisualizer(com_port="COM3", baud=115200, emulate=True)
    f.visualize(20)

if __name__ == "__main__":
    main()