from decimal import Decimal, getcontext
import string


getcontext().prec = 120

BASE = Decimal("73.21")
CHUNK_TARGETS = [
    Decimal("46741716782375706.8396419575653316"),
    Decimal("46291277424349185.5548286712719316"),
    Decimal("42149201139278358.4223548171552311"),
    Decimal("64147886106222656.2384332732886897"),
]
CHARS = "_" + string.digits + string.ascii_lowercase + "{}"
POWERS = [BASE**i for i in range(1, 9)]
DIGITS = sorted((ord(ch) - 48, ch) for ch in CHARS)
MIN_DIGIT = min(digit for digit, _ in DIGITS)
MAX_DIGIT = max(digit for digit, _ in DIGITS)


def bounds(length: int) -> tuple[Decimal, Decimal]:
    low = sum(Decimal(MIN_DIGIT) * POWERS[i] for i in range(length))
    high = sum(Decimal(MAX_DIGIT) * POWERS[i] for i in range(length))
    return low, high


def solve_chunk(target: Decimal, fixed: dict[int, str] | None = None) -> str:
    fixed = fixed or {}
    out: list[str] = []

    def rec(pos: int, rem: Decimal, acc: list[str]) -> bool:
        if pos == 0:
            if abs(rem) < Decimal("1e-25"):
                out.append("".join(acc))
                return True
            return False

        rem_min, rem_max = bounds(pos - 1)
        if pos in fixed:
            ordered = [(ord(fixed[pos]) - 48, fixed[pos])]
        else:
            estimate = float(rem / POWERS[pos - 1])
            ordered = sorted(DIGITS, key=lambda item: abs(item[0] - estimate))

        for digit, ch in ordered:
            new_rem = rem - Decimal(digit) * POWERS[pos - 1]
            if rem_min - Decimal("1e-25") <= new_rem <= rem_max + Decimal("1e-25"):
                if rec(pos - 1, new_rem, [ch] + acc):
                    return True

        return False

    if not rec(8, target, []):
        raise ValueError(f"no solution for {target}")

    return out[0]


chunks = [
    solve_chunk(CHUNK_TARGETS[0], {1: "p", 2: "i", 3: "n", 4: "g", 5: "{"}),
    solve_chunk(CHUNK_TARGETS[1]),
    solve_chunk(CHUNK_TARGETS[2]),
    solve_chunk(CHUNK_TARGETS[3], {8: "}"}),
]

print("".join(chunks))
