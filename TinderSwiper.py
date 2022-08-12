from termcolor import colored
import ctypes
import os
import csv

ascii =  """\n  _______ _           _           _____         _                 
 |__   __(_)         | |         / ____|       (_)                
    | |   _ _ __   __| | ___ _ _| (_____      ___ _ __   ___ _ __ 
    | |  | | '_ \ / _` |/ _ \ '__\___ \ \ /\ / / | '_ \ / _ \ '__|
    | |  | | | | | (_| |  __/ |  ____) \ V  V /| | |_) |  __/ |   
    |_|  |_|_| |_|\__,_|\___|_| |_____/ \_/\_/ |_| .__/ \___|_|   
                                                 | |              
                                                 |_|              """

def getaccounts():
    accounts = []
    with open('Accounts.csv', mode='r') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            accounts.append(row)
    return accounts

def selectmodule(module):
    os.system("cls")
    print(colored(ascii, "magenta"))
    print(colored(f"Starting Mode [{module}]...", 'white'))

    if module == "Auto Swiper":
        from Modules.tinder import start

    accounts = getaccounts()
    start(accounts)

def main():
    ctypes.windll.kernel32.SetConsoleTitleW("Tinder Swiper")
    while True:
        try:
            os.system("cls")
            print(colored(ascii, "magenta"))
            print(colored('Made for the boysss', 'white'))

            print('\n\nSelect a Mode to use!\n')
            print("""     [""" + colored('1', 'magenta') + """] Auto Swiper AI""")

            choice = input("\n\nYour choice" + colored(' > ', 'magenta'))
            if choice == '1':
                selectmodule("Auto Swiper")
            elif choice == '0':
                exit()
        except:
            continue


if __name__ == "__main__":
    os.system("cls")
    print(colored(ascii, "magenta"))
    main()