from decimal import Decimal, getcontext


getcontext().prec = 120

BASE = Decimal("73.21")
EXPECTED_LEN = 32
CHUNK_SIZE = 8
TARGETS = [
    Decimal("46741716782375706.8396419575653316"),
    Decimal("46291277424349185.5548286712719316"),
    Decimal("42149201139278358.4223548171552311"),
    Decimal("64147886106222656.2384332732886897"),
]


def chunk_value(chunk: str) -> Decimal:
    total = Decimal(0)
    for exponent, ch in enumerate(chunk, 1):
        total += Decimal(ord(ch) - 48) * (BASE**exponent)
    return total


def is_correct(flag: str) -> bool:
    if len(flag) != EXPECTED_LEN:
        return False

    chunks = [flag[i : i + CHUNK_SIZE] for i in range(0, EXPECTED_LEN, CHUNK_SIZE)]
    values = [chunk_value(chunk) for chunk in chunks]
    return all(abs(value - target) < Decimal("0.1") for value, target in zip(values, TARGETS))


if __name__ == "__main__":
    candidate = input("Flag: ")
    print("Flag is correct!" if is_correct(candidate) else "Flag is incorrect.")
