# R format - add, and, or, sll, slt, sra, srl, sub, xor, mul, div, rem
# I format - addi, andi, ori, lb, lh, lw, jalr
# S format - sb, sw, sh
# SB format - beq, bne, bge, blt
# U format - auipc, lui
# UJ format - jal

# ALUop       OPCODE        FUN3        FUNC7/FUN6
# 1 - add     0110011       000          0000000
# 2 - and     0110011       111          0000000
# 3 - or      0110011       110          0000000
# 4 - sll     0110011       001          0000000
# 5 - slt     0110011       010          0000000
# 6 - sra     0110011       101          0100000
# 7 - srl     0110011       101          0000000
# 8 - sub     0110011       000          0100000
# 9 - xor     0110011       100          0000000
# 10 - mul    0110011       000          0000001
# 11 - div    0110011       100          0000001
# 12 - rem    0110011       110          0000001

# 13 - addi   0010011       000          NA
# 14 - andi   0010011       111          NA
# 15 - ori    0010011       110          NA

# 16 - lb     0000011       000          NA
# 17 - lh     0000011       001          NA
# 18 - lw     0000011       010          NA

# 19 - jalr   1100111       000          NA

# 20 - sb     0100011       000          NA
# 21 - sw     0100011       010          NA
# 22 - sh     0100011       001          NA

# 23 - beq    1100011       000          NA
# 24 - bne    1100011       001          NA
# 25 - bge    1100011       101          NA
# 26 - blt    1100011       100          NA

# 27 - auipc  0010111       NA           NA

# 28 - lui    0110111       NA           NA

# 29 - jal    1101111       NA           NA

def twoS(s):
    f = ""
    f = ["0" if s[i] == '1' else "1" for i in range(len(s))]

    i = -1
    while (f[i] == '1' and abs(i) <= len(f)):
        f[i] = "0"
        i -= 1
    if (abs(i) != len(f)):
        f[i] = "1"
    f = "".join(f)
    return f


def two2dec(s):
    flag = "".join(s)
    if flag[0] == '1':
        return -1 * (int(''.join('1' if x == '0' else '0' for x in flag), 2) + 1)
    else:
        return int(flag, 2)


def dec2two(n):
    s = bin(int(n)).replace("0b", "").zfill(32)
    s = s[-32:]
    if (n >= 0):
        return list(s)
    else:
        return list(twoS(s))


def assignRegister(registerNum, reqValue):
    temp_assignReg = list(str(bin(int(reqValue, 16))[2:]).zfill(32))
    for i in range(32):
        registerFile[registerNum][i] = temp_assignReg[i]


registerFile = [['0' for i in range(32)] for j in range(32)]  # 0-based indexing

# Stack Pointer 0x7FFFFFFC
assignRegister(2, "0x7FFFFFFC")

# Initializing Variables
dataSegment = {}
instructionSegment = {}
PC = ['0' for i in range(32)]
IR = ['0' for i in range(32)]
rd = ""
rs1 = ""
rs2 = ""
clock = 0
immediate = ""
ALUop = -1
RA = ['0' for i in range(32)]
RB = ['0' for i in range(32)]
RM = ['0' for i in range(32)]
RZ = ['0' for i in range(32)]
MuxASelect = 0
MuxBSelect = 0
MuxINCSelect = 0
isBranch = 0
MuxPCSelect = 0
MuxYSelect = 0
memRead = 0
memWrite = 0
loadType = 0
storeType = 0
writeRegisterFile = 0
MAR = ['0' for i in range(32)]
MDR = ['0' for i in range(32)]
nINC = ['0' for i in range(32)]
PCtemp = ['0' for i in range(32)]
nRB = ['0' for i in range(32)]
RY = ['0' for i in range(32)]


# Initializing all 32 registers to 0
def resetSimulator():
    global PC, clock, IR, dataSegment
    dataSegment = {}
    loadDataSegment()
    clock = 0
    for i in range(32):
        PC[i] = '0'
        IR[i] = '0'
    for i in range(32):
        assignRegister(i, "0x0")
    assignRegister(2, "0x7FFFFFFC")


def loadDataSegment():
    # Address for data segment  "0x10000000"
    file = open("test.mc", "r+")
    data = file.readlines()
    for line in data:
        word = list(line.split())
        if (int(word[0], 0) >= int("0x10000000", 0)):
            word[0] = str(bin(int(word[0], 16))[2:]).zfill(32)
            word[1] = str(bin(int(word[1], 16))[2:]).zfill(8)
            dataSegment[word[0]] = word[1]


def loadInstructionSegment():
    file = open("test.mc", "r+")
    data = file.readlines()
    for line in data:
        word = list(line.split())
        # word is in little Indian
        # Convert in Big Indian
    
        if (int(word[0], 0) < int("0x10000000", 0)):
            big_endian ="0x"+word[1][8]+word[1][9]+word[1][6]+word[1][7]+word[1][4]+word[1][5]+word[1][2]+word[1][3]
            word[0] = str(bin(int(word[0], 16))[2:]).zfill(32)
            big_endian = str(bin(int(big_endian, 16))[2:]).zfill(32)
            instructionSegment[word[0]] = big_endian


def fetchInstruction():
    global IR, PCtemp
    temp_IR = list(instructionSegment["".join(PC)])
    for i in range(32):
        IR[i] = temp_IR[i]
    PCtemp = dec2two(two2dec(PC) + 4)


def decodeInstruction():
    global MuxASelect, ALUop, rd, rs1, rs2, immediate, MuxBSelect, MuxINCSelect, MuxPCSelect, MuxYSelect, memWrite, memRead, RA, RB, RM, writeRegisterFile, loadType, storeType, isBranch
    opCode = "".join(IR[25:32])
    ALUop = -1
    rd = ""
    rs1 = ""
    rs2 = ""
    immediate = ""
    writeRegisterFile = 0
    MuxASelect = 0
    MuxBSelect = 0  # RB is selected(I-type)
    MuxINCSelect = 0
    isBranch = 0
    MuxPCSelect = 0
    MuxYSelect = 0  # RZ is selected   1 - MDR is selected  2 - PCtemp is selected
    memWrite = 0
    memRead = 0
    loadType = 0
    storeType = 0
    # R-type instruction
    if (opCode == "0110011"):
        func3 = "".join(IR[17:20])
        func7 = "".join(IR[:7])
        if (func3 == "000" and func7 == "0000000"):
            ALUop = 1  # add
            writeRegisterFile = 1
        elif (func3 == "111" and func7 == "0000000"):
            ALUop = 2  # and
            writeRegisterFile = 1
        elif (func3 == "110" and func7 == "0000000"):
            ALUop = 3  # or
            writeRegisterFile = 1
        elif (func3 == "001" and func7 == "0000000"):
            ALUop = 4  # sll
            writeRegisterFile = 1
        elif (func3 == "010" and func7 == "0000000"):
            ALUop = 5  # slt
            writeRegisterFile = 1
        elif (func3 == "101" and func7 == "0100000"):
            ALUop = 6  # sra
            writeRegisterFile = 1
        elif (func3 == "101" and func7 == "0000000"):
            ALUop = 7  # srl
            writeRegisterFile = 1
        elif (func3 == "000" and func7 == "0100000"):
            ALUop = 8  # sub
            writeRegisterFile = 1
        elif (func3 == "100" and func7 == "0000000"):
            ALUop = 9  # xor
            writeRegisterFile = 1
        elif (func3 == "000" and func7 == "0000001"):
            ALUop = 10  # mul
            writeRegisterFile = 1
        elif (func3 == "100" and func7 == "0000001"):
            ALUop = 11  # div
            writeRegisterFile = 1
        elif (func3 == "110" and func7 == "0000001"):
            ALUop = 12  # rem
            writeRegisterFile = 1

    # I-type instruction
    elif (opCode == "0010011"):
        func3 = "".join(IR[17:20])
        if (func3 == "000"):
            ALUop = 13  # addi
            writeRegisterFile = 1
            MuxBSelect = 1
        elif (func3 == "111"):
            ALUop = 14  # andi
            writeRegisterFile = 1
            MuxBSelect = 1
        elif (func3 == "110"):
            ALUop = 15  # ori
            writeRegisterFile = 1
            MuxBSelect = 1

    elif (opCode == "0000011"):
        func3 = "".join(IR[17:20])
        if (func3 == "000"):
            ALUop = 16  # lb
            memRead = 1
            MuxYSelect = 1
            MuxBSelect = 1
            writeRegisterFile = 1
            loadType = 0
        elif (func3 == "001"):
            ALUop = 17  # lh
            memRead = 1
            MuxYSelect = 1
            MuxBSelect = 1
            writeRegisterFile = 1
            loadType = 1
        elif (func3 == "010"):
            ALUop = 18  # lw
            memRead = 1
            MuxYSelect = 1
            MuxBSelect = 1
            writeRegisterFile = 1
            loadType = 2
    elif (opCode == "1100111"):
        func3 = "".join(IR[17:20])
        if (func3 == "000"):
            ALUop = 19  # jalr
            MuxPCSelect = 1
            MuxYSelect = 2
            MuxBSelect = 1
            MuxINCSelect = 1
            isBranch = 1
            writeRegisterFile = 1

    # S-type instruction

    elif (opCode == "0100011"):
        func3 = "".join(IR[17:20])
        if (func3 == "000"):
            MuxBSelect = 1
            memWrite = 1
            ALUop = 20  # sb
            storeType = 0
        elif (func3 == "010"):
            MuxBSelect = 1
            memWrite = 1
            ALUop = 21  # sw
            storeType = 2
        elif (func3 == "001"):
            MuxBSelect = 1
            memWrite = 1
            ALUop = 22  # sh
            storeType = 1

    # SB-type instruction
    elif (opCode == "1100011"):
        func3 = "".join(IR[17:20])
        if (func3 == "000"):
            ALUop = 23  # beq
            isBranch = 1
        elif (func3 == "001"):
            ALUop = 24  # bne
            isBranch = 1
        elif (func3 == "101"):
            ALUop = 25  # bge
            isBranch = 1
        elif (func3 == "100"):
            ALUop = 26  # blt
            isBranch = 1

    # U-type instruction
    elif (opCode == "0010111"):
        ALUop = 27  # auipc
        MuxASelect = 1
        MuxBSelect = 1
        writeRegisterFile = 1

    elif (opCode == "0110111"):
        ALUop = 28  # lui
        MuxBSelect = 1
        writeRegisterFile = 1

    # UJ-type instruction
    elif (opCode == "1101111"):
        ALUop = 29  # jal
        MuxYSelect = 2
        MuxINCSelect = 1
        isBranch = 1
        writeRegisterFile = 1

    if (ALUop != -1):
        # 20 - 26 = No rd, both inclusive
        if (not (ALUop >= 20 and ALUop <= 26)):
            rd = "".join(IR[20:25])
        # 27-29 = No rs1
        if (not (ALUop >= 27 and ALUop <= 29)):
            rs1 = "".join(IR[12:17])
            RA = registerFile[int(rs1, 2)]

        # 13 - 19   27-29 = No rs2
        if ((ALUop >= 1 and ALUop <= 12) or (ALUop >= 20 and ALUop <= 26)):
            rs2 = "".join(IR[7:12])
            RB = registerFile[int(rs2, 2)]
            RM = RB[:]

        # I-format
        if (ALUop >= 13 and ALUop <= 19):
            temp = "".join(IR[:12])
            immediate = temp[0] * (32 - len(temp)) + temp
        # S-format
        elif (ALUop >= 20 and ALUop <= 22):
            temp = "".join(IR[:7]) + "".join(IR[20:25])
            immediate = temp[0] * (32 - len(temp)) + temp
        # SB-format
        elif (ALUop >= 23 and ALUop <= 26):
            temp = IR[0] + IR[24] + "".join(IR[1:7]) + "".join(IR[20:24]) + '0'
            immediate = temp[0] * (32 - len(temp)) + temp
        # U-format
        elif (ALUop == 27 or ALUop == 28):
            immediate = "".join(IR[:20]) + '0' * 12
        # UJ-format
        elif (ALUop == 29):
            temp = IR[0] + "".join(IR[12:20]) + IR[11] + "".join(IR[1:11]) + '0'
            immediate = temp[0] * (32 - len(temp)) + temp


def MuxA():
    global nRA, RA, PC
    if (MuxASelect == 0):
        nRA = RA[:]
    elif (MuxASelect == 1):
        nRA = PC[:]


def MuxB():
    global nRB, RB, immediate
    if (MuxBSelect == 0):
        nRB = RB[:]
    elif (MuxBSelect == 1):
        for i in range(32):
            nRB[i] = immediate[i]


def executeInstruction():
    global RZ, ALUop, nRA, nRB, MuxINCSelect
    # inputs are RA and nRB
    # output is RZ
    # two2dec takes an array(containing 2's complement binary number) and returns equivalent decimal number.
    MuxA()
    MuxB()
    if (ALUop == 1 or ALUop == 13 or (ALUop >= 16 and ALUop <= 18) or (ALUop >= 20 and ALUop <= 22)):
        RZ = dec2two(two2dec(nRA) + two2dec(nRB))

    elif (ALUop == 2 or ALUop == 14):
        RZ = dec2two(two2dec(nRA) & two2dec(nRB))
    elif (ALUop == 3 or ALUop == 15):
        RZ = dec2two(two2dec(nRA) | two2dec(nRB))
    elif (ALUop == 4):
        RZ = dec2two(two2dec(nRA) << (two2dec(nRB) % 32))
    elif (ALUop == 5):
        if (two2dec(nRA) < two2dec(nRB)):
            for i in range(32):
                RZ[i] = '0'
            RZ[31] = '1'
        else:
            for i in range(32):
                RZ[i] = '0'
    elif (ALUop == 6):
        # sra
        if (RA[0] == '0'):
            RZ = dec2two(two2dec(nRA) >> (two2dec(nRB) % 32))
        else:
            RZ = dec2two(two2dec(nRA) >> (two2dec(nRB) % 32))

            for i in range(32):
                if (RZ[i] == '1'):
                    break
                else:
                    RZ[i] = '1'
    elif (ALUop == 7):
        RZ = dec2two(two2dec(nRA) >> (two2dec(nRB) % 32))  # srl
    elif (ALUop == 8):
        RZ = dec2two(two2dec(nRA) - two2dec(nRB))  # sub
    elif (ALUop == 9):
        RZ = dec2two(two2dec(nRA) ^ two2dec(nRB))  # xor
    elif (ALUop == 10):
        RZ = dec2two(two2dec(nRA) * two2dec(nRB))  # mul
    elif (ALUop == 11):
        # Check for division of 0
        RZ = dec2two(two2dec(nRA) / two2dec(nRB))  # div
    elif (ALUop == 12):
        RZ = dec2two(two2dec(nRA) % two2dec(nRB))  # rem
    elif (ALUop == 23):
        # Input 4 - 0, Input immediate - 1
        if (two2dec(nRA) == two2dec(nRB)):
            for i in range(32):
                RZ[i] = '0'
            RZ[31] = '1'
        else:
            for i in range(32):
                RZ[i] = '0'
    elif (ALUop == 24):
        if (two2dec(nRA) != two2dec(nRB)):
            for i in range(32):
                RZ[i] = '0'
            RZ[31] = '1'
        else:
            for i in range(32):
                RZ[i] = '0'
    elif (ALUop == 25):
        if (two2dec(nRA) >= two2dec(nRB)):
            for i in range(32):
                RZ[i] = '0'
            RZ[31] = '1'
        else:
            for i in range(32):
                RZ[i] = '0'
    elif (ALUop == 26):
        if (two2dec(nRA) < two2dec(nRB)):
            for i in range(32):
                RZ[i] = '0'
            RZ[31] = '1'
        else:
            for i in range(32):
                RZ[i] = '0'
    elif (ALUop == 27):
        RZ = dec2two(two2dec(nRA) + two2dec(nRB))  # auipc
    elif (ALUop == 28):
        RZ = nRB[:]
    elif (ALUop == 19 or ALUop == 29):
        for i in range(32):
            RZ[i] = '0'
        RZ[31] = '1'


def memoryAccess():
    global MAR, memRead, MDR, RM, RZ, memWrite, dataSegment, loadType, storeType
    if (memRead == 1):
        MAR = RZ[:]
        if ("".join(MAR) in dataSegment):
            temp1 = list(dataSegment["".join(MAR)])
        else:
            temp1 = ['0' for i in range(8)]

        if (loadType == 0):  # lb
            temp2 = [temp1[0] for i in range(8)]
        else:
            if ("".join(dec2two(two2dec(MAR) + 1)) in dataSegment):
                temp2 = list(dataSegment["".join(dec2two(two2dec(MAR) + 1))])
            else:
                temp2 = ['0' for i in range(8)]

        if (loadType == 0 or loadType == 1):
            temp3 = [temp2[0] for i in range(8)]
        else:
            if ("".join(dec2two(two2dec(MAR) + 2)) in dataSegment):
                temp3 = list(dataSegment["".join(dec2two(two2dec(MAR) + 2))])
            else:
                temp3 = ['0' for i in range(8)]

        if (loadType == 0 or loadType == 1):
            temp4 = [temp3[0] for i in range(8)]
        else:
            if ("".join(dec2two(two2dec(MAR) + 3)) in dataSegment):
                temp4 = list(dataSegment["".join(dec2two(two2dec(MAR) + 3))])
            else:
                temp4 = ['0' for i in range(8)]

        temp = temp4 + temp3 + temp2 + temp1

        for i in range(32):
            MDR[i] = temp[i]

    elif (memWrite == 1):
        MDR = RM[:]
        MAR = RZ[:]
        temp_str = "00000000"
        dataSegment["".join(MAR)] = "".join(MDR[24:32])
        if ("".join(MDR[24:32]) == temp_str):
            del dataSegment["".join(MAR)]

        if (storeType == 1 or storeType == 2):
            dataSegment["".join(dec2two(two2dec(MAR) + 1))] = "".join(MDR[16:24])
            if ("".join(MDR[16:24]) == temp_str):
                del dataSegment["".join(dec2two(two2dec(MAR) + 1))]

        if (storeType == 2):
            dataSegment["".join(dec2two(two2dec(MAR) + 2))] = "".join(MDR[8:16])
            if ("".join(MDR[8:16]) == temp_str):
                del dataSegment["".join(dec2two(two2dec(MAR) + 2))]

            dataSegment["".join(dec2two(two2dec(MAR) + 3))] = "".join(MDR[0:8])
            if ("".join(MDR[0:8]) == temp_str):
                del dataSegment["".join(dec2two(two2dec(MAR) + 3))]

    # elif(memWrite==0 and memRead==0):
    # pass(as memory is not accessed)


def MuxY():
    global MuxSelect, RY, RZ, MDR, PCtemp
    if (MuxYSelect == 0):
        RY = RZ[:]
    elif (MuxYSelect == 1):
        RY = MDR[:]
    elif (MuxYSelect == 2):
        RY = PCtemp[:]


def registerUpdate():
    global ALUop, RY, registerFile
    MuxY()
    if (writeRegisterFile == 1):
        if (int(rd, 2) != 0):
            registerFile[int(rd, 2)] = RY[:]


def INCAndGate():
    global isBranch, MuxINCSelect, RZ
    MuxINCSelect = isBranch & int(RZ[31])


def MuxPC():
    global PC, RA, MuxPCSelect
    if (MuxPCSelect == 0):
        PC = PC[:]
    elif (MuxPCSelect == 1):
        PC = RA[:]


def MuxINC():
    global MuxINCSelect, nINC, immediate
    if (MuxINCSelect == 0):
        for i in range(32):
            nINC[i] = '0'
        nINC[29] = '1'
    elif (MuxINCSelect == 1):
        for i in range(32):
            nINC[i] = immediate[i]


def instructionAddressGeneration():
    global PC, MuxINCSelect, RZ
    INCAndGate()
    MuxPC()
    MuxINC()
    PC = dec2two(two2dec(PC) + two2dec(nINC))


def fileUpdate():
    file = open("test.mc", "r+")
    file.truncate()
    for i in sorted(instructionSegment):
        file.write(
            "0x" + str(hex(int(i, 2))[2:].zfill(8)) + " " + "0x" + str(hex(int(instructionSegment[i], 2)))[2:].zfill(
                8) + "\n")

    for i in sorted(dataSegment):
        file.write(
            "0x" + str(hex(int(i, 2))[2:].zfill(8)) + " " + "0x" + str(hex(int(dataSegment[i], 2)))[2:].zfill(2) + "\n")


def printRegisters():
    print("< Cycle Number >",clock)
    print("< PC >","".join(PC))
    print("< IR >","".join(IR))
    print()
    for i in range(8):
        for j in range(4):
            regNum = 8 * j + i
            if(regNum == 8 or regNum == 9):
                print("x" + str(regNum) + "  = 0x" + str(hex(int("".join(registerFile[regNum]), 2))[2:]).zfill(8), end='      ')
            else:
                print("x" + str(regNum) + " = 0x" + str(hex(int("".join(registerFile[regNum]), 2))[2:]).zfill(8), end='      ')
        print()
    print("\n")


# def printRegisters():
#  output = open("result.txt", "a+")
#  for i in range(32):
#    output.write("x" + str(i) + " = " + hex(int("".join(registerFile[i]), 2)) + #"\n")
#  output.write("\n")
# main



def terminal():
    global clock, PC, IR

    print("Select the configuration in which you wish to run the simulator")
    print("Enter 1 to run step by step")
    print("Enter any other key to run at once")
    flag = int(input("Enter your choice : "))
    flag2 = 'r' if (flag == 1) else 'R'

    while (True):
        clock = clock + 1
        fetchInstruction()
        if (int("".join(IR), 2) == 0):
            break
        decodeInstruction()
        executeInstruction()
        memoryAccess()
        registerUpdate()
        if (flag == 1 and flag2 == 'r'):
            printRegisters()
        instructionAddressGeneration()
        if(flag == 1 and flag2 == 'r'):
            flag2 = input("Enter r for running the next step\nEnter any other key to run the remaining steps at once\nEnter your choice : ")
    print("\n--------------------------- Code executed succesfully ---------------------------")
    print("\n============================== Final Register File ==============================\n")
    printRegisters()
    fileUpdate()
