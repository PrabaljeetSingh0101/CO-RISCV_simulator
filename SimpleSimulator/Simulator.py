program_memory_start = 0
program_memory_size = 256
program_memory_end = program_memory_start + program_memory_size - 1

stack_memory_start = 0x100
stack_memory_size = 128  
stack_memory_end = stack_memory_start + stack_memory_size - 1

data_memory_start = 0x10000
data_memory_size = 128
data_memory_end = data_memory_start + data_memory_size - 1

all_registers = [0] * 32
program_counter = program_memory_start
program_instructions = {}  
stack_area = {}  
data_area = {}  

def make_number_correct(number, bits):
    sign_bit_pos = bits - 1
    sign_bit_value = 1 << sign_bit_pos
    return (number & (sign_bit_value - 1)) - (number & sign_bit_value)


def write_registers_to_file(pc_value, all_regs, file_to_write):
    
    pc_binary = "0b" + format(pc_value, '032b')
    registers_in_binary = []
    for r in all_regs:
        if r >= 0:
            reg_binary = "0b" + format(r, '032b')
        else:
            reg_binary = "0b" + format((1 << 32) + r, '032b')
        registers_in_binary.append(reg_binary)
    
    my_file = open(file_to_write, 'a')
    my_file.write(pc_binary + " " + " ".join(registers_in_binary) + "\n")
    my_file.close()

def write_memory_to_file(memory_data, file_to_write):
    my_file = open(file_to_write, 'a')
    
    address = data_memory_start
    while address <= data_memory_end:
        value = memory_data.get(address, 0)
        
        if value >= 0:
            value_binary = "0b" + format(value, '032b')
        else:
            value_binary = "0b" + format((1 << 32) + value, '032b')
        
        my_file.write("0x" + format(address, '08X') + ":" + value_binary + "\n")
        address = address + 4
    
    my_file.close()

def load_program_from_file(file_name):
    global program_instructions, data_area
    
    print("Loading program from file: " + file_name)
    
    try:
        my_file = open(file_name, 'r')
        current_address = program_memory_start
        line_number = 0
        
        for each_line in my_file:
            each_line = each_line.strip()
            line_number = line_number + 1
            print("Line " + str(line_number) + ": " + each_line)
            
            program_instructions[current_address] = int(each_line, 2)
            print("Loaded instruction at " + hex(current_address) + ": " + each_line)
            current_address = current_address + 4
            
            if current_address > program_memory_end:          
                print("Error: Too many instructions for program memory!")
                break
                
        my_file.close()
        print("Program loaded: " + str(len(program_instructions)) + " instructions")
        
    except Exception as e:
        print("Error while loading program: " + str(e))

def do_r_type_instruction(func3, func7, rs1, rs2, rd):
    global all_registers, program_counter, output_file
    
    value1 = all_registers[int(rs1[1:])]
    value2 = all_registers[int(rs2[1:])]
    
    if func3 == "000" and func7 == "0000000":  # ADD
        all_registers[int(rd[1:])] = value1 + value2
        print("Did ADD: " + rd + " = " + str(value1) + " + " + str(value2) + " = " + str(all_registers[int(rd[1:])]))
    elif func3 == "000" and func7 == "0100000":  # SUB
        all_registers[int(rd[1:])] = value1 - value2
        print("Did SUB: " + rd + " = " + str(value1) + " - " + str(value2) + " = " + str(all_registers[int(rd[1:])]))
    elif func3 == "010":  # SLT
        all_registers[int(rd[1:])] = 1 if value1 < value2 else 0
        print("Did SLT: " + rd + " = 1 if " + str(value1) + " < " + str(value2) + " else 0 = " + str(all_registers[int(rd[1:])]))
    elif func3 == "101" and func7 == "0000000":  # SRL
        all_registers[int(rd[1:])] = value1 >> (value2 & 0x1F)
        print("Did SRL: " + rd + " = " + str(value1) + " >> " + str(value2 & 0x1F) + " = " + str(all_registers[int(rd[1:])]))
    elif func3 == "110" and func7 == "0000000":  # OR
        all_registers[int(rd[1:])] = value1 | value2
        print("Did OR: " + rd + " = " + str(value1) + " | " + str(value2) + " = " + str(all_registers[int(rd[1:])]))
    elif func3 == "111" and func7 == "0000000":  # AND
        all_registers[int(rd[1:])] = value1 & value2
        print("Did AND: " + rd + " = " + str(value1) + " & " + str(value2) + " = " + str(all_registers[int(rd[1:])]))
    
    program_counter = program_counter + 4
    write_registers_to_file(program_counter, all_registers, output_file)

def do_s_type_instruction(func3, immediate, rs1, rs2):
    global all_registers, program_counter, stack_area, data_area, output_file
    
    base_addr = all_registers[int(rs1[1:])]
    value = all_registers[int(rs2[1:])]
    immediate = make_number_correct(immediate, 12)
    
    if func3 == "010":  # SW (store word)
        memory_address = base_addr + immediate
        
        if int(rs1[1:]) == 2:
            print("Storing to stack memory")
        
        if stack_memory_start <= memory_address <= stack_memory_end and memory_address % 4 == 0:
            stack_area[memory_address] = value & 0xFFFFFFFF
            print("Did SW (Stack): Memory[" + hex(memory_address) + "] = " + str(value))
        elif data_memory_start <= memory_address <= data_memory_end and memory_address % 4 == 0:
            data_area[memory_address] = value & 0xFFFFFFFF
            print("Did SW (Data): Memory[" + hex(memory_address) + "] = " + str(value))
        else:
            print("Error: Bad memory address " + hex(memory_address) + " for SW")
    
    program_counter = program_counter + 4
    write_registers_to_file(program_counter, all_registers, output_file)
    return False

def do_i_type_instruction(func3, immediate, rs1, rd, op):
    global all_registers, program_counter, data_area, stack_area, output_file
    
    value1 = all_registers[int(rs1[1:])]
    rd_num = int(rd[1:])
    immediate = make_number_correct(immediate, 12)
    
    
    if int(rs1[1:]) == 2:
        print("Stack operation: Using stack pointer as base")
    
    if func3 == "010" and op == "0000011":  # LW (load word)
        memory_address = value1 + immediate
        
        if stack_memory_start <= memory_address <= stack_memory_end and memory_address % 4 == 0:
            if rd_num != 0:  # Don't update register 0
                all_registers[rd_num] = stack_area.get(memory_address, 0)
            print("Did LW from Stack: " + rd + " = Memory[" + hex(memory_address) + "] = " + str(stack_area.get(memory_address, 0)))
        elif data_memory_start <= memory_address <= data_memory_end and memory_address % 4 == 0:
            if rd_num != 0:  
                all_registers[rd_num] = data_area.get(memory_address, 0)
            print("Did LW from Data: " + rd + " = Memory[" + hex(memory_address) + "] = " + str(data_area.get(memory_address, 0)))
        else:
            print("Error: Bad memory address " + hex(memory_address) + " for LW")
            return True
            
    elif func3 == "000" and op == "0010011":  # ADDI 
        if rd_num == 2:
            print("Stack pointer changing: ADDI sp, " + str(value1) + ", " + str(immediate))
        
        if rd_num != 0:  # Don't update register 0
            all_registers[rd_num] = value1 + immediate
        print("Did ADDI: " + rd + " = " + str(value1) + " + " + str(immediate) + " = " + str(value1 + immediate))
        
    elif func3 == "000" and op == "1100111":  # JALR (jump and link register)
        target_address = (value1 + immediate) & ~1
        
        if rd_num != 0:
            all_registers[rd_num] = program_counter + 4
            print("Did JALR: " + rd + " = " + str(program_counter + 4) + ", PC = " + str(target_address))
        else:
            print("Did JALR with r0: PC = " + str(target_address) + " (r0 stays 0)")
        
        all_registers[0] = 0         # Make sure r0 is 0
        
        program_counter = target_address
        write_registers_to_file(program_counter, all_registers, output_file)
        return True
    
    all_registers[0] = 0
    
    program_counter = program_counter + 4
    write_registers_to_file(program_counter, all_registers, output_file)
    return False

def do_b_type_instruction(func3, immediate, rs1, rs2):
    global all_registers, program_counter, output_file

    value1 = all_registers[int(rs1[1:])] 
    value2 = all_registers[int(rs2[1:])]
    immediate = make_number_correct(immediate, 13)

    if func3 == "000" and rs1 == "r0" and rs2 == "r0" and immediate == 0:
        write_registers_to_file(program_counter, all_registers, output_file)
        print("Virtual Halt found, Stopping program")
        return True
    
    if func3 == "000":  # BEQ (branch if equal)
        if value1 == value2:
            program_counter = program_counter + immediate
            print("Did BEQ: Branch taken to PC = " + str(program_counter))
            write_registers_to_file(program_counter, all_registers, output_file)
            return True
        print("Did BEQ: Branch not taken")
        
    elif func3 == "001":  # BNE - branch if not equal
        if value1 != value2:
            program_counter = program_counter + immediate
            print("Did BNE: Branch taken to PC = " + str(program_counter))
            write_registers_to_file(program_counter, all_registers, output_file)
            return True
        print("Did BNE: Branch not taken")
    
    program_counter = program_counter + 4
    write_registers_to_file(program_counter, all_registers, output_file)
    return False

def do_j_type_instruction(immediate, rd):
    global all_registers, program_counter, output_file
    
    immediate = make_number_correct(immediate, 21)
    rd_num = int(rd[1:])
    
    all_registers[rd_num] = program_counter + 4
    
    program_counter = program_counter + immediate
    
    print("Did JAL: " + rd + " = " + str(program_counter + 4) + ", PC = " + str(program_counter))
    write_registers_to_file(program_counter, all_registers, output_file)
    return True

def run_risc_v_simulation(input_file, output_file):
    global all_registers, program_counter, program_instructions, stack_area, data_area

    # Set stack pointer (r2) to point to top of stack
    all_registers[2] = stack_memory_start + stack_memory_size - 4
    
    open(output_file, 'w').close()

    load_program_from_file(input_file)
    

    # Main execution loop
    found_halt = False
    while not found_halt and program_counter <= program_memory_end:

        if program_counter % 4 != 0:
            print("Error: PC not aligned: " + hex(program_counter))
            break
        
        instruction = program_instructions.get(program_counter, 0)
        if instruction == 0:
            print("Warning: No instruction at " + hex(program_counter))
            break
        
        # convert to binary string
        instruction_binary = format(instruction, '032b')
        opcode = instruction_binary[25:]
        
        print("Running instruction at " + hex(program_counter) + ": " + instruction_binary)
        
        # Make sure r0 is always 0
        all_registers[0] = 0
        
        # instruction identification
        if opcode == "0110011":  # R-type
            func7 = instruction_binary[:7]
            rs2 = "r" + str(int(instruction_binary[7:12], 2))
            rs1 = "r" + str(int(instruction_binary[12:17], 2))
            func3 = instruction_binary[17:20]
            rd = "r" + str(int(instruction_binary[20:25], 2))
            do_r_type_instruction(func3, func7, rs1, rs2, rd)
            
        elif opcode in ["0000011", "0010011", "1100111"]:  # I-type
            imm_bits = instruction_binary[:12]
            imm = int(imm_bits, 2)
            if imm_bits[0] == '1':  # Check sign bit
                imm = make_number_correct(imm, 12)
            rs1 = "r" + str(int(instruction_binary[12:17], 2))
            func3 = instruction_binary[17:20]
            rd = "r" + str(int(instruction_binary[20:25], 2))
            if do_i_type_instruction(func3, imm, rs1, rd, opcode):
                continue  # JALR changes PC, skip increment
                
        elif opcode == "0100011":  # S-type
            upper_imm = instruction_binary[:7]
            rs2 = "r" + str(int(instruction_binary[7:12], 2))
            rs1 = "r" + str(int(instruction_binary[12:17], 2))
            func3 = instruction_binary[17:20]
            lower_imm = instruction_binary[20:25]
            imm_bits = upper_imm + lower_imm
            imm = int(imm_bits, 2)
            if imm_bits[0] == '1':
                imm = make_number_correct(imm, 12)
            if do_s_type_instruction(func3, imm, rs1, rs2):
                continue  # If function handled PC, skip increment
                
        elif opcode == "1100011":  # B-type
            imm_12 = instruction_binary[0]
            imm_10_5 = instruction_binary[1:7]
            rs2 = "r" + str(int(instruction_binary[7:12], 2))
            rs1 = "r" + str(int(instruction_binary[12:17], 2))
            func3 = instruction_binary[17:20]
            imm_4_1 = instruction_binary[20:24]
            imm_11 = instruction_binary[24]
            imm_bits = imm_12 + imm_11 + imm_10_5 + imm_4_1 + "0"
            imm = int(imm_bits, 2)
            if imm_bits[0] == '1':
                imm = make_number_correct(imm, 13)
            
            branch_result = do_b_type_instruction(func3, imm, rs1, rs2)
            if branch_result:
                if func3 == "000" and rs1 == "r0" and rs2 == "r0" and imm == 0:
                    found_halt = True
                    write_memory_to_file(data_area, output_file)
                continue  # Skip PC increment
                
        elif opcode == "1101111":  # J-type (JAL)
            imm_20 = instruction_binary[0]
            imm_10_1 = instruction_binary[1:11]
            imm_11 = instruction_binary[11]
            imm_19_12 = instruction_binary[12:20]
            rd = "r" + str(int(instruction_binary[20:25], 2))
            imm_bits = imm_20 + imm_19_12 + imm_11 + imm_10_1 + "0"
            imm = int(imm_bits, 2)
            if imm_bits[0] == '1':
                imm = make_number_correct(imm, 21)
            do_j_type_instruction(imm, rd)
            continue  # Skip PC increment as function handles it
            
        else:
            print("Error: Unknown opcode " + opcode + " at " + hex(program_counter))
            break
            
        all_registers[0] = 0
        
    if not found_halt:
        print("Warning: Program ended without Virtual Halt")
        write_memory_to_file(data_area, output_file)

input_file = "/home/strangersagain/Downloads/Group_148/automatedTesting/tests/bin/simple/simple_1.txt"
output_file = "/home/strangersagain/Downloads/Group_148/automatedTesting/tests/user_traces/simple/simple_1.txt"

run_risc_v_simulation(input_file, output_file)