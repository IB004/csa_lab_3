mv r1 1
mv r2 2
mv r4 2         # sum reg
while:
    mv r3 r1
    add r3 r2
    cmp r3 4000000
    jg end
    mv r1 r2
    mv r2 r3
    rem r3 2
    jnz while
    add r4 r2
    jmp while
end:
    mv r0 r4
    call print_number
    hlt

# r0 - number
print_number:
    mv r8 r0
    rem r8 10
    add r8 48           # turn to number char
    push r8
    div r0 10
    cmp r0 0
    jz out_number
    jmp print_number
    out_number:
        cmp sp bp
        jz return
        pop r8
        out r8 0
        jmp out_number
    return:
        mv r8 10        # new line char
        out r8 0
        ret