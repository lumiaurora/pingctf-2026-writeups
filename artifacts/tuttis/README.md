# Tuttis Artifacts

These are the files used for the `tuttis` writeup.

- `solve.py`: full remote solver/exploit script
- `shellcode.S`: RISC-V shellcode source assembled by the solver

The solver expects `llvm-mc` and `llvm-objcopy` to be available in `PATH` so it can assemble `shellcode.S` into a raw payload before connecting to the challenge service.
