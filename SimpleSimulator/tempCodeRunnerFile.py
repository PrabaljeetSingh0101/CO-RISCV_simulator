def print_register_state():
    global regts, pc
    reg_values = [f"{reg:032b}" for reg in regts]
    output_line = ' '.join(reg_values)
    # Write to output file
    with open(output_file_path, 'a') as f:
        f.write(output_line + '\n')
def print_data_memory():
    global data_memory
    # Write memory contents to output file
    with open(output_file_path, 'a') as f:
        for addr in range(DATA_MEMORY_START, DATA_MEMORY_END + 1, 4):
            value = data_memory.get(addr, 0)
            f.write(f"0x{addr:08x}:0b{value:032b}\n")
            
def load_program_memory(file_path):
    global program_memory, pc
    pc = PROGRAM_MEMORY_START
    print(f"Loading program from {file_path}")
    try:
        with open(file_path, 'r') as f:
            address = PROGRAM_MEMORY_START
            line_count = 0
            for line in f:
                line = line.strip()
                line_count += 1
                print(f"Line {line_count}: {line}")
                if line.startswith("0b") and len(line) == 34:  # 0b + 32 bits
                    program_memory[address] = int(line[2:], 2)
                    print(f"Loaded instruction at {hex(address)}: {line}")
                    address += 4
                elif line.startswith("0x"):  # Memory address format
                    parts = line.split(":")
                    if len(parts) == 2:
                        addr = int(parts[0], 16)
                        if parts[1].startswith("0b"):
                            value = int(parts[1][2:], 2)
                            data_memory[addr] = value
                            print(f"Loaded data at {hex(addr)}: {parts[1]}")
                if address > PROGRAM_MEMORY_END:
                    raise ValueError("Program memory overflow!")
        print(f"Program loaded: {len(program_memory)} instructions")
    except Exception as e:
        print(f"Error loading program: {e}")

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
    print_register_state()

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
        print_register_state()
        return False
    elif funct3 == "000" and opcode == "0010011":  # ADDI
        regts[rd_idx] = val1 + imm
        print(f"Executed ADDI: {rd} = {val1} + {imm} = {regts[rd_idx]}")
        pc += 4
        print_register_state()
        return False
    elif funct3 == "000" and opcode == "1100111":  # JALR
        regts[rd_idx] = pc + 4
        pc = (val1 + imm) & ~1  # Ensure LSB is 0
        print(f"Executed JALR: {rd} = {pc + 4}, PC = {pc}")
        print_register_state()
        return True  # Jump taken
    
    pc += 4 # For other I-type instructions (if any)
    print_register_state()
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
        print_register_state()
        return False

def execute_b_type(funct3, imm, rs1, rs2):
    global regts, pc  # Access the registers and program counter
    val1 = regts[int(rs1[1:])]
    val2 = regts[int(rs2[1:])]
    
    imm = sign_extend(imm, 13)  # 13-bit immediate (shifted left by 1)
    
       # Check for Virtual Halt instruction (beq zero,zero,0)
    if funct3 == "000" and rs1 == "r0" and rs2 == "r0" and imm == 0:
        print("Virtual Halt encountered - stopping execution")
        print_register_state()
        print_data_memory()
        return True  # Special halt return code
    
    if funct3 == "000":  # BEQ
        if val1 == val2:
            pc+=imm
            print(f"Executed BEQ: Branch taken to PC = {pc}")
            print_register_state()
            return True  # PC was modified
        print(f"Executed BEQ: Branch not taken")
    
    elif funct3 == "001":  # BNE
        if val1 != val2:
            pc+=imm
            print(f"Executed BNE: Branch taken to PC = {pc}")
            print_register_state()
            return True  # PC was modified
        print(f"Executed BNE: Branch not taken")
    pc+=4
    print_register_state()
    return False  # PC was not modified

def execute_j_type(imm, rd):
    global regts, pc  # Access the registers and program counter
    
    imm = sign_extend(imm, 21)  # 21-bit immediate (shifted left by 1)
    rd_idx = int(rd[1:])

    regts[rd_idx] = pc + 4
    # Jump to target address    
    pc += imm
    
    print(f"Executed JAL: {rd} = {pc + 4}, PC = {pc}")
    print_register_state()
    return True  # PC was modifiedfied

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


def simulate(input_file_path, output_file_path):
    global program_memory, pc, regts, data_memory, stack_memory
    # Memory dictionaries (address -> 32-bit value)
    program_memory = {}  # For instructions
    stack_memory = {}    # For stack operations
    data_memory = {}     # For data storage (LW/SW)

    # Initialize 32 registers (all set to 0)
    regts = [0] * 32  
    pc = 0  # Program Counter (PC)
   # Clear output file
    with open(output_file_path, 'w') as f:
        f.write("")  # Clear the file content
    
    # Load program
    load_program_memory(input_file_path)
    
    # Execute instructions
    halt_encountered = False
    while not halt_encountered and pc <= PROGRAM_MEMORY_END:
        if pc % 4 != 0:
            print(f"Error: Misaligned PC {hex(pc)}")
            break
            
        instruction = program_memory.get(pc, 0)
        if instruction == 0:
            print(f"Warning: No instruction at {hex(pc)}")
            break
            
        instruction_bin = f"{instruction:032b}"
        opcode = instruction_bin[25:]
        
        # Check for Virtual Halt (beq zero,zero,0)
        if instruction_bin == "00000000000000000000000001100011":
            print("Virtual Halt encountered - stopping execution")
            print_register_state()
            print_data_memory()
            halt_encountered = True
            break
        
        print(f"Executing instruction at {hex(pc)}: {instruction_bin}")
        
        if opcode == "0110011":  # R 
            funct7 = instruction_bin[:7]
            rs2 = "r" + str(int(instruction_bin[7:12], 2))
            rs1 = "r" + str(int(instruction_bin[12:17], 2))
            funct3 = instruction_bin[17:20]
            rd = "r" + str(int(instruction_bin[20:25], 2)) 
            execute_r_type(funct3, funct7, rs1, rs2, rd)

        elif opcode == "0000011" or opcode == "0010011" or opcode == "1100111": # I
            imm = int(instruction_bin[:12], 2) 
            rs1 = "r" + str(int(instruction_bin[12:17], 2))  
            funct3 = instruction_bin[17:20] 
            rd = "r" + str(int(instruction_bin[20:25], 2))  
            execute_i_type(funct3, imm, rs1, rd, opcode)

        elif opcode == "0100011": # Store
            upper_imm = instruction_bin[:7]
            rs2 = "r" + str(int(instruction_bin[7:12], 2))
            rs1 = "r" + str(int(instruction_bin[12:17], 2))
            funct3 = instruction_bin[17:20]
            lower_imm = instruction_bin[20:25]
            # Merge the immediate parts
            imm = int(upper_imm + lower_imm, 2)  # Full 12-bit immediate
            execute_s_type(funct3, imm, rs1, rs2)
        
        elif opcode == "1100011": # Branch type
            imm_12 = instruction_bin[0]  # Most significant bit (MSB)
            imm_10_5 = instruction_bin[1:7]  # Bits 1-6
            rs2 = "r" + str(int(instruction_bin[7:12], 2))
            rs1 = "r" + str(int(instruction_bin[12:17], 2))
            funct3 = instruction_bin[17:20]
            imm_4_1 = instruction_bin[20:24]  # Bits 20-23
            imm_11 = instruction_bin[24]  # Bit 24
            # Merge the immediate correctly
            imm = int(imm_12 + imm_11 + imm_10_5 + imm_4_1 + "0", 2)  # Shift left by 1
    
            # Apply sign extension if negative
            if imm & (1 << 12):  # If 13th bit (MSB) is set
                imm -= (1 << 13)  # Convert to signed value
                
            result = execute_b_type(funct3, imm, rs1, rs2)
            if result and rs1 == "r0" and rs2 == "r0" and imm == 0:
                halt_encountered = True
                break

        elif opcode == "1101111":  # J-Type (JAL)
            imm_20 = instruction_bin[0]  # Most significant bit (MSB)
            imm_10_1 = instruction_bin[1:11]  # Bits 1-10
            imm_11 = instruction_bin[11]  # Bit 11
            imm_19_12 = instruction_bin[12:20]  # Bits 12-19
            rd = "r" + str(int(instruction_bin[20:25], 2))  # Destination register

            # Merge the immediate in the correct order (J-Type format)
            imm = int(imm_20 + imm_19_12 + imm_11 + imm_10_1 + "0", 2)  # Shift left by 1

            # Apply sign extension if negative
            if imm & (1 << 20):  # If 21st bit (MSB) is set
                imm -= (1 << 21)  # Convert to signed value

            execute_j_type(imm, rd)
        
        else:
            print(f"Error: Unknown opcode {opcode} at {hex(pc)}")
            break
    
    if not halt_encountered:
        print("Warning: Program ended without encountering Virtual Halt")

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
    
# File paths (you should replace these with command line arguments)
input_file_path = "/home/strangersagain/Downloads/Group_148/automatedTesting/tests/bin/simple/simple_1.txt"
output_file_path = "/home/strangersagain/Downloads/Group_148/trace_output.txt"

# Run the simulator
if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        input_file_path = sys.argv[1]
        output_file_path = sys.argv[2]
        
    print(f"Running simulator with input {input_file_path} and output {output_file_path}")
    simulate(input_file_path, output_file_path)
