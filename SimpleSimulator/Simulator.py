def print_register_state(pc, regts, output_file_path):
    # Convert PC to binary with 0b prefix
    pc_bin = f"0b{pc:032b}" if pc >= 0 else f"0b{(1 << 32) + pc:032b}"
    
    # Convert registers to binary with 0b prefix
    reg_values = []
    for reg in regts:
        if reg >= 0:
            reg_bin = f"0b{reg:032b}"
        else:
            reg_bin = f"0b{(1 << 32) + reg:032b}"
        reg_values.append(reg_bin)
    
    # Write to output file
    with open(output_file_path, 'a') as f:
        f.write(f"{pc_bin} {' '.join(reg_values)}\n")

def print_data_memory(data_memory, output_file_path):
    # Write memory contents to output file for data memory range
    with open(output_file_path, 'a') as f:
        for addr in range(DATA_MEMORY_START, DATA_MEMORY_END + 1, 4):
            value = data_memory.get(addr, 0)
            if value >= 0:
                value_bin = f"0b{value:032b}"
            else:
                value_bin = f"0b{(1 << 32) + value:032b}"
            # Use uppercase X for hexadecimal format
            f.write(f"0x{addr:08X}:{value_bin}\n")

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
                
                # Check if line is a 32-bit binary number (without 0b prefix)
                if len(line) == 32 and all(bit in '01' for bit in line):
                    program_memory[address] = int(line, 2)
                    print(f"Loaded instruction at {hex(address)}: {line}")
                    address += 4
                # Original handling for 0b prefix
                elif line.startswith("0b") and len(line) == 34:  # 0b + 32 bits
                    program_memory[address] = int(line[2:], 2)
                    print(f"Loaded instruction at {hex(address)}: {line}")
                    address += 4
                # Memory address format
                elif line.startswith("0x"):
                    parts = line.split(":")
                    if len(parts) == 2:
                        addr = int(parts[0], 16)
                        if parts[1].startswith("0b"):
                            value = int(parts[1][2:], 2)
                            data_memory[addr] = value
                            print(f"Loaded data at {hex(addr)}: {parts[1]}")
                        else:
                            # Handle case where value doesn't have 0b prefix
                            value = int(parts[1], 2)
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
# Update execution functions to use the new print_register_state
def execute_r_type(funct3, funct7, rs1, rs2, rd):
    global regts, pc
    val1 = regts[int(rs1[1:])]
    val2 = regts[int(rs2[1:])]
    if funct3 == "000" and funct7 == "0000000":  # ADD
        regts[int(rd[1:])] = val1 + val2
    elif funct3 == "000" and funct7 == "0100000":  # SUB
        regts[int(rd[1:])] = val1 - val2
    elif funct3 == "010":  # SLT
        regts[int(rd[1:])] = 1 if val1 < val2 else 0
    elif funct3 == "101" and funct7 == "0000000":  # SRL
        regts[int(rd[1:])] = val1 >> (val2 & 0x1F)
    elif funct3 == "110" and funct7 == "0000000":  # OR
        regts[int(rd[1:])] = val1 | val2
    elif funct3 == "111" and funct7 == "0000000":  # AND
        regts[int(rd[1:])] = val1 & val2
    print(f"Executed R-type: {rd} = {regts[int(rd[1:])]}")
    pc += 4
    print_register_state(pc, regts, output_file_path)

# Update execute_s_type to better handle stack operations
def execute_s_type(funct3, imm, rs1, rs2):
    global regts, stack_memory, data_memory, pc
    val1 = regts[int(rs1[1:])]
    val2 = regts[int(rs2[1:])]
    imm = sign_extend(imm, 12)
    
    if funct3 == "010":  # SW
        mem_addr = val1 + imm
        
        # Check for stack operations (typically using sp register r2)
        if int(rs1[1:]) == 2:
            print(f"Stack operation detected: SW using stack pointer")
            
        if STACK_MEMORY_START <= mem_addr <= STACK_MEMORY_END and mem_addr % 4 == 0:
            stack_memory[mem_addr] = val2 & 0xFFFFFFFF
            print(f"Executed SW (Stack): MEM[{hex(mem_addr)}] = {val2}")
        elif DATA_MEMORY_START <= mem_addr <= DATA_MEMORY_END and mem_addr % 4 == 0:
            data_memory[mem_addr] = val2 & 0xFFFFFFFF
            print(f"Executed SW (Data): MEM[{hex(mem_addr)}] = {val2}")
        else:
            print(f"Error: Invalid memory address {hex(mem_addr)} for SW")
            
    pc += 4
    print_register_state(pc, regts, output_file_path)
    return False

# Update execute_i_type to handle stack operations better
def execute_i_type(funct3, imm, rs1, rd, opcode):
    global regts, data_memory, stack_memory, pc
    val1 = regts[int(rs1[1:])]
    rd_idx = int(rd[1:])
    imm = sign_extend(imm, 12)
    
    # Check for stack operations
    if int(rs1[1:]) == 2:
        print(f"Stack operation detected: Using stack pointer as base address")
    
    if funct3 == "010" and opcode == "0000011":  # LW
        mem_addr = val1 + imm
        if STACK_MEMORY_START <= mem_addr <= STACK_MEMORY_END and mem_addr % 4 == 0:
            regts[rd_idx] = stack_memory.get(mem_addr, 0)
            print(f"Executed LW from Stack: {rd} = MEM[{hex(mem_addr)}] = {regts[rd_idx]}")
        elif DATA_MEMORY_START <= mem_addr <= DATA_MEMORY_END and mem_addr % 4 == 0:
            regts[rd_idx] = data_memory.get(mem_addr, 0)
            print(f"Executed LW from Data: {rd} = MEM[{hex(mem_addr)}] = {regts[rd_idx]}")
        else:
            print(f"Error: Invalid memory address {hex(mem_addr)} for LW")
            return True
    elif funct3 == "000" and opcode == "0010011":  # ADDI
        # Check if this is updating the stack pointer
        if rd_idx == 2:
            print(f"Stack pointer operation: ADDI sp, {val1}, {imm}")
            
        regts[rd_idx] = val1 + imm
        print(f"Executed ADDI: {rd} = {val1} + {imm} = {regts[rd_idx]}")
    elif funct3 == "000" and opcode == "1100111":  # JALR
        regts[rd_idx] = pc + 4
        pc = (val1 + imm) & ~1
        print(f"Executed JALR: {rd} = {pc + 4}, PC = {pc}")
        print_register_state(pc, regts, output_file_path)
        return True
    
    pc += 4
    print_register_state(pc, regts, output_file_path)
    return False

def execute_b_type(funct3, imm, rs1, rs2):
    global regts, pc
    val1 = regts[int(rs1[1:])]
    val2 = regts[int(rs2[1:])]
    imm = sign_extend(imm, 13)
    
    # Virtual halt check - BEQ r0, r0, 0
    if funct3 == "000" and rs1 == "r0" and rs2 == "r0" and imm == 0:
        pc += 4  # Important: increment PC before halting
        print(f"Virtual Halt encountered - stopping execution")
        print_register_state(pc, regts, output_file_path)
        print_data_memory(data_memory, output_file_path)
        return True  # Return True to indicate halt
        
    if funct3 == "000":  # BEQ
        if val1 == val2:
            pc += imm
            print(f"Executed BEQ: Branch taken to PC = {pc}")
            print_register_state(pc, regts, output_file_path)
            return True
        print(f"Executed BEQ: Branch not taken")
    elif funct3 == "001":  # BNE
        if val1 != val2:
            pc += imm
            print(f"Executed BNE: Branch taken to PC = {pc}")
            print_register_state(pc, regts, output_file_path)
            return True
        print(f"Executed BNE: Branch not taken")
    
    pc += 4
    print_register_state(pc, regts, output_file_path)
    return False
def execute_j_type(imm, rd):
    global regts, pc
    imm = sign_extend(imm, 21)
    rd_idx = int(rd[1:])
    regts[rd_idx] = pc + 4
    pc += imm
    print(f"Executed JAL: {rd} = {pc + 4}, PC = {pc}")
    print_register_state(pc, regts, output_file_path)
    return True
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
    
    # Initialize stack pointer (r2) to the top of stack memory
    regts[2] = STACK_MEMORY_START + STACK_MEMORY_SIZE - 4  # Point to the last valid word in stack
    
    pc = PROGRAM_MEMORY_START  # Start at 0x00000000
    
    # Clear output file
    with open(output_file_path, 'w') as f:
        f.write("")  # Clear the file content
    
    # Load program
    load_program_memory(input_file_path)
    
    # Print initial register state including initialized stack pointer
    print_register_state(pc, regts, output_file_path)
    
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
        
        print(f"Executing instruction at {hex(pc)}: {instruction_bin}")
        
        # Special handling for r0 - always keep it at 0
        regts[0] = 0
        
        if opcode == "0110011":  # R-type
            funct7 = instruction_bin[:7]
            rs2 = "r" + str(int(instruction_bin[7:12], 2))
            rs1 = "r" + str(int(instruction_bin[12:17], 2))
            funct3 = instruction_bin[17:20]
            rd = "r" + str(int(instruction_bin[20:25], 2)) 
            execute_r_type(funct3, funct7, rs1, rs2, rd)
        
        elif opcode in ["0000011", "0010011", "1100111"]:  # I-type
            imm_str = instruction_bin[:12]
            imm = int(imm_str, 2)
            if imm_str[0] == '1':  # Check if sign bit is set
                imm = sign_extend(imm, 12)
            rs1 = "r" + str(int(instruction_bin[12:17], 2))
            funct3 = instruction_bin[17:20]
            rd = "r" + str(int(instruction_bin[20:25], 2))
            if execute_i_type(funct3, imm, rs1, rd, opcode):
                continue  # JALR changed PC, skip increment
                
        elif opcode == "0100011":  # S-type
            upper_imm = instruction_bin[:7]
            rs2 = "r" + str(int(instruction_bin[7:12], 2))
            rs1 = "r" + str(int(instruction_bin[12:17], 2))
            funct3 = instruction_bin[17:20]
            lower_imm = instruction_bin[20:25]
            imm_str = upper_imm + lower_imm
            imm = int(imm_str, 2)
            if imm_str[0] == '1':  # Check if sign bit is set
                imm = sign_extend(imm, 12)
            if execute_s_type(funct3, imm, rs1, rs2):
                continue  # If function handled PC update, skip increment
        
        elif opcode == "1100011":  # B-type
            imm_12 = instruction_bin[0]
            imm_10_5 = instruction_bin[1:7]
            rs2 = "r" + str(int(instruction_bin[7:12], 2))
            rs1 = "r" + str(int(instruction_bin[12:17], 2))
            funct3 = instruction_bin[17:20]
            imm_4_1 = instruction_bin[20:24]
            imm_11 = instruction_bin[24]
            imm_str = imm_12 + imm_11 + imm_10_5 + imm_4_1 + "0"
            imm = int(imm_str, 2)
            if imm_str[0] == '1':  # Check if sign bit is set
                imm = sign_extend(imm, 13)  # B-type immediates are 13 bits
            
            branch_taken = execute_b_type(funct3, imm, rs1, rs2)
            if branch_taken:
                # The execute_b_type function already handles PC updates and virtual halt
                if funct3 == "000" and rs1 == "r0" and rs2 == "r0" and imm == 0:
                    halt_encountered = True
                continue  # Skip PC increment
                
        elif opcode == "1101111":  # J-type (JAL)
            imm_20 = instruction_bin[0]
            imm_10_1 = instruction_bin[1:11]
            imm_11 = instruction_bin[11]
            imm_19_12 = instruction_bin[12:20]
            rd = "r" + str(int(instruction_bin[20:25], 2))
            imm_str = imm_20 + imm_19_12 + imm_11 + imm_10_1 + "0"
            imm = int(imm_str, 2)
            if imm_str[0] == '1':  # Check if sign bit is set
                imm = sign_extend(imm, 21)  # J-type immediates are 21 bits
            execute_j_type(imm, rd)
            continue  # Skip PC increment as execute_j_type handles it
            
        else:
            print(f"Error: Unknown opcode {opcode} at {hex(pc)}")
            break
        
        # Ensure r0 is always 0
        regts[0] = 0
    
    if not halt_encountered:
        print("Warning: Program ended without encountering Virtual Halt")
    
    # Print final data memory state
    print_data_memory(data_memory, output_file_path)
    
    
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