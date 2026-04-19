from pathlib import Path
import re

import numpy as np


W = 64
H = 48
GENERATIONS = 0x537A

# Recovered from the dependency graph built by TheStrongDecideTheNatureOfSin.
OFFSETS = [
    (-2, -2),
    (-2, 0),
    (-2, 2),
    (0, -2),
    (0, 2),
    (2, -2),
    (2, 0),
    (2, 2),
]


def art_to_board(data: bytes) -> np.ndarray:
    return np.fromiter((1 if c != 0x20 else 0 for c in data), dtype=np.uint8).reshape(H, W)


def step(board: np.ndarray, rule: np.ndarray) -> np.ndarray:
    padded = np.pad(board, ((2, 2), (2, 2)))
    idx = np.zeros((H, W), dtype=np.uint16)

    for dx, dy in OFFSETS:
        idx = (idx << 1) | padded[2 + dy : H + 2 + dy, 2 + dx : W + 2 + dx].astype(np.uint16)

    idx |= board.astype(np.uint16) << 8
    return rule[idx]


def decode_initial_board(board: np.ndarray) -> bytes:
    out = bytearray()

    for block in range(H // 8):
        rows = board[block * 8 : (block + 1) * 8]
        for x in range(W):
            value = 0
            for bit in range(8):
                value |= int(rows[bit, x]) << bit
            out.append(value)

    return bytes(out)


def main() -> None:
    blob = Path("task").read_bytes()
    rule = np.fromiter((1 if c == ord("1") else 0 for c in blob[0x3100:0x3500:2]), dtype=np.uint8)

    previous = art_to_board(blob[0x3500:0x4100])
    current = art_to_board(blob[0x4100:0x4D00])

    for _ in range(GENERATIONS - 1):
        older = step(previous, rule) ^ current
        current, previous = previous, older

    candidate = decode_initial_board(previous).split(b"\x00", 1)[0]
    match = re.search(rb"ping_[ -~]{0,58}", candidate)
    if not match:
        raise SystemExit("flag not found")

    print(match.group().decode())


if __name__ == "__main__":
    main()
