import sys

def check_braces(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    stack = []
    for i, line in enumerate(lines):
        for j, char in enumerate(line):
            if char == '{':
                stack.append((i+1, j+1))
            elif char == '}':
                if not stack:
                    print(f"Excess '}}' at line {i+1}, col {j+1}")
                    return
                stack.pop()
    
    if stack:
        line, col = stack[-1]
        print(f"Unclosed '{{' starting at line {line}, col {col}")
    else:
        print("Braces are balanced")

if __name__ == "__main__":
    check_braces(sys.argv[1])
