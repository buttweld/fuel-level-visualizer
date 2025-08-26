from enum import Enum
import numpy as np
import struct
import crcmod

class PacketType(Enum):
    QUERY = 0
    RESPONSE = 1

class Command(Enum):
    HEADER = 0xAA55
    QUERY = 0x1111
    RESPONSE = 0x2222

class Packet:
    length: int
    byte_array: bytearray

class Data:
    type: PacketType
    n_samples: int
    samples: np.ndarray

class SerialProtocol:
    def __init__(self,
                 use_emulator: bool = False,):
        # CRC-CCITT-FALSE: poly=0x1021, init=0xFFFF, xorOut=0x0000
        self.crc_ccitt = crcmod.mkCrcFun(0x11021, initCrc=0xFFFF, xorOut=0x0000, rev=False)

        self.packet: Packet = Packet()
        self.data: Data = Data()

    def build_packet(self,
                     packet_type: PacketType,
                     n_samples: int=None,
                     samples=None) -> Packet:

        # QUERY: HEADER + COMMAND.QUERY + LENGTH + N_SAMPLES + CRC
        if packet_type == PacketType.QUERY:
            self.packet.length = 2
            self.packet.byte_array = bytearray(struct.pack(">H", Command.HEADER.value)
                                               + struct.pack(">H", Command.QUERY.value)
                                               + struct.pack(">H", self.packet.length)
                                               + struct.pack(">H", n_samples))
            crc = self.crc_ccitt(self.packet.byte_array)
            self.packet.byte_array.extend(struct.pack(">H", crc))

        # RESPONSE: HEADER + COMMAND.RESPONSE + LENGTH + DATA ARRAY + CRC
        elif packet_type == PacketType.RESPONSE:
            self.packet.length = len(samples) * 4   # 2 bytes time stamp + 2 bytes fuel level data
            self.packet.byte_array = bytearray(struct.pack(">H", Command.HEADER.value)
                                               + struct.pack(">H", Command.RESPONSE.value)
                                               + struct.pack(">H", self.packet.length))
            for sample in samples:
                self.packet.byte_array.extend(struct.pack(">HH", sample["TimeStamp"], sample["FuelLevel"]))

            crc = self.crc_ccitt(self.packet.byte_array)
            self.packet.byte_array.extend(struct.pack(">H", crc))

        return self.packet

    def parse_packet(self, data_bytes: bytearray) -> Data:
        # Split data and CRC
        payload = data_bytes[:-2]
        crc_recv = struct.unpack(">H", data_bytes[-2:])[0]

        # Validate CRC
        crc_calc = self.crc_ccitt(payload)
        if crc_recv != crc_calc:
            raise ValueError(f"CRC mismatch: got {crc_recv:04x}, expected {crc_calc:04x}")

        # Parse header, command, length
        header, command, length = struct.unpack(">HHH", payload[0:6])
        if header != Command.HEADER.value:
            raise ValueError(f"Invalid header: {header:04x}")

        self.packet = Packet()
        self.packet.length = length

        if command == Command.QUERY.value:
            n_samples, = struct.unpack(">H", payload[6:8])
            self.data.type = PacketType.QUERY
            self.data.n_samples = n_samples

        elif command == Command.RESPONSE.value:
            self.data.type = PacketType.RESPONSE
            self.data.n_samples = length // 4

            samples_section = payload[6:6 + length]
            dtype = [("TimeStamp", ">u2"), ("FuelLevel", ">u2")]
            self.data.samples = np.frombuffer(samples_section, dtype=dtype)

        return self.data

    def emulate_response(self) -> bytearray:
        # query data
        self.parse_packet(self.packet.byte_array)
        n_samples = self.data.n_samples
        random_samples = self._generate_random_samples(n_samples)
        packet = self.build_packet(packet_type=PacketType.RESPONSE, samples=random_samples)
        print(f"Response Packet: {packet.byte_array.hex(" ").upper()}")
        return packet.byte_array

    @staticmethod
    def _generate_random_samples(n_samples: int) -> np.ndarray:
        start_time_stamp = np.random.randint(0, 3600 - n_samples)
        dtype = [("TimeStamp", ">u2"), ("FuelLevel", ">u2")]
        samples = np.zeros(n_samples, dtype=dtype)
        samples["TimeStamp"] = np.arange(start_time_stamp, start_time_stamp + n_samples, dtype=np.uint16)
        samples["FuelLevel"] = np.random.randint(0, 2**15, size=n_samples, dtype=np.uint16)
        return samples

