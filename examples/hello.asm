mv r0 name
call print
hlt

# r0 - str pointer
print:
    mv ar r0
    ld r2 ar
    add ar 1
    print_while:
        cmp r2 0
        jz print_end
        ld r1 ar
        out r1 0
        sub r2 1
        add ar 1
        jmp print_while
    print_end:
        ret

name: "Hello world!"