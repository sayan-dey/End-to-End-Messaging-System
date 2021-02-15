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



# Sending Messages To All required Clients
def broadcast(message,clnts):
    for rec_client in clnts:
        rec_client.send(message)

def broadcast_file(file, temp, clnts):
    #st=temp[0]+' FILE '+ temp[2]
    for rec_client in clnts:
        rec_client.send((temp[0]+' '+temp[2]).encode())
        try:
            index=clients.index(rec_client)
            nickname=nicknames[index]
            os.system('cp '+file+' '+nickname+'/'+temp[2]+' 2>/dev/null')
        except:
            rec_client.send('An error occurred'.encode())


def unicast(client):
    if len(groups)==0:
        client.send('No group present\n'.encode())
        return
    st=''
    for key in groups:
        st+=str(key)+': '+ str(len(groups[key]))+ ' member(s)'+'\n'
    client.send(st.encode())   

        
# Handling Messages From Clients
def handle(client):
    while True:
        try:
            # Broadcasting Messages
            message = client.recv(1024)  #its first word is just username

            temp=re.split(' ',message.decode())
            if temp[1].upper()=='CREATE': # create a group
                groups[temp[2]]=[]

            elif temp[1].upper()=='LIST':  # show groups' info only to this client
                unicast(client) 

            elif temp[1].upper()=='JOIN':  #for joining a group (create it if this grp is not present)
                flag=0
                for key in groups:
                    if key==temp[2]:
                        flag=1
                        memlist=groups[temp[2]]
                        flag1=0
                        for x in memlist:
                            if x==client:
                                flag1=1
                                break
                        if flag1==0:  # to avoid duplicate users in a group        
                            groups[temp[2]].append(client)
                        else:
                            client.send('You are already a member of this group\n'.encode())
                if flag ==0:  # if the group is absent
                    groups[temp[2]] = []
                    groups[temp[2]].append(client)

            elif temp[1].upper()=='SEND': # sending to an individual
                flag=0
                for nickname in nicknames:
                    if nickname==temp[2]:
                        flag=1
                        break          
                if flag ==1:  #receiver present
                    index= nicknames.index(temp[2])
                    rec_client = clients[index]  # client who will get the msg
                    if temp[3].upper()!='FILE':  #text message
                        st=temp[0]
                        for x in range(3,len(temp)):
                            st+=' '+temp[x]
                        st+='\n'    
                        rec_client.send(st.encode())
                    else:  #file message
                        
                        rec_client.send((temp[0]+' '+temp[4]).encode())
                        index = clients.index(client)
                        nickname=nicknames[index]
                        file=str(nickname)+'/'+temp[4]  #filename to be unicasted
                        index = clients.index(rec_client)
                        nickname=nicknames[index]
                        os.system('cp '+file+' '+nickname+'/'+temp[4]+' 2>/dev/null')
                         

                else:
                    st='Receiver not present\n'
                    client.send(st.encode()) 


            else:  # broadcasting to all members of all groups where this user is present
                #broadcast(message)
                if len(groups)==0:
                    client.send('No group present to receive your message\n'.encode())
                else:
                    grouplist=[]  # groupnames where this msg will be broadcasted
                    for key,value in groups.items():
                        for x in value:
                            if x == client:
                                grouplist.append(key)
                    if len(grouplist)==0:
                        client.send('You are not a member of any group\n'.encode())
                    else:
                        clientset=set()  #clients who will receive this message 
                        clientset.add(client)
                        for group in grouplist:
                            for key,value in groups.items():
                                if key==group:
                                    for x in value:
                                        clientset.add(x)
                        if temp[1].upper()!='FILE': #text message                
                            broadcast(message,list(clientset)) 
                        else:  #file msg
                            index = clients.index(client)
                            nickname=nicknames[index]
                            file=str(nickname)+'/'+temp[2]  #filename to be broadcasted
                            broadcast_file(file, temp, list(clientset))

                          


        except:
            # Removing And Closing Clients
            index = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[index]
            broadcast('{} left!'.format(nickname).encode('ascii'), clients)
            nicknames.remove(nickname)
            break

# Receiving / Listening Function
def receive():
    while True:
        # Accept Connection
        client, address = server.accept()
        print("Connected with {}".format(str(address)))

        # Request And Store Nickname
        client.send('NICK'.encode('ascii'))
        nickname = client.recv(1024).decode('ascii')
        nicknames.append(nickname)
        clients.append(client)

        # Print And Broadcast Nickname
        print("Username is {}".format(nickname))
        broadcast("{} joined!".format(nickname).encode('ascii'),clients)
        client.send('Connected to server!'.encode('ascii'))

        # Start Handling Thread For Client
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()



# Connection Data
host = '127.0.0.1'
port = 55555

# Starting Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

# Lists For Clients and Their Nicknames
clients = []
nicknames = []
groups = dict()  #dict where key= groupname(str), value=list of names of users(list)

client_user_dict = {}
users_dict = {}
#print(type(dictionary_data))
a_file = open("users_dict.pkl", "wb")
pickle.dump(users_dict, a_file)
a_file.close()

groups_dict ={ }
b_file = open("groups_dict.pkl" , "wb")
pickle.dump(groups_dict,b_file)
b_file.close()


x=random.randint(0,3)
roll_list =[2020201064,2020201040,2020201007,2020801014]
n=str(roll_list[x])
r= str(random.randint(100000,999999))
Key= n+r
iv = Random.new().read(DES3.block_size)
cipher_encrypt = DES3.new(Key, DES3.MODE_OFB, iv)



receive()
