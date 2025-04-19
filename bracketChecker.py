import os

def is_commented(line, index):
    """Check if character at index is after a # in the same line."""
    comment_pos = line.find('#')
    return comment_pos != -1 and index > comment_pos

def count_braces_in_file(filepath):
    left_count = 0
    right_count = 0

    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            for idx, char in enumerate(line):
                if char == '{' and not is_commented(line, idx):
                    left_count += 1
                elif char == '}' and not is_commented(line, idx):
                    right_count += 1

    return left_count, right_count

def scan_txt_files():
    mismatched_files = []

    for filename in os.listdir('.'):
        if filename.endswith('.txt') and os.path.isfile(filename):
            left, right = count_braces_in_file(filename)
            if left != right:
                mismatched_files.append((filename, left, right))

    if mismatched_files:
        print("Files with mismatched brackets:")
        for fname, l, r in mismatched_files:
            print(f"{fname}: {{={l}, }}={r}")
    else:
        print("All files have matched braces.")

if __name__ == "__main__":
    scan_txt_files()
