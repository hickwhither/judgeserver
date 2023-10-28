import subprocess, signal, sys

r"""
`create_subprc(executable_file)`: create an auto subprocess for u

`eprint(*args, **kwargs)`: print as stderr

Draw: stdout -> 0
Bot1 wins: stdout -> 1
Bot2 wins: stdout -> 2
Your response: stderr
"""

class create_subprc():
    r"""
    `read(timeout)`: read with timeout
    
    `write(*message)`: write message
    
    `terminate()`: terminate interactive
    """
    def __init__(self, executable_file):
        self.subprc = subprocess.Popen(
            executable_file,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8")

    def read(self, timeout=None):
        if timeout == None:
            return self.subprc.stdout.readline().decode("utf-8")
        
        def handle(*args): raise Exception("Timeout")
        signal.signal(signal.SIGALRM,handle)
        signal.alarm(timeout)
        
        try:
            return (self.subprc.stdout.readline().decode("utf-8"),0)
        except:
            return ("",1)

    def write(self, *message):
        self.subprc.stdin.write(f"{' '.join(i for i in message)}\n".encode("utf-8"))
        self.subprc.stdin.flush()

    def terminate(self):
        self.subprc.stdin.close()
        self.subprc.terminate()
        self.subprc.wait(timeout=0.2)
    
    def communicate(self, input = "", timeout = None):
        return self.subprc.communicate(bytes(input,'UTF-8'),timeout)