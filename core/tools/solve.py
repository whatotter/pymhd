"""
a small tool to help me do basic math i refuse to do with a calculator
"""

def solve_linear_mapping(raw1: int, phys1: float, raw2: int, phys2: float):
    """
    Solve for factor (scale) and offset in a linear CAN mapping:
        physical = raw * factor + offset

    Args:
        raw1 (int): First raw value (integer from CAN bytes).
        phys1 (float): Corresponding physical value.
        raw2 (int): Second raw value.
        phys2 (float): Corresponding physical value.

    Returns:
        tuple: (factor, offset)
    """
    if raw1 == raw2:
        raise ValueError("raw1 and raw2 must be different to solve mapping")

    factor = (phys2 - phys1) / (raw2 - raw1)
    offset = phys1 - factor * raw1
    return factor, offset

def decode(raw: int, factor: float, offset: float) -> float:
    return raw * factor + offset

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("sb_eq_int", help="starting byte = starting int")
parser.add_argument("eb_eq_int", help="ending byte = ending int")
args = parser.parse_args()

hexByteOne, physIntOne = args.sb_eq_int.split("=")
hexByteTwo, physIntTwo = args.eb_eq_int.split("=")

factor, offset = solve_linear_mapping(
    int(hexByteOne), float(physIntOne), 
    int(hexByteTwo), float(physIntTwo)
    )

print("-" * 10)
print("Factor: {}".format(factor))
print("Offset: {}".format(offset))
print("-" * 10)
