import logging
import sys
from enum import IntEnum, auto

from isa import Command, Opcodes, Registers, read_code

max_int_32 = 2**31 - 1
min_int_32 = -(2**31)


class AluOps(IntEnum):
    LFT = 0
    RGT = auto()
    INC = auto()
    DEC = auto()
    SUM = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    REM = auto()


Alu = {
    AluOps.LFT: lambda x, y: x,
    AluOps.RGT: lambda x, y: y,
    AluOps.DEC: lambda x, y: x - 1,
    AluOps.INC: lambda x, y: x + 1,
    AluOps.SUM: lambda x, y: x + y,
    AluOps.SUB: lambda x, y: x - y,
    AluOps.MUL: lambda x, y: x * y,
    AluOps.DIV: lambda x, y: x // y,
    AluOps.REM: lambda x, y: x % y,
}


class DataPath:
    def __init__(self, code, memory_size, input_buffer):
        assert memory_size > 0, "Memory size should be positive."
        assert len(code) <= memory_size, "Not enough memory to store data."

        self.memory_size = memory_size
        self.memory = code[: len(code)] + [Command(data=0)] * (memory_size - len(code))
        self.r = [0] * len(Registers)
        self.r[Registers.SP.value] = len(self.memory) - 1

        self.zero = 1
        self.sign = 0
        self.overflow = 0

        self.input_buffer = input_buffer
        self.output_buffer = []

    # set flags, no register latch by itself
    def do_alu_operation(self, alu_op, sel_left, sel_right, latch_flags=True):
        left = self.r[sel_left.value]
        right = self.r[sel_right.value]

        res = Alu[alu_op](left, right)
        if latch_flags:
            self.zero = 1 if res == 0 else 0
            self.sign = 1 if res < 0 else 0
            self.overflow = 1 if res > max_int_32 or res < min_int_32 else 0
        if res > max_int_32:
            delta = res - max_int_32
            res = min_int_32 + delta + 1
        if res < min_int_32:
            delta = res - min_int_32
            res = max_int_32 + delta + 1

        return res

    # sel_reg_alu_data
    def latch_reg_alu_data(self, reg, alu_op, sel_left, sel_right, latch_flags=True):
        self.r[reg.value] = self.do_alu_operation(alu_op, sel_left, sel_right, latch_flags)

    # sel_reg_mem_data && oe
    def latch_reg_mem_data(self, reg, sel_addr):
        self.r[reg.value] = self.memory[self.r[sel_addr.value]].data

    # sel_reg_in_data && in_addr
    def latch_reg_in_data(self, reg):
        if len(self.input_buffer) == 0:
            raise EOFError()
        symbol = self.input_buffer.pop(0)
        symbol_code = ord(symbol)
        self.r[reg.value] = symbol_code
        logging.debug("input: %s\n", repr(symbol))

    # wr
    def mem_wr(self, sel_data, sel_addr):
        self.memory[self.r[sel_addr.value]] = Command(data=self.r[sel_data.value])

    # out_addr
    def output(self, sel_data):
        symbol = chr(self.r[sel_data.value])
        logging.debug("output: %s << %s\n", repr("".join(self.output_buffer)), repr(symbol))
        self.output_buffer.append(symbol)


class ControlUnit:
    def __init__(self, data_path):
        self._tick = 0
        self.data_path = data_path
        self.cur_command = None

    def tick(self):
        self._tick += 1

    def current_tick(self):
        return self._tick

    def increment_instruction_pointer(self):
        self.data_path.latch_reg_alu_data(
            Registers.IP,
            AluOps.INC,
            Registers.IP,
            Registers.IP,
            latch_flags=False,
        )

    def try_execute_control_flow_command(self, command) -> bool:
        match command.opcode:
            case Opcodes.NOP:
                self.tick()
                return True

            case Opcodes.HLT:
                raise StopIteration()

            case Opcodes.CMP:
                self.data_path.do_alu_operation(AluOps.SUB, command.r1, command.r2)
                self.tick()
                return True

            case Opcodes.CALL:
                # push instruction pointer
                self.data_path.latch_reg_alu_data(Registers.SP, AluOps.DEC, Registers.SP, Registers.SP)
                self.tick()
                self.data_path.mem_wr(sel_data=Registers.IP, sel_addr=Registers.SP)
                self.tick()

                # push base pointer
                self.data_path.latch_reg_alu_data(Registers.SP, AluOps.DEC, Registers.SP, Registers.SP)
                self.tick()
                self.data_path.mem_wr(sel_data=Registers.BP, sel_addr=Registers.SP)
                self.tick()

                # base pointer <- stack pointer
                self.data_path.latch_reg_alu_data(Registers.BP, AluOps.LFT, Registers.SP, Registers.SP)
                self.tick()

                # jmp function
                self.data_path.latch_reg_alu_data(Registers.IP, AluOps.LFT, command.r2, command.r2, latch_flags=False)
                self.tick()

                return True

            case Opcodes.RET:
                # stack pointer <- base pointer
                self.data_path.latch_reg_alu_data(Registers.SP, AluOps.LFT, Registers.BP, Registers.BP)
                self.tick()

                # pop base pointer
                self.data_path.latch_reg_mem_data(reg=Registers.BP, sel_addr=Registers.SP)
                self.tick()
                self.data_path.latch_reg_alu_data(Registers.SP, AluOps.INC, Registers.SP, Registers.SP)
                self.tick()

                # pop instruction pointer
                self.data_path.latch_reg_mem_data(reg=Registers.IP, sel_addr=Registers.SP)
                self.tick()
                self.data_path.latch_reg_alu_data(Registers.SP, AluOps.INC, Registers.SP, Registers.SP)
                self.tick()
                return True

            case Opcodes.JMP:
                self.data_path.latch_reg_alu_data(Registers.IP, AluOps.LFT, command.r2, command.r2, latch_flags=False)
                self.tick()
                return True

            case Opcodes.JZ:
                if self.data_path.zero == 1:
                    self.data_path.latch_reg_alu_data(
                        Registers.IP, AluOps.LFT, command.r2, command.r2, latch_flags=False
                    )
                self.tick()
                return True

            case Opcodes.JNZ:
                if self.data_path.zero == 0:
                    self.data_path.latch_reg_alu_data(
                        Registers.IP, AluOps.LFT, command.r2, command.r2, latch_flags=False
                    )
                self.tick()
                return True

            case Opcodes.JG:
                if self.data_path.zero == 0 and self.data_path.sign == self.data_path.overflow:
                    self.data_path.latch_reg_alu_data(
                        Registers.IP, AluOps.LFT, command.r2, command.r2, latch_flags=False
                    )
                self.tick()
                return True

            case Opcodes.JL:
                if self.data_path.sign != self.data_path.overflow:
                    self.data_path.latch_reg_alu_data(
                        Registers.IP, AluOps.LFT, command.r2, command.r2, latch_flags=False
                    )
                self.tick()
                return True

        return False

    def decode_and_execute_instruction(self):
        # read current instruction from memory
        self.data_path.latch_reg_mem_data(reg=Registers.CR, sel_addr=Registers.IP)
        self.tick()

        # decode instruction
        command: Command = self.data_path.memory[self.data_path.r[Registers.IP.value]]
        self.cur_command = command

        # ip contains next instruction addr
        self.increment_instruction_pointer()
        self.tick()

        # execute control flow command
        if self.try_execute_control_flow_command(command):
            return

        # else execute data flow command
        match command.opcode:
            case Opcodes.ST:
                self.data_path.mem_wr(sel_data=command.r1, sel_addr=command.r2)
                self.tick()

            case Opcodes.LD:
                self.data_path.latch_reg_mem_data(reg=command.r1, sel_addr=command.r2)
                self.tick()

            case Opcodes.PUSH:
                self.data_path.latch_reg_alu_data(Registers.SP, AluOps.DEC, Registers.SP, Registers.SP)
                self.tick()
                self.data_path.mem_wr(sel_data=command.r2, sel_addr=Registers.SP)
                self.tick()

            case Opcodes.POP:
                self.data_path.latch_reg_mem_data(reg=command.r2, sel_addr=Registers.SP)
                self.tick()
                self.data_path.latch_reg_alu_data(Registers.SP, AluOps.INC, Registers.SP, Registers.SP)
                self.tick()

            case Opcodes.IN:
                self.data_path.latch_reg_in_data(command.r1)
                self.tick()

            case Opcodes.OUT:
                self.data_path.output(command.r1)
                self.tick()

            case Opcodes.MV:
                self.data_path.latch_reg_alu_data(command.r1, AluOps.LFT, command.r2, command.r2)
                self.tick()

            case Opcodes.ADD:
                self.data_path.latch_reg_alu_data(command.r1, AluOps.SUM, command.r1, command.r2)
                self.tick()

            case Opcodes.SUB:
                self.data_path.latch_reg_alu_data(command.r1, AluOps.SUB, command.r1, command.r2)
                self.tick()

            case Opcodes.MUL:
                self.data_path.latch_reg_alu_data(command.r1, AluOps.MUL, command.r1, command.r2)
                self.tick()

            case Opcodes.DIV:
                self.data_path.latch_reg_alu_data(command.r1, AluOps.DIV, command.r1, command.r2)
                self.tick()

            case Opcodes.REM:
                self.data_path.latch_reg_alu_data(command.r1, AluOps.REM, command.r1, command.r2)
                self.tick()

    def __repr__(self):
        state_repr = "CR: {}\n".format(self.cur_command)
        state_repr += "TICK: {:6}    IP: {:8}    SP: {:8}    BP: {:8}    Z S O: {:1} {:1} {:1}    ADDR: {:6}\n".format(
            self._tick,
            self.data_path.r[Registers.IP.value],
            self.data_path.r[Registers.SP.value],
            self.data_path.r[Registers.BP.value],
            self.data_path.zero,
            self.data_path.sign,
            self.data_path.overflow,
            self.data_path.r[Registers.AR.value],
        )

        state_repr += "R0: {:8}    R1: {:8}    R2: {:8}    R3: {:8}    R4: {:8}    R5: {:8}\n".format(
            self.data_path.r[Registers.R0.value],
            self.data_path.r[Registers.R1.value],
            self.data_path.r[Registers.R2.value],
            self.data_path.r[Registers.R3.value],
            self.data_path.r[Registers.R4.value],
            self.data_path.r[Registers.R5.value],
        )

        state_repr += "R6: {:8}    R7: {:8}    R8: {:8}    R9: {:8}    R10: {:7}\n\n".format(
            self.data_path.r[Registers.R6.value],
            self.data_path.r[Registers.R7.value],
            self.data_path.r[Registers.R8.value],
            self.data_path.r[Registers.R9.value],
            self.data_path.r[Registers.R10.value],
        )

        return state_repr


def simulation(code, input_tokens, memory_size, limit):
    data_path = DataPath(code, memory_size, input_tokens)
    control_unit = ControlUnit(data_path)
    instr_counter = 0

    logging.debug("%s", control_unit)
    try:
        while instr_counter < limit:
            control_unit.decode_and_execute_instruction()
            instr_counter += 1
            logging.debug("%s", control_unit)
    except EOFError:
        logging.warning("Input buffer is empty!")
    except StopIteration:
        pass

    if instr_counter >= limit:
        logging.warning("Limit exceeded!")
    logging.info("output_buffer: %s", repr("".join(data_path.output_buffer)))
    return data_path.output_buffer, instr_counter, control_unit.current_tick()


def main(code_file, input_file):
    code = read_code(code_file)
    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_tokens = []
        for char in input_text:
            input_tokens.append(char)

    output, instr_counter, ticks = simulation(
        code,
        input_tokens,
        memory_size=128,
        limit=1024,
    )

    print("".join(output))
    print("instr_counter: ", instr_counter, "ticks:", ticks)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 3, "Wrong arguments: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)
