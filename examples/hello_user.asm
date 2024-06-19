mv r0 question
call print

mv r0 name
mv r1 32
call input_name

mv r0 greeting
call print

mv r0 name
call print

mv r0 ending
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

# r0 - buffer pointer
# r1 - buffer size
input_name:
    mv ar r0
    add ar 1
    sub r1 1
    mv r2 0                 # r2 - counter
    input_name_while:
        cmp r2 r1
        jz input_name_end
        in r3 1
        cmp r3 10           # '\\n'
        jz input_name_end
        st r3 ar
        add r2 1
        add ar 1
        jmp input_name_while
    input_name_end:
        st r2 r0
        ret


question: "What is your name? "
greeting: "Hello, "
ending: "!"
name: [32]