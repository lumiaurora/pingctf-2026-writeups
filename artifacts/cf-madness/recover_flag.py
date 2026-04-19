#!/usr/bin/env python3

import struct
import sys
from pathlib import Path

DEADBEEF = 0xDEADBEEF
TABLE_VADDR = 0x419460
DATA_VADDR = 0x419020
DATA_OFFSET = 0x18020
TABLE_OFFSET = DATA_OFFSET + (TABLE_VADDR - DATA_VADDR)


def load_table(binary_path: Path) -> list[int]:
    data = binary_path.read_bytes()
    raw = data[TABLE_OFFSET : TABLE_OFFSET + 128 * 4]
    if len(raw) != 128 * 4:
        raise ValueError("failed to read the expected-value table from the ELF")
    return list(struct.unpack("<128I", raw))


def decode_flag(table: list[int]) -> str:
    length = ((table[0] - DEADBEEF) // 726) - 1

    for i in range(length):
        expected = (DEADBEEF + 726 * (length + 1 - i)) & 0xFFFFFFFF
        if table[2 * i] != expected:
            raise ValueError(f"unexpected even table entry at index {2 * i}")

    out = []

    for i in range(length):
        word = table[2 * i + 1]
        state = 0x539 if i == 0 else i - 1
        ch = (word ^ DEADBEEF ^ ((i * 0x1337) & 0xFFFFFFFF) ^ ((state * 0xABCD) & 0xFFFFFFFF)) & 0xFFFFFFFF
        if ch >= 0x80:
            raise ValueError(f"decoded non-ASCII value 0x{ch:x} at position {i}")
        out.append(chr(ch))

    return "".join(out)


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} /path/to/chall", file=sys.stderr)
        return 1

    binary_path = Path(sys.argv[1])
    table = load_table(binary_path)
    print(decode_flag(table))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
