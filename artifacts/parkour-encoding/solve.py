#!/usr/bin/env python3
"""Solve the pingCTF 2026 'parkour encoding' challenge.

This script reads a Java Edition world save directly from disk, samples the
parkour route on y=0, z=0, interprets diamond blocks as 1 and air as 0, and
decodes the resulting bitstream as ASCII.
"""

from __future__ import annotations

import argparse
import gzip
import math
import struct
import zlib
from io import BytesIO
from pathlib import Path

MASK64 = (1 << 64) - 1


class NBTParser:
    def __init__(self, data: bytes):
        self.buffer = BytesIO(data)

    def read(self, size: int) -> bytes:
        data = self.buffer.read(size)
        if len(data) != size:
            raise EOFError("unexpected end of NBT data")
        return data

    def byte(self) -> int:
        return self.read(1)[0]

    def short(self) -> int:
        return struct.unpack(">h", self.read(2))[0]

    def int(self) -> int:
        return struct.unpack(">i", self.read(4))[0]

    def long(self) -> int:
        return struct.unpack(">q", self.read(8))[0]

    def float(self) -> float:
        return struct.unpack(">f", self.read(4))[0]

    def double(self) -> float:
        return struct.unpack(">d", self.read(8))[0]

    def string(self) -> str:
        return self.read(self.short()).decode("utf-8", "replace")

    def payload(self, tag_type: int):
        if tag_type == 0:
            return None
        if tag_type == 1:
            return struct.unpack(">b", self.read(1))[0]
        if tag_type == 2:
            return self.short()
        if tag_type == 3:
            return self.int()
        if tag_type == 4:
            return self.long()
        if tag_type == 5:
            return self.float()
        if tag_type == 6:
            return self.double()
        if tag_type == 7:
            return self.read(self.int())
        if tag_type == 8:
            return self.string()
        if tag_type == 9:
            subtype = self.byte()
            length = self.int()
            return [self.payload(subtype) for _ in range(length)]
        if tag_type == 10:
            result = {}
            while True:
                subtype = self.byte()
                if subtype == 0:
                    return result
                name = self.string()
                result[name] = self.payload(subtype)
        if tag_type == 11:
            return [self.int() for _ in range(self.int())]
        if tag_type == 12:
            return [self.long() for _ in range(self.int())]
        raise ValueError(f"unsupported NBT tag: {tag_type}")

    def parse(self):
        root_type = self.byte()
        _root_name = self.string()
        return self.payload(root_type)


class World:
    def __init__(self, world_path: Path):
        self.region_dir = world_path / "region"
        self.chunk_cache = {}

    def _read_chunk(self, chunk_x: int, chunk_z: int):
        key = (chunk_x, chunk_z)
        if key in self.chunk_cache:
            return self.chunk_cache[key]

        region_x = chunk_x >> 5
        region_z = chunk_z >> 5
        local_x = chunk_x & 31
        local_z = chunk_z & 31
        region_path = self.region_dir / f"r.{region_x}.{region_z}.mca"
        if not region_path.exists():
            self.chunk_cache[key] = None
            return None

        region_data = region_path.read_bytes()
        header_index = local_x + (local_z * 32)
        entry = region_data[header_index * 4:(header_index + 1) * 4]
        offset = int.from_bytes(entry[:3], "big")
        sector_count = entry[3]
        if offset == 0 or sector_count == 0:
            self.chunk_cache[key] = None
            return None

        chunk_start = offset * 4096
        chunk_length = int.from_bytes(region_data[chunk_start:chunk_start + 4], "big")
        compression_type = region_data[chunk_start + 4]
        payload = region_data[chunk_start + 5:chunk_start + 4 + chunk_length]

        if compression_type == 1:
            raw_chunk = gzip.decompress(payload)
        elif compression_type == 2:
            raw_chunk = zlib.decompress(payload)
        elif compression_type == 3:
            raw_chunk = payload
        else:
            raise ValueError(f"unknown chunk compression type: {compression_type}")

        chunk = NBTParser(raw_chunk).parse()
        sections = {}
        for section in chunk.get("sections", []):
            block_states = section.get("block_states")
            if not block_states:
                continue
            palette = block_states["palette"]
            packed = [value & MASK64 for value in block_states.get("data", [])]
            sections[int(section["Y"])] = (palette, packed)

        self.chunk_cache[key] = sections
        return sections

    def get_block(self, x: int, y: int, z: int) -> str:
        chunk_x = x >> 4
        chunk_z = z >> 4
        sections = self._read_chunk(chunk_x, chunk_z)
        if sections is None:
            return "minecraft:void_air"

        section_y = y >> 4
        if section_y not in sections:
            return "minecraft:air"

        palette, packed = sections[section_y]
        if len(palette) == 1:
            return palette[0]["Name"]

        bits_per_block = max(4, math.ceil(math.log2(len(palette))))
        mask = (1 << bits_per_block) - 1
        block_index = ((y & 15) << 8) | ((z & 15) << 4) | (x & 15)
        bit_index = block_index * bits_per_block
        long_index = bit_index // 64
        start_offset = bit_index % 64

        value = (packed[long_index] >> start_offset) & mask
        end_offset = start_offset + bits_per_block
        if end_offset > 64:
            spill_bits = end_offset - 64
            value |= (packed[long_index + 1] & ((1 << spill_bits) - 1)) << (64 - start_offset)

        return palette[value]["Name"]


def extract_bits(world: World, length: int, y: int, z: int) -> str:
    return "".join(
        "1" if world.get_block(x, y, z) == "minecraft:diamond_block" else "0"
        for x in range(length)
    )


def decode_ascii(bits: str) -> str:
    if len(bits) % 8 != 0:
        raise ValueError("bitstream length must be divisible by 8")
    return "".join(chr(int(bits[index:index + 8], 2)) for index in range(0, len(bits), 8))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("world", nargs="?", default="parkour encoding", help="path to the extracted world save")
    parser.add_argument("--length", type=int, default=432, help="number of x positions to sample")
    parser.add_argument("--y", type=int, default=0, help="y coordinate of the route")
    parser.add_argument("--z", type=int, default=0, help="z coordinate of the route")
    parser.add_argument("--dump-bits", action="store_true", help="print the grouped bitstream before the flag")
    args = parser.parse_args()

    world = World(Path(args.world))
    bits = extract_bits(world, args.length, args.y, args.z)

    if args.dump_bits:
        print(" ".join(bits[index:index + 8] for index in range(0, len(bits), 8)))

    print(decode_ascii(bits))


if __name__ == "__main__":
    main()
