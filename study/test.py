def add(a, b):
    return a + b

def sub(a, b):
    return a - b

def mul(a, b):
    return a * b

def div(a, b):
    return a / b

def cal(a, b, op):
    if op == '+':
        return add(a, b)
    elif op == '-':
        return sub(a, b)
    elif op == '*':
        return mul(a, b)
    elif op == '/':
        return div(a, b)
    else:
        return "Invalid operator"

def find_even_numbers(input_numbers):
    even_numbers = []
    for num in input_numbers:
        if num == 0:
            print(f"Found zero: {num}")
            return None
        elif num % 2 == 0:
            even_numbers.append(num)
    else:
        # 当 for 循环未被 break 中断时执行
        return even_numbers

def write_file():
    try:
        # 文件不存在会直接创建文件，存在会清空文件重新写入
        with open('io_test.txt', 'w', encoding='utf-8') as f:
            f.write('Hello, World!')
    except IOError:
        print("IO error")

if __name__ == "__main__":
    res = cal(10, 20, '+')
    print(f"Result: {res}")

    numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    even = find_even_numbers(numbers)
    print(f"Even numbers: {even}")

    write_file()

