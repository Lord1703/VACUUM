import struct

def check_crc(frame):
    frame_length = len(frame)
    if frame_length < 8:
        return False
    return crc16(frame[0:(frame_length-2)]) == (frame[frame_length-1]<<8)+frame[frame_length-2]

def crc16(data):
    offset = 0
    length = len(data)
    if data is None or offset < 0 or offset > len(data) - 1 and offset+length > len(data):
        return 0
    crc = 0xFFFF
    for i in range(0, length):
        crc ^= data[offset + i]
        for j in range(0, 8):
            if (crc & 1) > 0:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc = crc >> 1
    return crc

def get_values_from_bytes(barray):
    values = []
    for idx in range(0, len(barray), 2):
        values.append((barray[idx]<<8) + barray[idx + 1])
    return values

def get_bytes_from_values(values):
    barray = bytearray([])
    for value in values:
        barray += bytearray([value>>8, value&0xFF])
    return barray

def pack_bitstring(bits):
    ret = b""
    i = packed = 0
    for bit in bits:
        if bit:
            packed += 128
        i += 1
        if i == 8:
            ret += struct.pack(">B", packed)
            i = packed = 0
        else:
            packed >>= 1
    if 0 < i < 8:
        packed >>= 7 - i
        ret += struct.pack(">B", packed)
    return ret

def unpack_bitstring(string):
    byte_count = len(string)
    bits = []
    for byte in range(byte_count):
        value = int(int(string[byte]))
        for _ in range(8):
            bits.append((value & 1) == 1)
            value >>= 1
    return bits

def encode_float(value):
    return bytearray(struct.pack("f", value))

def decode_to_float(values):
    if isinstance(values, list):
        return struct.unpack("f", bytearray(values))[0]
    return struct.unpack("f", values)[0]