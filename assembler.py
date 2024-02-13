# Recieves an Array of Strings(Java statments)
# Returns an Array of Arrays(Containing the components of each statement)
# Example parse(["String   a = "Hello, World!;", "Int b = 3;"]) would return [["String","a", "=", "Hello, World!", ";"], ["Int", "b", "=", "3", ";"]]

import re


def parse(lines):
    parsed_lines = []  # Will hold the parsed version of each line

    for line in lines:
        # parsed_line = line.strip().split()

        # Add space where there should be space
        line = space_out(['+', '-', '/', '*', '%', '=', '>',
                         '<', '!', ')', '(', '}', '{', '||', '&&', ';'], line)

        # We undo the changes for the operators that use two symbols
        # To preserve increment statements(i++)
        line = line.replace("+  +", "++")
        # To preserve decrement statements(i--)
        line = line.replace("-  -", "--")
        line = line.replace("/  /", "//")
        line = line.replace("/  *", "/*")
        line = line.replace("*  /", "*/")
        line = line.replace("=  =", "==")
        line = line.replace(">  =", ">=")
        line = line.replace("<  =", "<=")
        line = line.replace("!  =", "!=")
        line = line.replace("-  =", "-=")
        line = line.replace("*  =", "*=")  # To preserve a += b types
        # To preserve a += b types# To preserve a += b types
        line = line.replace("+  =", "+=")

        # Preserve strings within Java Statements from whitespace condenscing
        all_strings = re.findall(r"\"(.*?)\"", line)
        line = re.sub(r"\"(.*?)\"", " ' ", line)

        # Tokenize arithmetic expressions
        line = re.sub(
            r"(\d+|[_a-zA-Z]\w*)(\s*)([+\-*/%])(\s*)(\d+|[_a-zA-Z]\w*)", r"\1 \3 \5", line)

        # Tokenize comparison expressions
        line = re.sub(
            r"(\d+|[_a-zA-Z]\w*)(\s*)(==|<=|>=|!=|<|>)(\s*)(\d+|[_a-zA-Z]\w*)", r"\1 \3 \5", line)

        # Tokenize logical expressions
        line = re.sub(r"(\w+)(\s*)(\|\||&&)(\s*)(\w+)", r"\1 \3 \5", line)

        # Remove multiple whitespaces
        line = re.sub(r"\s+", " ", line)

        # splits a string to an array based on whitespace
        parsed_line = line.strip().split(' ')

        # reintegrate preserved strings back
        x = 0
        for i, component in enumerate(parsed_line):
            if component == "'":
                parsed_line[i] = "\"" + all_strings[x] + "\""
                x += 1

        # Append to parsedLines array after checking

        # Check if the line is a for loop statement
        if len(parsed_line) >= 3 and parsed_line[0] == 'for' and parsed_line[1] == '(' and parsed_line[-1] == '}':
            x = parsed_line.index(')')
            init_stmt, condition, update_stmt = extract_for_components(
                parsed_line[2:x])
            body = parsed_line[x + 2:-1]
            parsed_lines.append(
                ['for', init_stmt, condition, update_stmt, body])
        # Check if the line is a while loop statement
        elif len(parsed_line) >= 3 and parsed_line[0] == 'while' and parsed_line[1] == '(' and parsed_line[-1] == '}':
            x = parsed_line.index(')')
            condition = parsed_line[2:x]
            body = parsed_line[x + 2:-1]
            parsed_lines.append(['while', condition, body])
        elif len(parsed_line) >= 3 and parsed_line[0] == 'if' and parsed_line[1] == '(' and parsed_line[-1] == '}':
            x = parsed_line.index(')')
            condition = parsed_line[2:x]
            body = parsed_line[x + 2:-1]
            parsed_lines.append(['if', condition, body])

        elif 'else' in parsed_line and parsed_line[-1] == '}':
            body = parsed_line[2:-1]
            parsed_lines.append(['else', body])
        else:
            parsed_lines.append(parsed_line)

    return parsed_lines


def space_out(arr, string):
    for character in arr:
        string = string.replace(character, " " + character + " ")

    return string


def extract_for_components(components):
    components = [c.strip() for c in components]
    condition_start_idx = components.index(';') + 1
    update_stmt_start_idx = components.index(';', condition_start_idx) + 1
    init_stmt = components[:condition_start_idx - 1]
    condition = components[condition_start_idx:update_stmt_start_idx - 1]
    update_stmt = components[update_stmt_start_idx:]
    return init_stmt, condition, update_stmt


def handler(lines):
    parsed_lines = parse(lines)
    mips_data = [".data", "newline: .asciiz {}".format('"\\n"')]
    mips_text = [".text", "main:"]

    variables = {}  # variable-value map , for value assignment only
    variable_registered = {}  # variable-register map every used register is here

    mips_regs = ["$s0", "$s1", "$s2", "$s3", "$s4", "$s5", "$s6", "$s7", "$t7", "$t6", "$t5", "$t4", "$t3", "$t2",
                 "$t1", "$t0"]
    if_count = 0
    print_counter = 0
    loop_count = 0
    blockCount = 0
    operator_map = {'+': 'add', '-': 'sub', '*': 'mul', '>': 'sgt', '<': 'slt',
                    '>=': 'sge', '<=': 'sle', '==': 'seq', '!=': 'sne', '&&': 'and', '||': 'or'}
    operator_map2 = {'>': 'bgt', '<': 'blt', '>=': 'bge',
                     '<=': 'ble', '==': 'beq', '!=': 'bne'}

    for line in parsed_lines:

        # Ignore empty lines
        if not line:
            continue

        # Start with handling of the assignment statements for int
        if line[0] == 'int' and len(line) == 5:
            if line[1] not in variables:  # new variable declaration
                variables[line[1]] = line[3]
                if line[3].isdigit():
                    # Move an integer to a register
                    mips_data.append(f"{line[1]}: .word {line[3]}")
                    x = mips_regs.pop()
                    mips_text.append(f"lw {x}, {line[1]}")
                    variable_registered[line[1]] = x
                elif line[3] in variables:

                    val_reg = variable_registered[line[3]]
                    x = mips_regs.pop()
                    mips_text.append("move {}, {}".format(x, val_reg))
                    variable_registered[line[1]] = x
            # else:
            #
            #     # Move a variable to a register
            #     ####################################################
            elif line[1] in variables:  # declared variable update
                raise ValueError("variable re-declaration is not supported")

            # handle string variable assignment
        elif line[0] == "String":
            # Add variable to dictionary
            variables[line[1]] = line[3]

            # Create space in memory for variable
            mips_data.append(f"{line[1]}: .asciiz {line[3]}")

            # handle any kind of print statement
        elif line[0] == 'System.out.println':
            if print_counter > 0:
                mips_text.append("la $a0, newline")
                mips_text.append("li $v0, 4")
                mips_text.append("syscall")
            x = line.index(')')
            value = line[2:x][0]

            # If the value is a number, load it into $a0 and call print_int
            if str(value).isdigit():
                mips_text.append("li $a0, {}".format(value))
                mips_text.append("li $v0, 1")
                mips_text.append("syscall")
            # If the value is a variable, load its value into $a0 and call print_int
            elif value in variable_registered:
                val_reg = variable_registered[value]
                mips_text.append("move $a0, {}".format(val_reg))
                mips_text.append("li $v0, 1")
                mips_text.append("syscall")
            # If the value is a string, load its address into $a0 and call print_string
            elif ((value[0] and value[-1]) == ('"')) or ((value[0] and value[-1]) == ("'")):
                lbl = "string_" + str(len(mips_data))
                if (value[0] and value[-1]) == ("'"):
                    value = '"' + value[1:-1] + '"'
                mips_data.append("{}: .asciiz {}".format(lbl, value))
                mips_text.append("la $a0, {}".format(lbl))
                mips_text.append("li $v0, 4")
                mips_text.append("syscall")

            else:
                raise ValueError("Invalid print statement")
            print_counter += 1

        elif line[0][0] == "#":
            # If the first line is a comment starting with '#', append it as a comment to the mips_text list
            for i in line:
                mips_text.append(i)

        # handle any kind of arthimetic operation
        # (line[0] not in ['if', 'else', 'for', 'while'])
        elif (line[1] in ['+=', '-=', '*=', '++', '--']) or (len(line) > 4 and line[4] in ['+', '-', '*', '/', '%']) or (len(line) > 3 and line[3] in ['+', '-', '*', '/', '%']):
            if line[0] == 'int' and line[2] == '=' and len(line) > 5 and line[4] in ['+', '-', '*', '/', '%']:
                operator = line[4]
                operand1 = line[3]
                operand2 = line[5]
                result = line[1]

                if operand1.isdigit():
                    reg_operand1 = mips_regs.pop()
                    mips_text.append("li {}, {}".format(
                        reg_operand1, operand1))
                elif operand1 in variables:
                    reg_operand1 = variable_registered[operand1]
                else:
                    raise ValueError("Undefined variable: {}".format(operand1))
                mips_data.append(f"{result}: .word 0")
                reg_result = mips_regs.pop()
            elif (line[0] in variable_registered):
                if line[1] in ['+=', '-=', '*=', '++', '--']:
                    operator = line[1][0]
                    operand1 = line[0]
                    result = line[0]
                    if line[1] in ['++', '--']:
                        operand2 = '1'
                    else:
                        operand2 = line[2]
                elif line[3] in ['+', '-', '*', '/', '%']:
                    operator = line[3]
                    operand1 = line[0]
                    operand2 = line[4]
                    result = line[0]
                reg_operand1 = variable_registered[operand1]
                reg_result = reg_operand1
            else:
                raise ValueError("Unsupported arithmetic operation format")

            if operand2.isdigit():
                reg_operand2 = "$at"
                mips_text.append("li {}, {}".format(reg_operand2, operand2))
            elif operand2 in variables:
                reg_operand2 = variable_registered[operand2]
            else:
                raise ValueError("Undefined variable: {}".format(operand2))

            # Perform the operation and store the result in a register
            if operator in ['+', '-', '*']:
                arthimetic = operator_map[operator]
                mips_text.append("{} {}, {}, {}".format(
                    arthimetic, reg_result, reg_operand1, reg_operand2))
                mips_text.append("sw {}, {}".format(reg_result, result))

            elif operator == '/':
                mips_text.append("div {}, {}".format(
                    reg_operand1, reg_operand2))
                mips_text.append("mflo {}".format(reg_result))
                mips_text.append("sw {}, {}".format(reg_result, result))
            elif operator == '%':
                mips_text.append("div {}, {}".format(
                    reg_operand1, reg_operand2))
                mips_text.append("mfhi {}".format(reg_result))
                mips_text.append("sw {}, {}".format(reg_result, result))

            # Store the result in the variables dictionary
            variable_registered[result] = reg_result

        # Handle comparison operators that includes variable assignment
        elif line[0] == 'boolean' and line[2] == '=' and len(line) > 5 and (line[4] in ['==', '!=', '<', '<=', '>', '>=', '&&', '||']):
            operand1 = line[3]
            operand2 = line[5]
            result = line[1]
            operator = line[4]
            if operand1.isdigit():
                reg_operand1 = mips_regs.pop()
                mips_text.append("li {}, {}".format(reg_operand1, operand1))
            elif operand1 in variables:
                reg_operand1 = variable_registered[operand1]
            else:
                raise ValueError("Undefined variable: {}".format(operand1))
            mips_data.append(f"{result}: .word 0")
            reg_result = mips_regs.pop()
            if operand2.isdigit():
                mips_text.append("li $s0, {}".format(operand2))
            elif operand2 in variables:
                reg_operand2 = variable_registered[operand2]
            else:
                raise ValueError("Undefined variable: {}".format(operand2))

            comparison = operator_map[operator]
            mips_text.append("{} {}, {}, {}".format(
                comparison, reg_result, reg_operand1, reg_operand2))
            mips_text.append("sw {}, {}".format(reg_result, result))

# even when this is erased it still cause error for if/else
        elif line[0] == 'if':  # If statement
            if_count += 1
            blockCount += 1
            condition = line[1]
            body = line[2]
            # assuming the condition is a simple comparison only
            if len(condition) == 3 and (condition[0] in variable_registered) and (
                    condition[1] in ['==', '!=', '<', '<=', '>', '>=']):
                operator = condition[1]
                operand1 = condition[0]
                operand2 = condition[2]
                reg_operand1 = variable_registered[operand1]
                reg_operand2 = '$at'
                if operand2.isdigit():
                    mips_text.append("li $at, {}".format(operand2))
                elif operand2 in variables:
                    reg_operand2 = variable_registered[operand2]
                else:
                    raise ValueError("Undefined variable: {}".format(operand2))
                comp = operator_map2[operator]
                label = "truth_" + str(if_count)
                mips_text.append("{} {}, {}, {}".format(
                    comp, reg_operand1, reg_operand2, label))
                mips_text.append("j cont_{}".format(str(if_count)))
                # mips_text.append("j cont_"+str(if_count))
                # define and translate the body here
                mips_text.append("{}:".format(label))
                data, text = translate_body(body, blockCount)
                mips_data.extend(data)
                mips_text.extend(text)
                mips_text.append("cont_{}:".format(str(if_count)))

            else:
                raise ValueError("Unsupported condition format")

        elif line[0] == 'else':
            # translate body here
            blockCount += 1
            body = line[1]
            data, text = translate_body(body, blockCount)
            mips_data.extend(data)
            startOfElse = mips_text.index("j cont_{}".format(str(if_count)))
            mips_text = mips_text[:startOfElse] + \
                text + mips_text[startOfElse:]
        elif line[0] == 'for':
            blockCount += 1
            loop_count += 1
            initial = line[1] + [';']
            initial_data, initial_text = translate_body(initial, blockCount)

            mips_text.extend(initial_text)
            mips_data.extend(initial_data)
            condition = line[2]
            increment = line[3]
            increment_data, increment_text = translate_body(
                increment, blockCount, variable_registered)
            body = line[4]
            if len(condition) == 3 and (condition[0] in variable_registered) and (
                    condition[1] in ['==', '!=', '<', '<=', '>', '>=']):
                operator = condition[1]
                operand1 = condition[0]
                operand2 = condition[2]
                reg_operand1 = variable_registered[operand1]
                reg_operand2 = '$at'
                if operand2.isdigit():
                    mips_text.append("li $at, {}".format(operand2))
                elif operand2 in variables:
                    reg_operand2 = variable_registered[operand2]
                else:
                    raise ValueError("Undefined variable: {}".format(operand2))
                comp = operator_map2[operator]
                label = "truth_" + str(loop_count)
                mips_text.append('loop:')
                mips_text.append("{} {}, {}, {}".format(
                    comp, reg_operand1, reg_operand2, label))
                mips_text.append('j end')
                mips_text.append('{}:'.format(label))
                data, text = translate_body(body, blockCount)
                mips_data.extend(data)
                mips_text.extend(text)
                mips_text.extend(increment_text)
                mips_data.extend(increment_data)
                mips_text.append('j loop')
                mips_text.append('end:')

    # return statement should be updated to fit gui

    # print('\n'.join(mips_text+mips_data))
    return mips_text, mips_data

# assuming the body only contains print,arthimetic,logical,and variable assignments


def translate_body(body, blockNum, variable_registered={}):
    result = []
    temp_list = []

    for item in body:
        if item == ";":
            temp_list.append(item)  # Add the delimiter to the current sublist
            result.append(temp_list)
            temp_list = []
        else:
            temp_list.append(item)

    # Add the last sublist to the result
    result.append(temp_list)
    mips_text = []
    mips_data = []

    variables = {}  # variable-value map , for value assignment only
    variable_registered = {}  # variable-register map every used register is here
    # mips-regs is changed
    mips_regs = ["$s7", "$s6", "$s5", "$s4", "$s3", "$s2", "$s1", "$s0"]

    print_counter = 0
    operator_map = {'+': 'add', '-': 'sub', '*': 'mul', '>': 'sgt', '<': 'slt', '>=': 'sge', '<=': 'sle', '==': 'seq',
                    '!=': 'sne', '&&': 'and', '||': 'or'}

    for line in result:

        # Ignore empty lines
        if not line:
            continue

        # Start with handling of the assignment statements for int
        if line[0] == 'int' and len(line) == 5:
            if line[1] not in variables:  # new variable declaration
                variables[line[1]] = line[3]
                if line[3].isdigit():
                    # Move an integer to a register
                    mips_data.append(f"{line[1]}: .word {line[3]}")
                    x = mips_regs.pop()
                    mips_text.append(f"lw {x}, {line[1]}")
                    variable_registered[line[1]] = x
                elif line[3] in variables:

                    val_reg = variable_registered[line[3]]
                    x = mips_regs.pop()
                    mips_text.append("move {}, {}".format(x, val_reg))
                    variable_registered[line[1]] = x
            # else:
            #
            #     # Move a variable to a register
            #     ####################################################
            elif line[1] in variables:  # declared variable update
                raise ValueError("variable re-declaration is not supported")

            # handle string variable assignment
        elif line[0] == "String":
            # Add variable to dictionary
            variables[line[1]] = line[3]

            # Create space in memory for variable
            mips_data.append(f"{line[1]}: .asciiz {line[3]}")

            # handle any kind of print statement
        elif line[0] == 'System.out.println':
            if print_counter > 0:
                mips_text.append("la $a0, newline")
                mips_text.append("li $v0, 4")
                mips_text.append("syscall")
            x = line.index(')')
            value = line[2:x][0]

            # If the value is a number, load it into $a0 and call print_int
            if str(value).isdigit():
                mips_text.append("li $a0, {}".format(value))
                mips_text.append("li $v0, 1")
                mips_text.append("syscall")
            # If the value is a variable, load its value into $a0 and call print_int
            elif value in variable_registered:
                val_reg = variable_registered[value]
                mips_text.append("move $a0, {}".format(val_reg))
                mips_text.append("li $v0, 1")
                mips_text.append("syscall")
            # If the value is a string, load its address into $a0 and call print_string
            elif ((value[0] and value[-1]) == ('"')) or ((value[0] and value[-1]) == ("'")):
                lbl = "string_" + str(blockNum) + str(len(mips_data))
                if (value[0] and value[-1]) == ("'"):
                    value = '"' + value[1:-1] + '"'
                mips_data.append("{}: .asciiz {}".format(lbl, value))
                mips_text.append("la $a0, {}".format(lbl))
                mips_text.append("li $v0, 4")
                mips_text.append("syscall")

            else:
                raise ValueError("Invalid print statement")
            print_counter += 1

        # handle any kind of arthimetic operation
        elif (line[1] in ['+=', '-=', '*=', '++', '--']) or (line[4] in ['+', '-', '*', '/', '%']) or (
                line[3] in ['+', '-', '*', '/', '%']):
            print(line, variable_registered)
            if line[0] == 'int' and line[2] == '=' and len(line) > 5 and line[4] in ['+', '-', '*', '/', '%']:
                operator = line[4]
                operand1 = line[3]
                operand2 = line[5]
                result = line[1]

                if operand1.isdigit():
                    reg_operand1 = mips_regs.pop()
                    mips_text.append("li {}, {}".format(
                        reg_operand1, operand1))
                elif operand1 in variables:
                    reg_operand1 = variable_registered[operand1]
                else:
                    raise ValueError("Undefined variable: {}".format(operand1))
                mips_data.append(f"{result}: .word 0")
                reg_result = mips_regs.pop()
            elif (line[0] in variable_registered):

                if line[1] in ['+=', '-=', '*=', '++', '--']:
                    operator = line[1][0]
                    operand1 = line[0]
                    result = line[0]
                    if line[1] in ['++', '--']:
                        operand2 = '1'
                    else:
                        operand2 = line[2]
                elif line[3] in ['+', '-', '*', '/', '%']:
                    operator = line[3]
                    operand1 = line[0]
                    operand2 = line[4]
                    result = line[0]
                reg_operand1 = variable_registered[operand1]
                reg_result = reg_operand1
            else:
                raise ValueError("Unsupported arithmetic operation format")

            if operand2.isdigit():
                reg_operand2 = "$at"
                mips_text.append("li {}, {}".format(reg_operand2, operand2))
            elif operand2 in variables:
                reg_operand2 = variable_registered[operand2]
            else:
                raise ValueError("Undefined variable: {}".format(operand2))

            # Perform the operation and store the result in a register
            if operator in ['+', '-', '*']:
                arthimetic = operator_map[operator]
                mips_text.append("{} {}, {}, {}".format(
                    arthimetic, reg_result, reg_operand1, reg_operand2))
                mips_text.append("sw {}, {}".format(reg_result, result))

            elif operator == '/':
                mips_text.append("div {}, {}".format(
                    reg_operand1, reg_operand2))
                mips_text.append("mflo {}".format(reg_result))
                mips_text.append("sw {}, {}".format(reg_result, result))
            elif operator == '%':
                mips_text.append("div {}, {}".format(
                    reg_operand1, reg_operand2))
                mips_text.append("mfhi {}".format(reg_result))
                mips_text.append("sw {}, {}".format(reg_result, result))

            # Store the result in the variables dictionary
            variable_registered[result] = reg_result

        # Handle comparison operators that includes variable assignment
        elif line[0] == 'boolean' and line[2] == '=' and len(line) > 5 and (
                line[4] in ['==', '!=', '<', '<=', '>', '>=', '&&', '||']):
            operand1 = line[3]
            operand2 = line[5]
            result = line[1]
            operator = line[4]
            if operand1.isdigit():
                reg_operand1 = mips_regs.pop()
                mips_text.append("li {}, {}".format(reg_operand1, operand1))
            elif operand1 in variables:
                reg_operand1 = variable_registered[operand1]
            else:
                raise ValueError("Undefined variable: {}".format(operand1))
            mips_data.append(f"{result}: .word 0")
            reg_result = mips_regs.pop()
            if operand2.isdigit():
                mips_text.append("li $s0, {}".format(operand2))
            elif operand2 in variables:
                reg_operand2 = variable_registered[operand2]
            else:
                raise ValueError("Undefined variable: {}".format(operand2))

            comparison = operator_map[operator]
            mips_text.append("{} {}, {}, {}".format(
                comparison, reg_result, reg_operand1, reg_operand2))
            mips_text.append("sw {}, {}".format(reg_result, result))

    return mips_data, mips_text

# testing ... the if/else is causing problem other things works fine

# handler([
# "int b=5;",
#     'int c=b+4;',
# # "int b=5;",
#
# # '''if ( b == 0) {
# #
# #
# #     System.out.println("at least one of a or b is 0");
# #     System.out.println("neither a nor b is 0");
# # }''',
# '''else {
#     String h='nowww'
#     System.out.println("neither a nor b is 0");
# }'''
# ])


# handler([
    # "int c= 5;",
    # "String d= 'now';",
    # "int e=3;",
    # 'String a = "Hello";'
    # "int i = 6;",
    # "int c = 5;",
    # "if (i > c) { System.out.println(\"holy grail\");}",
    # "else { System.out.println(\"unholy af\")}"
    # "String newCode = \"This is a whole new world\";",
    # "System.out.println('h');"

    # ])
# '#sdlakmdklsmkl',
# '#asijoiasjdioajsd',
# '#ajsdhkashd',
# 'int x = 15;',
# 'int y = 6;',
# 'x+=1',
# 'y-=1',
#
# 'int a = x + y;',
# 'int f= y + 11;',
# 'a*=3',
# 'f=f+2',
#
# 'int c = x * y;',
#
# 'int d = x / y;',
# 'int j=x/5;',
#
# 'int e = x % y;',
# 'int k= x%7;',
# "System.out.println('yesss');",
# 'System.out.println("yesss againn");',
# 'System.out.println(4)',
# 'System.out.println(a)',
#     "int a = 3;",
#     "int b= 4;",
#     "boolean c=a>b;",
#
# "boolean d=a<b;",
# "boolean e=a>=b;",
# "boolean f=a<=b;",
# "boolean g=a==b;",
# "boolean h=a!=b;",
# "boolean k=a&&b;",
# "boolean l=a||b;",

# ])
