def print_register_state():
    global regts, pc
    reg_values = [f"{reg:032b}" for reg in regts]
    print(f"{hex(pc)} {' '.join(reg_values)}")

def print_data_memory():
    global data_memory
    print("\nData Memory (after Virtual Halt):")
    for addr in range(DATA_MEMORY_START, DATA_MEMORY_END + 1, 4):
        value = data_memory.get(addr, 0)
        print(f"{value:032b}")
def load_program_memory(file_path):
    global program_memory, pc
    pc = PROGRAM_MEMORY_START  # Start at 0x00000000
    with open(file_path, 'r') as f:
        address = PROGRAM_MEMORY_START
        for line in f:
            line = line.strip()
            if len(line) == 32:  # Ensure it's a 32-bit instruction
                program_memory[address] = int(line, 2)  # Store as integer
                address += 4  # Instructions are 4 bytes apart
            if address > PROGRAM_MEMORY_END:
                raise ValueError("Program memory overflow!")
            
def sign_extend(value, bits):
    sign_bit = 1 << (bits - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)

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

def execute_i_type(funct3, imm, rs1, rd, opcode):
    global regts, data_memory, pc     
    val1 = regts[int(rs1[1:])]
    rd_idx = int(rd[1:])
    imm = sign_extend(imm, 12)  # Proper 12-bit sign extension

    if funct3 == "010" and opcode == "0000011":  # LW
        mem_addr = val1 + imm
        if DATA_MEMORY_START <= mem_addr <= DATA_MEMORY_END and mem_addr % 4 == 0:  # Word-aligned
            regts[rd_idx] = data_memory.get(mem_addr, 0)  # Default to 0 if uninitialized
            print(f"Executed LW: {rd} = MEM[{hex(mem_addr)}] = {regts[rd_idx]}")
        else:
            print(f"Error: Invalid memory address {hex(mem_addr)} for LW (range: {hex(DATA_MEMORY_START)}-{hex(DATA_MEMORY_END)})")
            return True  # Indicate error (optional)
        pc += 4
        return False
    elif funct3 == "000" and opcode == "0010011":  # ADDI
        regts[rd_idx] = val1 + imm
        print(f"Executed ADDI: {rd} = {val1} + {imm} = {regts[rd_idx]}")
        pc += 4
        return False
    elif funct3 == "000" and opcode == "1100111":  # JALR
        regts[rd_idx] = pc + 4
        pc = (val1 + imm) & ~1  # Ensure LSB is 0
        print(f"Executed JALR: {rd} = {pc + 4}, PC = {pc}")
        return True  # Jump taken
    
    pc += 4 # For other I-type instructions (if any)
    return False
    
# S-type execution
def execute_s_type(funct3, imm, rs1, rs2):
    global regts, stack_memory, data_memory, pc
    val1 = regts[int(rs1[1:])]
    val2 = regts[int(rs2[1:])]
    imm = sign_extend(imm, 12)

    if funct3 == "010":  # SW
        mem_addr = val1 + imm
        if STACK_MEMORY_START <= mem_addr <= STACK_MEMORY_END and mem_addr % 4 == 0:
            stack_memory[mem_addr] = val2 & 0xFFFFFFFF
            print(f"Executed SW (Stack): MEM[{hex(mem_addr)}] = {val2} (from {rs2})")
        elif DATA_MEMORY_START <= mem_addr <= DATA_MEMORY_END and mem_addr % 4 == 0:
            data_memory[mem_addr] = val2 & 0xFFFFFFFF
            print(f"Executed SW (Data): MEM[{hex(mem_addr)}] = {val2} (from {rs2})")
        else:
            print(f"Error: Invalid memory address {hex(mem_addr)} for SW")
        pc += 4
        return False

def execute_b_type(funct3, imm, rs1, rs2):
    global regts, pc  # Access the registers and program counter
    val1 = regts[int(rs1[1:])]
    val2 = regts[int(rs2[1:])]
    
    imm = sign_extend(imm, 13)  # 13-bit immediate (shifted left by 1)
    
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
    pc+=4
    return False  # PC was not modified

def execute_j_type(imm, rd):
    global regts, pc  # Access the registers and program counter
    
    imm = sign_extend(imm, 21)  # 21-bit immediate (shifted left by 1)
    rd_idx = int(rd[1:])

    regts[rd_idx] = pc + 4
    # Jump to target address    
    pc += (imm << 1) 
    
    print(f"Executed JAL: {rd} = {pc + 4}, PC = {pc}")
    return True  # PC was modified

# Memory initialization
PROGRAM_MEMORY_SIZE = 256  # 64 locations * 4 bytes = 256 bytes
STACK_MEMORY_SIZE = 128    # 32 locations * 4 bytes = 128 bytes
DATA_MEMORY_SIZE = 128     # 32 locations * 4 bytes = 128 bytes

PROGRAM_MEMORY_START = 0x00000000
STACK_MEMORY_START = 0x00000100
DATA_MEMORY_START = 0x00010000

PROGRAM_MEMORY_END = PROGRAM_MEMORY_START + PROGRAM_MEMORY_SIZE - 1  # 0x000000FF
STACK_MEMORY_END = STACK_MEMORY_START + STACK_MEMORY_SIZE - 1        # 0x0000017F
DATA_MEMORY_END = DATA_MEMORY_START + DATA_MEMORY_SIZE - 1          # 0x0001007F

# Memory dictionaries (address -> 32-bit value)
program_memory = {}  # For instructions
stack_memory = {}    # For stack operations
data_memory = {}     # For data storage (LW/SW)

# Initialize 32 registers (all set to 0)
regts = [0] * 32  
pc = 0  # Program Counter (PC)


# Read machine code instructions from file
with open("/home/strangersagain/Downloads/Group_148/automatedTesting/tests/bin/simple/simple_1.txt", 'r') as f:
    # file_content = f.read()
    # print(file_content)
    for line in f:
        line=line.strip()#Whitespace characters include spaces, tabs (\t), newline characters (\n), carriage returns (\r), and vertical tabs (\v).
        print(line)
        opcode = line[25:]
        if line=="00000000000000000000000001100011":
            print("Virtual halt encountered - stopping execution")
            break
        
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

        elif opcode == "0000011" or opcode == "0010011" or opcode == "1100111" : # I
            imm = int(line[:12], 2) 
            rs1 = "r" + str(int(line[12:17], 2))  
            funct3 = line[17:20] 
            rd = "r" + str(int(line[20:25], 2))  
            print(f"imm: {imm}")
            print(f"rs1: {rs1}")
            print(f"funct3: {funct3}")
            print(f"rd: {rd}")
            print(f"opcode: {opcode}")
            execute_i_type(funct3, imm, rs1, rd, opcode)
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
            # Merge the immediate correctly
            imm = int(imm_12 + imm_11 + imm_10_5 + imm_4_1 + "0", 2)  # Shift left by 1
    
            # Apply sign extension if negative
            if imm & (1 << 12):  # If 13th bit (MSB) is set
                imm -= (1 << 13)  # Convert to signed value
            print(f"imm: {imm}")
            print(f"rs2: {rs2}")
            print(f"rs1: {rs1}")
            print(f"funct3: {funct3}")
            print(f"opcode: {opcode}")
            execute_b_type(funct3, imm, rs1, rs2)
            print("- - - - -- - - - -- ")

        elif opcode == "1101111":  # J-Type (JAL)
            imm_20 = line[0]  # Most significant bit (MSB)
            imm_10_1 = line[1:11]  # Bits 1-10
            imm_11 = line[11]  # Bit 11
            imm_19_12 = line[12:20]  # Bits 12-19
            rd = "r" + str(int(line[20:25], 2))  # Destination register

            # Merge the immediate in the correct order (J-Type format)
            imm = int(imm_20 + imm_19_12 + imm_11 + imm_10_1 + "0", 2)  # Shift left by 1

            # Apply sign extension if negative
            if imm & (1 << 20):  # If 21st bit (MSB) is set
                imm -= (1 << 21)  # Convert to signed value

            print(f"imm: {imm}")
            print(f"rd: {rd}")
            print(f"opcode: {opcode}")

            execute_j_type(imm, rd)  
            print("- - - - -- - - - -- ")
            
