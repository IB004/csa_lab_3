import sys

from isa import Command, Opcodes, Registers, write_code
from tokenizer import TokenNames, TokenTypes, tokenize


class UnknownTypeOfCommandError(Exception):
    pass


def is_register(token):
    return isinstance(token.type.enum, Registers)


def is_number(token):
    return token.type == TokenTypes[TokenNames.NUMBER]


def is_label(token):
    return token.type == TokenTypes[TokenNames.IDENT]


def parse_second_reg(operand, command):
    if is_register(operand):
        command.r2 = operand.type.enum

    if is_number(operand):
        command.r2 = Registers.CR
        command.data = int(operand.text)

    if is_label(operand):
        command.r2 = Registers.CR
        command.label = operand.text


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.labels = {}
        self.code = []

    def on_top(self, *type_names):
        if len(self.tokens) < len(type_names):
            return False
        for i in range(len(type_names)):
            if self.tokens[i].type != TokenTypes[type_names[i]]:
                return False
        return True

    def on_top_operation(self, operands):
        token_type = self.tokens[0].type
        return isinstance(token_type.enum, Opcodes) and token_type.operands == operands and len(self.tokens) >= operands

    def parse_code(self):
        while len(self.tokens) > 0:
            self.parse_code_line()
        self.fill_label_addr()
        return self.code

    def parse_code_line(self):
        pc = len(self.code)

        # <label>: ...
        if self.on_top(TokenNames.IDENT, TokenNames.COLON):
            label = self.tokens.pop(0).text
            assert label not in self.labels, f"Redefinition of label: {label}"
            self.labels[label] = pc
            self.tokens.pop(0)  # :
            return

        # number
        if self.on_top(TokenNames.NUMBER):
            token = self.tokens.pop(0)
            self.code.append(Command(data=int(token.text)))
            return

        # string
        if self.on_top(TokenNames.STRING):
            token = self.tokens.pop(0)
            length = len(token.text) - 2
            self.code.append(Command(data=length))
            for i in range(1, length + 1):
                self.code.append(Command(data=ord(token.text[i])))
            return

        # alloc
        if self.on_top(TokenNames.ALLOC):
            token = self.tokens.pop(0)
            length = int(token.text[1:-1])
            for i in range(length):
                self.code.append(Command(data=0))
            return

        # op <...> <...>
        if not self.try_parse_operation_command():
            raise UnknownTypeOfCommandError

    def try_parse_operation_command(self):
        # op
        if self.on_top_operation(0):
            self.parse_void_operation()
            return True

        # op ...
        if self.on_top_operation(1):
            self.parse_unary_operation()
            return True

        # op ... ...
        if self.on_top_operation(2):
            self.parse_bin_operation()
            return True

        return False

    def parse_void_operation(self):
        token_type = self.tokens.pop(0).type
        command = Command(token_type.enum)
        self.code.append(command)

    def parse_unary_operation(self):
        operation_type = self.tokens.pop(0).type

        operand = self.tokens.pop(0)

        command = Command(operation_type.enum)
        parse_second_reg(operand, command)

        if operation_type.enum == Opcodes.POP:
            assert command.r2 != Registers.CR, "Can pop only to register."

        self.code.append(command)

    def parse_bin_operation(self):
        operation_type = self.tokens.pop(0).type

        first = self.tokens.pop(0)

        assert is_register(first), "First operand should be a register."

        second = self.tokens.pop(0)

        command = Command(operation_type.enum)
        command.r1 = first.type.enum
        parse_second_reg(second, command)

        self.code.append(command)

    def fill_label_addr(self):
        for command in self.code:
            if command.label is not None:
                assert command.r2 == Registers.CR, "Use label with CR."
                assert command.label in self.labels, f"Unknown label '{command.label}'"
                command.data = self.labels[command.label]


def main(source, target):
    with open(source, encoding="utf-8") as f:
        source = f.read()

    tokens = tokenize(source)
    parser = Parser(tokens)
    code = parser.parse_code()

    write_code(target, code)
    print("source LoC:", len(source.split("\n")), "code instr:", len(code))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: parser.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
