import re
from enum import Enum, auto

from isa import Opcodes, Registers


class UnresolvedSymbolError(Exception):
    def __init__(self, pos, unresolved):
        super().__init__(f"Can not resolve symbol on position {pos}:\n{unresolved}...")


class TokenType:
    def __init__(self, name, regex, enum=None, operands=0):
        self.name = name
        self.regex = regex
        self.enum = enum
        self.operands = operands


class TokenNames(Enum):
    HLT = 0

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

    R0 = auto()
    R1 = auto()
    R2 = auto()
    R3 = auto()
    R4 = auto()
    R5 = auto()
    R6 = auto()
    R7 = auto()
    R8 = auto()
    R9 = auto()
    R10 = auto()
    AR = auto()

    BP = auto()
    SP = auto()

    NUMBER = auto()
    STRING = auto()
    ALLOC = auto()

    IDENT = auto()

    COLON = auto()
    SPACE = auto()
    COMMENT = auto()


TokenTypes = {
    TokenNames.HLT: TokenType("HLT", "hlt\\b", Opcodes.HLT, 0),
    TokenNames.CALL: TokenType("CALL", "call\\b", Opcodes.CALL, 1),
    TokenNames.RET: TokenType("RET", "ret\\b", Opcodes.RET, 0),
    TokenNames.CMP: TokenType("CMP", "cmp\\b", Opcodes.CMP, 2),
    TokenNames.JMP: TokenType("JMP", "jmp\\b", Opcodes.JMP, 1),
    TokenNames.JZ: TokenType("JZ", "jz\\b", Opcodes.JZ, 1),
    TokenNames.JNZ: TokenType("JNZ", "jnz\\b", Opcodes.JNZ, 1),
    TokenNames.JL: TokenType("JL", "jl\\b", Opcodes.JL, 1),
    TokenNames.JG: TokenType("JG", "jg\\b", Opcodes.JG, 1),
    TokenNames.ST: TokenType("ST", "st\\b", Opcodes.ST, 2),
    TokenNames.LD: TokenType("LD", "ld\\b", Opcodes.LD, 2),
    TokenNames.POP: TokenType("POP", "pop\\b", Opcodes.POP, 1),
    TokenNames.PUSH: TokenType("PUSH", "push\\b", Opcodes.PUSH, 1),
    TokenNames.IN: TokenType("IN", "in\\b", Opcodes.IN, 2),
    TokenNames.OUT: TokenType("OUT", "out\\b", Opcodes.OUT, 2),
    TokenNames.MV: TokenType("MV", "mv\\b", Opcodes.MV, 2),
    TokenNames.ADD: TokenType("ADD", "add\\b", Opcodes.ADD, 2),
    TokenNames.SUB: TokenType("SUB", "sub\\b", Opcodes.SUB, 2),
    TokenNames.MUL: TokenType("MUL", "mul\\b", Opcodes.MUL, 2),
    TokenNames.DIV: TokenType("DIV", "div\\b", Opcodes.DIV, 2),
    TokenNames.REM: TokenType("REM", "rem\\b", Opcodes.REM, 2),
    TokenNames.R0: TokenType("R0", "r0\\b", Registers.R0),
    TokenNames.R1: TokenType("R1", "r1\\b", Registers.R1),
    TokenNames.R2: TokenType("R2", "r2\\b", Registers.R2),
    TokenNames.R3: TokenType("R3", "r3\\b", Registers.R3),
    TokenNames.R4: TokenType("R4", "r4\\b", Registers.R4),
    TokenNames.R5: TokenType("R5", "r5\\b", Registers.R5),
    TokenNames.R6: TokenType("R6", "r6\\b", Registers.R6),
    TokenNames.R7: TokenType("R7", "r7\\b", Registers.R7),
    TokenNames.R8: TokenType("R8", "r8\\b", Registers.R8),
    TokenNames.R9: TokenType("R9", "r9\\b", Registers.R9),
    TokenNames.R10: TokenType("R10", "r10\\b", Registers.R10),
    TokenNames.AR: TokenType("AR", "ar\\b", Registers.AR),
    TokenNames.BP: TokenType("BP", "bp\\b", Registers.BP),
    TokenNames.SP: TokenType("SP", "sp\\b", Registers.SP),
    TokenNames.NUMBER: TokenType("NUMBER", "[-+]?\\d+"),
    TokenNames.STRING: TokenType("STRING", '".*"'),
    TokenNames.ALLOC: TokenType("ALLOC", "\\[\\d+\\]"),
    TokenNames.IDENT: TokenType("IDENT", "\\w+"),
    TokenNames.COLON: TokenType("COLON", ":"),
    TokenNames.SPACE: TokenType("SPACE", "\\s"),
    TokenNames.COMMENT: TokenType("COMMENT", "#.*"),
}


class Token:
    def __init__(self, token_type, text="no_repr", pos=0):
        self.type = token_type
        self.text = text
        self.pos = pos

    def __str__(self):
        return f"{(self.type.name + ':').ljust(12)} {self.text.ljust(8)} ({self.pos})"

    def __repr__(self):
        return f"{self.type.name + ':'} {self.text} ({self.pos})"


ignore_token_types = [TokenTypes[TokenNames.SPACE], TokenTypes[TokenNames.COMMENT]]


def tokenize(code):
    pos = 0
    tokens = []
    while pos < len(code):
        token = get_next_token(code, pos)
        pos += len(token.text)
        if token.type not in ignore_token_types:
            tokens.append(token)
    return tokens


def get_next_token(code, pos):
    for token_type in TokenTypes.values():
        pattern = "^" + token_type.regex
        match = re.search(pattern, code[pos:], re.IGNORECASE)
        if match is None:
            continue
        res = match[0]
        return Token(token_type, res, pos)
    unresolved = code[pos : pos + 10] if pos + 10 < len(code) else code[pos:]

    raise UnresolvedSymbolError(pos, unresolved)


def print_tokens(tokens):
    for token in tokens:
        print(token)
