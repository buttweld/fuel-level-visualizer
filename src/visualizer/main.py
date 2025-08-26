import os
from logging import exception

import serial
import argparse
import matplotlib.pyplot as plt
from .serial_protocol import SerialProtocol, PacketType

class FuelLevelVisualizer:
    def __init__(self,
                 port: str = None,
                 baud: int = 9600,
                 emulate: bool = False):

        url = port if not emulate else "loop://"
        self.emulate = emulate
        try:
            self.port = serial.serial_for_url(url, baudrate=baud, timeout=1)
        except Exception as e:
            print(f"Failed to open serial port '{url}': {e}")

        self.protocol = SerialProtocol()

        self.protocol.build_packet(packet_type=PacketType.QUERY, n_samples=60)
        print(f"Query Packet: {self.protocol.packet.byte_array.hex(" ").upper()}")

    def visualize(self, duration: int) -> None:
        # query
        self.protocol.build_packet(packet_type=PacketType.QUERY, n_samples=duration)
        self.port.write(self.protocol.packet.byte_array)
        # read
        if self.emulate:
            response = self.protocol.emulate_response()
        else:
            response=self.port.read()
        # parse
        self.protocol.parse_packet(bytearray(response))
        # console output
        print(f"Fuel Levels:\n{self.protocol.data.samples}")
        # visualize
        self._plot()
        # close port
        self.port.close()

    def _plot(self) -> None:
        # plot
        time_axis = self.protocol.data.samples["TimeStamp"]
        fuel_level = self._raw_to_percentage(self.protocol.data.samples["FuelLevel"])
        plt.plot(time_axis, fuel_level)
        plt.xlabel("Time [s]")
        plt.ylabel("Fuel Level [%]")
        plt.grid(True)
        plt.tight_layout()

        # save
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        output_dir = os.path.join(project_root, "output")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "output.png")
        plt.savefig(output_path, dpi=300)

        # show
        plt.show()

    @staticmethod
    def _raw_to_percentage(raw_value) -> float:
        return raw_value / 2**15 * 100.0


def get_arguments():
    parser = argparse.ArgumentParser(description="Fuel Level Visualizer")
    parser.add_argument("-p", "--port", default="COM1", help="Serial port name")
    parser.add_argument("-b", "--baud", type=int, default=115200, help="Baud rate")
    parser.add_argument("-e", "--emulate", action="store_true", help="Enable emulation mode")
    parser.add_argument("-n", "--n_samples", type=int, default=60, help="Number of samples to visualize")

    args = parser.parse_args()

    return args

def main():
    args = get_arguments()
    f = FuelLevelVisualizer(port=args.port,
                            baud=args.baud,
                            emulate=args.emulate)
    f.visualize(args.n_samples)

if __name__ == "__main__":
    main()