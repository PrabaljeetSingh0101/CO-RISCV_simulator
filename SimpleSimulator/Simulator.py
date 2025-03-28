def execute_r_type(funct3, funct7, rs1, rs2, rd):
    global regts  # Access the register list
    val1 = regts[int(rs1[1:])]  # Extract integer index
    val2 = regts[int(rs2[1:])]
    
    if funct3 == "000" and funct7 == "0000000":  # ADD
        regts[int(rd[1:])] = val1 + val2
    elif funct3 == "000" and funct7 == "0100000":  # SUB
        regts[int(rd[1:])] = val1 - val2
    elif funct3 == "111":  # AND
        regts[int(rd[1:])] = val1 & val2
    elif funct3 == "110":  # OR
        regts[int(rd[1:])] = val1 | val2
    elif funct3 == "100":  # XOR
        regts[int(rd[1:])] = val1 ^ val2
    elif funct3 == "001":  # SLL (Shift Left Logical)
        regts[int(rd[1:])] = val1 << (val2 & 0x1F)
    elif funct3 == "101" and funct7 == "0000000":  # SRL (Shift Right Logical)
        regts[int(rd[1:])] = val1 >> (val2 & 0x1F)
    elif funct3 == "101" and funct7 == "0100000":  # SRA (Shift Right Arithmetic)
        regts[int(rd[1:])] = val1 >> (val2 & 0x1F) if val1 >= 0 else (val1 >> (val2 & 0x1F)) | (-(1 << (32 - (val2 & 0x1F))))
    
    print(f"Executed R-type: {rd} = {regts[int(rd[1:])]}")


# Initialize 32 registers (all set to 0)
regts = [0] * 32  
memory = {}  # Dictionary to simulate memory storage
pc = 0  # Program Counter (PC)

# Read machine code instructions from file
with open("/home/strangersagain/Downloads/Group_148/automatedTesting/tests/bin/simple/simple_6.txt", 'r') as f:
    # file_content = f.read()
    # print(file_content)
    for line in f:
        line=line.strip()#Whitespace characters include spaces, tabs (\t), newline characters (\n), carriage returns (\r), and vertical tabs (\v).
        print(line)
        opcode = line[25:]

        if opcode == "0110011":  # R 
            funct7 = line[:7]
            rs2 = "r" + str(int(line[7:12], 2))
            rs1 = "r" + str(int(line[12:17], 2))
            funct3 = line[17:20]
            rd = "r" + str(int(line[20:25], 2)) 
            print(f"funct7: {funct7}")
            print(f"rs2: {rs2}")
            print(f"rs1: {rs1}")
            print(f"funct3: {funct3}")
            print(f"rd: {rd}")
            print(f"opcode: {opcode}")
            execute_r_type(funct3, funct7, rs1, rs2, rd)
            print("- - - - -- - - - -- ")

        elif opcode == "0000011": # I
            imm = int(line[:12], 2) 
            rs1 = "r" + str(int(line[12:17], 2))  
            funct3 = line[17:20] 
            rd = "r" + str(int(line[20:25], 2))  
            print(f"imm: {imm}")
            print(f"rs1: {rs1}")
            print(f"funct3: {funct3}")
            print(f"rd: {rd}")
            print(f"opcode: {opcode}")
            print("- - - - -- - - - -- ")

        elif opcode == "0100011": # Store
            upper_imm = line[:7]
            rs2 = "r" + str(int(line[7:12], 2))
            rs1 = "r" + str(int(line[12:17], 2))
            funct3 = line[17:20]
            lower_imm = line[20:25]
            # Merge the immediate parts
            imm = int(upper_imm + lower_imm, 2)  # Full 12-bit immediate
            print(f"imm: {imm}")
            print(f"rs2: {rs2}")
            print(f"rs1: {rs1}")
            print(f"funct3: {funct3}")
            print(f"opcode: {opcode}")
            print("- - - - -- - - - -- ")
        
        elif opcode == "1100011": # Branch type
            imm_12 = line[0]  # Most significant bit (MSB)
            imm_10_5 = line[1:7]  # Bits 1-6
            rs2 = "r" + str(int(line[7:12], 2))
            rs1 = "r" + str(int(line[12:17], 2))
            funct3 = line[17:20]
            imm_4_1 = line[20:24]  # Bits 20-23
            imm_11 = line[24]  # Bit 24
            # Merge the immediate in the correct order
            imm = int(imm_12 + imm_11 + imm_10_5 + imm_4_1 + "0", 2)  # Shift left by 1 (as per RISC-V spec)        
            print(f"imm: {imm}")
            print(f"rs2: {rs2}")
            print(f"rs1: {rs1}")
            print(f"funct3: {funct3}")
            print(f"opcode: {opcode}")
            print("- - - - -- - - - -- ")

