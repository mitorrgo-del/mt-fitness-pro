import sys

def dump_hex(filename, start_line, end_line):
    with open(filename, 'rb') as f:
        content = f.read().decode('utf-8', errors='replace').splitlines()
    
    for i in range(start_line - 1, min(end_line, len(content))):
        line = content[i]
        print(f"{i+1}: {line}")
        print(f"HEX: {line.encode('utf-8').hex()}")

if __name__ == "__main__":
    dump_hex(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
