import socket
import threading
import re
import os, sys, pickle
from cryptography.fernet import Fernet

import pyDH
import random
from Crypto.Cipher import DES3
from Crypto.Random import get_random_bytes
from Crypto import Random


'''
# Choosing Nickname
nickname = input("Choose your username: ")
try:
    os.system('mkdir '+nickname+' 2>/dev/null') #dir name=user name
except:
    print('Directory of this user already exists')    
'''

Address = socket.gethostbyname(socket.gethostname())

usrname = None
users_dict_file = open("users_dict.pkl","rb")
users_dict = pickle.load(users_dict_file)
users_dict_file.close()

def search_user(usrname) :
    for user in users_dict :
        if usrname == user :
            return True
    return False

count = 0
while True :
    if count > 3 :
        print("Authentication failed more than 3 times")
        sys.exit()
    print("Are you a new user ? \n Type Y or N " )
    yes_or_no = input() 
    if yes_or_no == "y" or yes_or_no ==  "Y" :
        usrname = input("Select Username : ")
        if search_user(usrname) == True :
            print("Username already exists , Please select some other username ")
            continue
        else :
            passwd = input("Select Password : ")
            users_dict[usrname] = passwd
            print("Signed up !!!" + "\n" + "Logged in !!!")

            nickname=usrname
            try:
                os.system('mkdir '+nickname+' 2>/dev/null') #dir name=user name
            except:
                print('Directory of this user already exists')   

            break

    elif yes_or_no == "n" or yes_or_no == "N" :
        print("Login : ")
        usrname = input("Enter Username : ")
        passwd = input("Enter Password : ")
        if search_user(usrname) == False or  ( search_user(usrname) == True and passwd != users_dict[usrname] ) :
            print("Wrong Credentials")
            continue 
        else :
            print("Logged in !!!")

            nickname=usrname
            try:
                os.system('mkdir '+nickname+' 2>/dev/null') #dir name=user name
            except:
                print('Directory of this user already exists')   

            break
    count += 1

user_dict_file = open("users_dict.pkl", "wb")
pickle.dump(users_dict , user_dict_file)
user_dict_file.close()





# Connecting To Server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 55555))


def write_key():
    """
    Generates a key and save it into a file
    """
    key = Fernet.generate_key()
    with open("key.key", "wb") as key_file:
        key_file.write(key)

def load_key():
    """
    Loads the key from the current directory named `key.key`
    """
    return open("key.key", "rb").read()


def encrypt(filename, key):
    """
    Given a filename (str) and key (bytes), it encrypts the file and write it
    """
    f = Fernet(key)
    with open(filename, "rb") as file:
        # read all file data
        file_data = file.read()
    # encrypt data
    encrypted_data = f.encrypt(file_data)
    # write the encrypted file
    with open(filename, "wb") as file:
        file.write(encrypted_data)


def decrypt(filename, key):
    """
    Given a filename (str) and key (bytes), it decrypts the file and write it
    """
    f = Fernet(key)
    with open(filename, "rb") as file:
        # read the encrypted data
        encrypted_data = file.read()
    # decrypt data
    decrypted_data = f.decrypt(encrypted_data)
    # write the original file
    with open(filename, "wb") as file:
        file.write(decrypted_data)




# Listening to Server and Sending Nickname
def receive():
    while True:
        try:
            # Receive Message From Server
            # If 'NICK' Send Nickname
            message = client.recv(1024).decode('ascii')
            if message == 'NICK':
                client.send(nickname.encode('ascii'))
            else:
                print(message+'\n')


                #print(type(message))
        except:
            # Close Connection When Error
            print("An error occured!")
            client.close()
            break

# Sending Messages To Server
def write():
    while True:
        message = '{}: {}'.format(nickname, input('')) #here, 1st word is <nickname>:

        client.send(message.encode('ascii'))

# Starting Threads For Listening And Writing
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()


