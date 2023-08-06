import os
import telebot

import configparser
import json
import asyncio
from django.db import models
from django.utils import timezone
import time

from datetime import datetime   

import requests 
import math

import secrets

import sys
 
from pyrogram import Client
import time

from pyrogram.errors import RPCError 
import sqlite3


con = sqlite3.connect("tutorial.db")

 

#API_KEY = secrets.API_KEY
App_api_id = secrets.App_api_id
App_api_hash = secrets.App_api_hash
#Telegram_username = secrets.Telegram_username
phone = secrets.phone

apps = Client("Sessions/",int(App_api_id),str(App_api_hash),phone_number=phone)  

apps.start() 

def markAsBothered(usersJson, uName):       
    if uName in usersJson:
        usersJson[uName]['bothered'] = True
    else:
        print("Error " + uName + " not in usersJson!!!") 



def addUsers2Channel(spec):
      now = datetime.now(timezone.utc)
      print("now = " + str(now)) 
      
      #apps.send_message("@racdbn", "yo")
      with open('users.json') as f:
        usersJson = (json.load(f)) 
      
      
      mmaxGr = 10
      count = 0
      maxCount = 0
      
      error_count = 0
      
      for ex in range(0, mmaxGr):
        cuGr = mmaxGr - ex
        for uuu in usersJson:
          if count > maxCount:
            break        
          if 'Bot' not in uuu: 
            if 'bot' not in uuu: 
              if len(usersJson[uuu]['uGroups']) == cuGr:
                bothered = False
                if 'bothered' in usersJson[uuu]:
                    if usersJson[uuu]['bothered'] == True:
                        bothered = True
                if not bothered:
                    print(uuu + " " + str(usersJson[uuu]))  
                    try:
                        print ("Adding {}".format(uuu))
                        #client(InviteToChannelRequest('@' + spec['dest'],['@' + uuu]))
                        markAsBothered(usersJson, uuu)
                        count += 1
                        apps.add_chat_members('@' + spec['dest'],'@' + uuu)
                    except Exception as e: 
                        print(e)
                        #traceback.print_exc()
                        #print("Unexpected Error")
                        error_count += 1
                        if error_count > 10:
                            sys.exit('print')
                            count = maxCount + 1 
                            break
                        status = ex.__class__.__name__
                        print("status = " + str(status))
                        continue 
                    print("Waiting 10 Seconds...")
                    time.sleep(10)             
    
      with open('users.json', 'w') as f:
        prettylog = json.dumps(usersJson, indent=4)
        f.write(prettylog)
        f.close()    
    
  



testing = False

if testing: 
  print('Now ru')
    
else:
    while(True):
      spec = {'dest': 'OpenNewsAggregatorRUUA'}
      res = addUsers2Channel(spec)
      print(res)
      time.sleep((3600 / 4))

  