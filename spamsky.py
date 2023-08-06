import os
import telebot

import configparser
import json
import asyncio
from django.db import models
from django.utils import timezone
import time

from datetime import datetime   


from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.types import (
    PeerChannel
)

import requests 
import math

import secrets

import sys

import boto3

from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError
from telethon.tl.functions.channels import InviteToChannelRequest

 

API_KEY = secrets.API_KEY
App_api_id = secrets.App_api_id
App_api_hash = secrets.App_api_hash
Telegram_username = secrets.Telegram_username
phone = secrets.phone

def try2AddUser2Database(usersJson, uName, uGroup):
    if uName in usersJson:
        alreadyIn = False 
        for i in range(len(usersJson[uName]['uGroups'])):
            if usersJson[uName]['uGroups'][i] == uGroup:
                alreadyIn = True             
        if not(alreadyIn):
            usersJson[uName]['uGroups'].append(uGroup)
    else:
        usersJson[uName] = {}
        usersJson[uName]['uGroups'] = []
        usersJson[uName]['uGroups'].append(uGroup)
        
def markAsBothered(usersJson, uName):       
    if uName in usersJson:
        usersJson[uName]['bothered'] = True
    else:
        print("Error " + uName + " not in usersJson!!!")
    



def addUsers2Channel(spec):
  print("t3.3") 

  res = []
  async def main(phone):
      print("t3.2") 
      res2 = []
      await client.start()
      print("Client Created")
      # Ensure you're authorized
      if await client.is_user_authorized() == False:
          await client.send_code_request(phone)
          try:
              await client.sign_in(phone, input('Enter the code: '))
          except SessionPasswordNeededError:
              await client.sign_in(password=input('Password: '))
  
      # me = await client.get_me()
    
      print("---------Channels---------------")


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
          if 'bot' not in uuu: 
              if len(usersJson[uuu]['uGroups']) == cuGr:
                bothered = False
                if 'bothered' in usersJson[uuu]:
                    if usersJson[uuu]['bothered'] == True:
                        bothered = True
                if not bothered:  
                    print("Waiting 10 Seconds...")
                    time.sleep(10)
                    print(uuu + " " + str(usersJson[uuu]))  
                    try:
                        print ("Adding {}".format(uuu))
 
                        
                        client(InviteToChannelRequest('@' + spec['dest'],['@' + uuu]))
                        #result = client(functions.messages.AddChatUserRequest(
                        #    chat_id=-12398745604826,
                        #    user_id=uuu,
                        #    fwd_limit=42
                        #))
                        #print(result.stringify())
                        
                        markAsBothered(usersJson, uuu)
                        
                        count += 1
                        
                    except Exception as e: 
                        print(e)
                        #traceback.print_exc()
                        #print("Unexpected Error")
                        error_count += 1
                        if error_count > 10:
                            sys.exit('print')
                            count = maxCount + 1 
                            break
                            
                        continue 
                    
                   



      #markAsBothered(usersJson, 'gapud_gapud')
      
      with open('users.json', 'w') as f:
        prettylog = json.dumps(usersJson, indent=4)
        f.write(prettylog)
        f.close()    
      
      #for uuu in usersJson:
      #  if len(usersJson[uuu]['uGroups']) == 3:
      #      print(uuu + " " + str(usersJson[uuu]))
            
            
       
      return res2
  with client:
    res = client.loop.run_until_complete(main(phone))
  return res  
  

def scrapUsers():
  print("t3.3") 

  res = []
  async def main(phone):
      print("t3.2") 
      res2 = []
      await client.start()
      print("Client Created")
      # Ensure you're authorized
      if await client.is_user_authorized() == False:
          await client.send_code_request(phone)
          try:
              await client.sign_in(phone, input('Enter the code: '))
          except SessionPasswordNeededError:
              await client.sign_in(password=input('Password: '))
  
      # me = await client.get_me()
    
      print("---------Channels---------------")

      Channels = []

      entities = []
      #if type == "EN":
      #  with open('SourceENG2.json') as f:
      #      entities = json.load(f).get("channels")
      #if type == "RU":
      #  with open('SourceRU.json') as f:
      #      entities = (json.load(f)).get("channels")     
      
      #spec = {'type': 'text', 'source': 'SourceRU.json', 'numPerPost': 1, 'numTotal': 5, 'censorLinks': False, 'maxChar': 10000}
      
      entities = ["https://t.me/rvvoenkor2","https://t.me/readovchat","https://t.me/yurasumyChat","https://t.me/rt_russian_chat", "https://t.me/Ukraina_onli", "https://t.me/nevzorovtvchat"]     
    
      #with open('Dialogs.txt', 'w', encoding="utf-8") as f:
      #  async for dialog in client.iter_dialogs():
      #      f.write(str(dialog))
      #   
      #f.close() 
      #  
      #
      #return []
    
      async for dialog in client.iter_dialogs():
          #if dialog.is_channel:
              #print(f'{dialog.id}:{dialog.title}')  
              foundInList = False
              for ent in entities:
                spl = ent.lower().lower().split("/")
                rrr = spl[len(spl) - 1]
                #if "Ukraina_onli" in str(dialog.entity.username):
                #    print("str(dialog.entity.username) = " + str(dialog.entity.username))
                #    print(spl)
                #    print(rrr)
                #print(spl)
                #print(rrr)
                
                #print("---------------")
                #print(dialog.entity)
                #if dialog.entity.participants_count > 5:
                if hasattr(dialog.entity, 'username'):
                    if rrr == str(dialog.entity.username).lower():
                      foundInList = True
                      print(str(dialog.entity.username) + " " + rrr + " " + str(foundInList))
              if foundInList:
                Channels.append(dialog)
              #else:
              #  print("can't find " + str(dialog.entity.username))

      with open('users.json') as f:
        usersJson = (json.load(f)) 
      
      
      for i in range(0, len(Channels)):  
          print("------------------------")
          dialog = Channels[i]
          entity = dialog.entity
          print(dialog)
          
          users = await client.get_participants(dialog)
          print(users)
          for j in range(0, len(users)):  
            if users[j].username != None:
                print(users[j].username)
                try2AddUser2Database(usersJson, users[j].username, str(dialog.entity.username))
      
      
      markAsBothered(usersJson, 'ArturRudom')
      
      markAsBothered(usersJson, 'Dima_Anokhin777')
      markAsBothered(usersJson, 'se_ganesh')
      markAsBothered(usersJson, 'Abcdz12345')
      markAsBothered(usersJson, 'pablobablo')
      
      markAsBothered(usersJson, 'LuckyJet_Operator')
      markAsBothered(usersJson, 'dmitrbashk')
      markAsBothered(usersJson, 'DivAdmin')
      markAsBothered(usersJson, 'a1h1m1k')
      markAsBothered(usersJson, 'cmQmc')
      markAsBothered(usersJson, 'gapud_gapud')
      
      with open('users.json', 'w') as f:
      
        prettylog = json.dumps(usersJson, indent=4)
        #print(prettylog, f)
        f.write(prettylog)
        #sys.stdout = original_stdout
        f.close()    
      
      for uuu in usersJson:
        if len(usersJson[uuu]['uGroups']) == 3:
            print(uuu + " " + str(usersJson[uuu]))
            
            
       
      return res2
  with client:
    res = client.loop.run_until_complete(main(phone))
  return res   


# Setting configuration values
api_id = App_api_id
api_hash = App_api_hash


phone = phone
username = Telegram_username

# Create the client and connect
client = TelegramClient(username, api_id, api_hash)
print("client should exist")
 
 
#API_KEY = API_KEY
bot = telebot.TeleBot(API_KEY)
print("t2")  
"""
@bot.message_handler(commands=['Greet'])
def greet(message):
  bot.reply_to(message, "Hey!")
  print("123")
  
  grabTheTop()
  
  print("456")  


bot.polling()
"""
 
testing = False

if testing: 
  print('Now ru')
    
else:
 
      print("t3") 
      #spec = {'type': 'repo', 'source': 'SourceRU.json', 'numTotal': 5, 'noDuplicatesNum': 10, 'noDuplicatesTresh': 0.7, 'forLastXhours': 6, 'noChannelDuplicatesNum': 7}
      
      #res =  scrapUsers()
      spec = {'dest': 'OpenNewsAggregatorRUUA'}
      res = addUsers2Channel(spec)
      print(res)
      
      
      #log['blocks'].append({})
      #log['blocks'][0]['posts'] = []
      #log['blocks'][0]['posts'].append({})
      #log['blocks'][0]['posts'][0]['text'] = 'test text yo'
  