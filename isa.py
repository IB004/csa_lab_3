import json
from enum import IntEnum, auto

max_int_32 = 2**31 - 1
min_int_32 = -(2**31)

max_int_22 = 2**21 - 1
min_int_22 = -(2**21)


class Opcodes(IntEnum):
    NOP = 0
    HLT = auto()

    CALL = auto()
    RET = auto()

    CMP = auto()
    JMP = auto()
    JZ = auto()
    JNZ = auto()
    JL = auto()
    JG = auto()

    ST = auto()
    LD = auto()
    POP = auto()
    PUSH = auto()

    IN = auto()
    OUT = auto()

    MV = auto()
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    REM = auto()


class Registers(IntEnum):
    R0 = 0
    R1 = 1
    R2 = 2
    R3 = 3

    R4 = 4
    R5 = 5
    R6 = 6
    R7 = 7

    R8 = 8
    R9 = 9
    R10 = 10
    AR = 11

    BP = 12
    SP = 13
    IP = 14
    CR = 15


class Command:
    def __init__(
        self,
        opcode=None,
        r1=None,
        r2=None,
        data=None,
        label=None,
    ):
        self.opcode = opcode
        self.r1 = r1
        self.r2 = r2
        self.data = 0 if data is None else data
        self.label = label

    def __repr__(self):
        opcode_name = "-" if self.opcode is None else self.opcode.name
        r1_name = "-" if self.r1 is None else self.r1.name
        r2_name = "-" if self.r2 is None else self.r2.name
        label = "" if self.label is None else "(" + self.label + ")"
        data = "" if self.r2 != Registers.CR and (self.r1 is not None or self.r2 is not None) else str(self.data)

        n_just = 6
        if self.r2 == Registers.CR:
            return f"{opcode_name.ljust(n_just)} {r1_name.ljust(n_just)} {data.ljust(n_just)} {label.ljust(n_just)}"
        return f"{opcode_name.ljust(n_just)} {r1_name.ljust(n_just)} {r2_name.ljust(n_just)} {data.ljust(n_just)}"


def write_code(filename, code):
    with open(filename, "w", encoding="utf-8") as file:
        buf = []
        for instr in code:
            buf.append(json.dumps(instr.__dict__))
        file.write("[" + ",\n ".join(buf) + "]")


def read_code(filename):
    commands = []
    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())

    for instr in code:
        opcode = None if instr["opcode"] is None else Opcodes(instr["opcode"])
        r1 = None if instr["r1"] is None else Registers(instr["r1"])
        r2 = None if instr["r2"] is None else Registers(instr["r2"])
        data = None if instr["data"] is None else int(instr["data"])
        label = instr["label"]
        commands.append(Command(opcode, r1, r2, data, label))

    return commands
