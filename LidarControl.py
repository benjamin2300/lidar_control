import socket
import keyboard
import threading
import json
#import time
import pandas as pd
from datetime import datetime
import csv

def RxMessage() :
  global s, rxRunState
  timeCount = 0
  while (rxRunState == 1) :
    s.settimeout(1)
    timeCount = timeCount + 1
    try :
      indata, addr = s.recvfrom(1500)
      #print('recvfrom ' + str(addr) + ': ' + indata.decode(), end='', flush=True)
      print(indata.decode(), end='', flush=True)
      if(indata.decode() == 'stopfire') :
        print('cmd>')
    except :
      #print("Time :"+str(timeCount)+"sec",end='\r')
      pass

def TxMessage():
  global s, remoteAddr, txRunState
  while (txRunState == 1) :
    outdata = input('cmd>')
    if(outdata == '') :
      pass#print('cmd>')
    elif(outdata != 'exit') :
      s.sendto(outdata.encode(), remoteAddr)
      #print('sendto ' + str(remoteAddr) + ': ' + outdata)
    else :
      txRunState = 0
    

etherInfom = {
    "localIP": "192.168.2.194",
    "remoteIP": "192.168.2.10",
    "port": 8880
}


print('APP version : 20240723 0.0.1')
try :
  with open('etherInform.json', 'r') as openfile:
    etherInfom = json.load(openfile)
except :
  pass

localIP_Data = input('輸入電腦 IP 位址 :')
remoteIP_Data = input('輸入光達 IP 位址 :')
PORT_Data = input('輸入控制埠號 :')

if localIP_Data != '':
  etherInfom['localIP'] = localIP_Data

if remoteIP_Data != '':
  etherInfom['remoteIP'] = remoteIP_Data
  
if PORT_Data != '':
  etherInfom['port'] = PORT_Data    
  
print(etherInfom['localIP'])
print(etherInfom['remoteIP'])
print(etherInfom['port'])
 
with open("etherInform.json", "w") as outfile:
  json.dump(etherInfom, outfile)
    
HOST = etherInfom['localIP']#'192.168.2.194'
REMOTE = etherInfom['remoteIP']#'192.168.2.10'
PORT = etherInfom['port']#8880
FIRE_PORT = 8882
localAddr = (HOST, PORT)
remoteAddr = (REMOTE, PORT)
fireAddr = (HOST, FIRE_PORT)

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
IsConnectOK = 1
try :
  s.bind(localAddr)
  print('Server start at: %s:%s ' % localAddr)
  print('wait for connection...')
  IsConnectOK = 1
except :
  print('Server failed to bind at: %s:%s ' % localAddr)
  input('請按任意鍵結束...........')
  IsConnectOK = 0


if IsConnectOK == 1 :
  rxRunState = 1
  txRunState = 1
  rx = threading.Thread(target = RxMessage)
  tx = threading.Thread(target = TxMessage)
  rx.start()
  tx.start()
else :
  txRunState = 0 
  rxRunState = 0 

while True:     
  if (txRunState == 0):
    rxRunState = 0
    runRxFireState = 0
    print("Exit LIDAR control..................") 
    break;
s.close()