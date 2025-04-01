def execute_r_type(funct3, funct7, rs1, rs2, rd):
    global regts,pc  # Access the register list
    val1 = regts[int(rs1[1:])]  # Extract integer index
    val2 = regts[int(rs2[1:])]

    if funct3 == "000" and funct7 == "0000000":  # ADD 
        regts[int(rd[1:])] = val1 + val2
    elif funct3 == "000" and funct7 == "0100000":  # SUB okie2
        regts[int(rd[1:])] = val1 - val2
    elif funct3 == "010":  # SLT (Set Less Than)
        # If val1 is less than val2 when treated as signed numbers, set rd to 1, else 0
        regts[int(rd[1:])] = 1 if val1 < val2 else 0
    elif funct3 == "101" and funct7 == "0000000":  # SRL Shift Right Logical
        regts[int(rd[1:])] = val1 >> (val2 & 0x1F)
    elif funct3 == "110" and funct7 == "0000000":  # OR                         
        regts[int(rd[1:])] = val1 | val2
    elif funct3 == "111" and funct7 == "0000000":  # AND                        
        regts[int(rd[1:])] = val1 & val2        
    pc+=4;                                      # cookie
    print(f"Executed R-type: {rd} = {regts[int(rd[1:])]}")

def execute_i_type(funct3, imm, rs1, rd):
    global regts, memory, pc  # Access the registers, memory, and program counter
    val1 = regts[int(rs1[1:])]  # Extract value from source register
    
    # Sign extend the immediate value (12 bits)
    if imm & 0x800:  # Check if the MSB is 1 (negative number)
        imm = imm | (~0xFFF)  # Sign extend by setting all upper bits to 1
    
    if funct3 == "010" and opcode == "0000011":  # LW
        # Calculate memory address
        mem_addr = val1 + imm
        # Load word from memory
        regts[int(rd[1:])] = memory.get(mem_addr, 0)  # Load from memory, default 0 if not found
        print(f"Executed LW: {rd} = MEM[{mem_addr}] = {regts[int(rd[1:])]}")

    elif funct3 == "000" and opcode == "0010011":  # ADDI
        regts[int(rd[1:])] = val1 + imm
        print(f"Executed ADDI: {rd} = {val1} + {imm} = {regts[int(rd[1:])]}")
    
    elif funct3 == "000" and opcode == "1100111":  # JALR
        # Save return address
        regts[int(rd[1:])] = pc + 4
        # Jump to target address (making sure the LSB is 0)
        pc = (val1 + imm) & ~1
        print(f"Executed JALR: {rd} = {pc + 4}, PC = {pc}")
        return True  # Indicate PC was modified
    
    pc+=4                       # cookie
    return False  # PC was not modified

def execute_s_type(funct3, imm, rs1, rs2):
    global regts, memory  # Access the registers and memory
    val1 = regts[int(rs1[1:])]  # Base address
    val2 = regts[int(rs2[1:])]  # Data to store
    
    # Sign extend the immediate value
    if imm & 0x800:  # Check if the MSB is 1 (negative number)
        imm = imm | (~0xFFF)  # Sign extend by setting all upper bits to 1
    
    if funct3 == "010":  # SW
        # Calculate memory address
        mem_addr = val1 + imm
        # Store word in memory
        memory[mem_addr] = val2
    pc+=4;
    print(f"Executed SW: MEM[{mem_addr}] = {val2}")

def execute_b_type(funct3, imm, rs1, rs2):
    global regts, pc  # Access the registers and program counter
    val1 = regts[int(rs1[1:])]
    val2 = regts[int(rs2[1:])]
    
    # Sign extend the immediate value
    if imm & 0x1000:  # Check if the MSB is 1 (negative number)
        imm = imm | (~0x1FFF)  # Sign extend
    
    if funct3 == "000":  # BEQ
        if val1 == val2:
            pc+=imm
            print(f"Executed BEQ: Branch taken to PC = {pc}")
            return True  # PC was modified
        print(f"Executed BEQ: Branch not taken")
    
    elif funct3 == "001":  # BNE
        if val1 != val2:
            pc+=imm
            print(f"Executed BNE: Branch taken to PC = {pc}")
            return True  # PC was modified
        print(f"Executed BNE: Branch not taken")
    pc+=4;
    return False  # PC was not modified

def execute_j_type(imm, rd):
    global regts, pc  # Access the registers and program counter
    
    # Sign extend the immediate value
    if imm & 0x100000:  # Check if the MSB is 1 (negative number)
        imm = imm | (~0x1FFFFF)  # Sign extend
    
    # Save return address
    regts[int(rd[1:])] = pc + 4
    
    # Jump to target address
    pc+=imm
    
    print(f"Executed JAL: {rd} = {pc + 4}, PC = {pc}")
    return True  # PC was modified


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
            execute_i_type(funct3, imm, rs1, rd)
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
            execute_s_type(funct3, imm, rs1, rs2)
            print("- - - - -- - - - -- ")
        
        elif opcode == "1100011": # Branch type
            imm_12 = line[0]  # Most significant bit (MSB)
            imm_10_5 = line[1:7]  # Bits 1-6
            rs2 = "r" + str(int(line[7:12], 2))
            rs1 = "r" + str(int(line[12:17], 2))
            funct3 = line[17:20]
            imm_4_1 = line[20:24]  # Bits 20-23
            imm_11 = line[24]  # Bit 24
            execute_b_type(funct3, imm, rs1, rs2)
            # Merge the immediate in the correct order
            imm = int(imm_12 + imm_11 + imm_10_5 + imm_4_1 + "0", 2)  # Shift left by 1 (as per RISC-V spec)        
            print(f"imm: {imm}")
            print(f"rs2: {rs2}")
            print(f"rs1: {rs1}")
            print(f"funct3: {funct3}")
            print(f"opcode: {opcode}")
            execute_j_type(imm, rd)
            print("- - - - -- - - - -- ")

