# map a joystick x and y to left and right motor power from -100 to 100 (smoothly)


def joy2lr(x, y):
    left = y + x
    right = y - x
    return left, right


if __name__ == "__main__":
    while True:
        x = input("x: ")
        y = input("y: ")
        print(joy2lr(int(x), int(y)))
