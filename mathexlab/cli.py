import sys
import argparse
from mathexlab.kernel.session import KernelSession
from mathexlab.kernel.executor import execute

def main():
    parser = argparse.ArgumentParser(description="MathexLab CLI")
    parser.add_argument('file', nargs='?', help="Script file to run")
    args = parser.parse_args()

    session = KernelSession()

    if args.file:
        try:
            with open(args.file, 'r') as f:
                code = f.read()
            # Execute file content
            execute(code, session)
        except Exception as e:
            print(f"Error reading file: {e}")
    else:
        # Start REPL
        print("MathexLab CLI 1.0. Type 'exit' to quit.")
        while True:
            try:
                line = input(">> ")
                if line.strip() == 'exit': break
                res = execute(line, session)
                if res: print(res)
            except KeyboardInterrupt:
                print("\n")
                break

if __name__ == "__main__":
    main()