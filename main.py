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
 

API_KEY = secrets.API_KEY
App_api_id = secrets.App_api_id
App_api_hash = secrets.App_api_hash
Telegram_username = secrets.Telegram_username
phone = secrets.phone

print()  

def text2Dict(Text):
    res = {}
    sp = Text.split()
    for i in range(len(sp)):
        if sp[i] in res:
            res[sp[i]] += 1
        else:
            res[sp[i]] = 1
    return res

def totalMass(dict):
    sum = 0
    for key in dict:  
        sum += dict[key]
    return 1.0 * sum

def statDist(Mu, Nu):
    tMu = totalMass(Mu)
    tNu = totalMass(Nu)
    dist = 0
    for key in Mu:  
        if key in Nu:
            dist += abs((Mu[key] / tMu) - (Nu[key] / tNu))
        else:
            dist += Mu[key] / tMu
    for key in Nu:
        if not (key in Mu):
            dist += Nu[key] / tNu
    return dist / 2         

def isDuplicate(MText, spec, newTexts, tresh):
    MDict = text2Dict(MText)
    
    for k in range(len(newTexts)):
        postText = newTexts[k] 
        PDict = text2Dict(postText)
        print('statDist')
        print(statDist(MDict, PDict))
        if statDist(MDict, PDict) < tresh:
            return True
    
    directory = os.fsencode('logs')
    names = []
    for file in os.listdir(directory):
         filename = os.fsdecode(file)
         if filename.endswith(".log"):
             if filename.startswith(spec['source'].rsplit(".",1)[0] + "-"):
                 print(filename)
                 names.append(filename)
             continue
         else:
             continue
             
    names = sorted(names, key=str.upper) 
    
    for i in range(1, spec['noDuplicatesNum'] + 1): 
        if len(names) - i < 0:
            return False
        with open('logs\\' + names[len(names) - i], 'r') as myfile:
            data = myfile.read()         
            #print(data)
            #print(names[len(names) - i])
            #print('e data')
            log = json.loads(data)
        for j in range(len(log['blocks'])):    
            for k in range(len(log['blocks'][j]['posts'])):
                postText = log['blocks'][j]['posts'][k]['text']
                #print('i = ' + str(i) + ',j = ' + str(j)  + ',k = ' + str(k))
                #print(postText)
                PDict = text2Dict(postText)
                #print('statDist')
                #print(statDist(MDict, PDict))
                if statDist(MDict, PDict) < tresh:
                    return True
    return False  
    
def isFromDuplicateChannel(chName, spec):
    directory = os.fsencode('logs')
    names = []
    for file in os.listdir(directory):
         filename = os.fsdecode(file)
         if filename.endswith(".log"):
             if filename.startswith(spec['source'].rsplit(".",1)[0] + "-"):
                 print(filename)
                 names.append(filename)
             continue
         else:
             continue
             
    names = sorted(names, key=str.upper) 
    
    for i in range(1, spec['noChannelDuplicatesNum'] + 1): 
        if len(names) - i < 0:
            return False
        with open('logs\\' + names[len(names) - i], 'r') as myfile:
            data = myfile.read()         
            #print(data)
            #print(names[len(names) - i])
            #print('e data')
            log = json.loads(data)
        for j in range(len(log['blocks'])):    
            for k in range(len(log['blocks'][j]['posts'])):
                if 'channelName' in log['blocks'][j]['posts'][k]:
                    channelName = log['blocks'][j]['posts'][k]['channelName']
                    #print('i = ' + str(i) + ',j = ' + str(j)  + ',k = ' + str(k))
                    #print(postText)
                    #PDict = text2Dict(postText)
                    #print('statDist')
                    #print(statDist(MDict, PDict))
                    if channelName == chName:
                        return True
    return False    

#def grabTheTop(type, num2get, saveType):
def grabTheTop(spec):
  print("t3.3") 

  res = []
  async def main(phone):
      #await client.forward_messages('@OpenNewsAggregatorRUUA', 4, '@vv_volodin') 
      
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
  
      me = await client.get_me()
    
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
      with open(spec['source']) as f:
          entities = (json.load(f)).get("channels")     
    
      async for dialog in client.iter_dialogs():
          if dialog.is_channel:
              print(f'{dialog.id}:{dialog.title}')  
              foundInList = False
              for ent in entities:
                if str(dialog.entity.username).lower() in ent.lower():
                  foundInList = True
              if foundInList:
                Channels.append(dialog)
              else:
                print("can't find " + str(dialog.entity.username))

       
      print("---------END Channels---------------")
      #return(res)
    
      top = []
      entitiesTop = []
      textMsgTop = []
      msgIdTop = []
      
      prevIn = []
      
   
      

   
   
      now = datetime.now(timezone.utc)
      print("now = " + str(now))  
   
      
      #for i in range(0, len(entities)):
      for i in range(0, len(Channels)):  
          # entity = entities[i]  #sleep
          
          #if i > 10:
          #    break
          #print("start " + str(entity))
          dialog = Channels[i]
          entity = dialog.entity
          print("start " + str(entity.username))
          #time.sleep(1)
          #my_channel = await client.get_entity(entity)
          my_channel = dialog        
          
          maxViewsInCurChannel = -1
          
  
          offset_id = 0
          limit = 10
          all_messages = []
          total_messages = 0
          total_count_limit = 100
          
          gettinOld = False
  
          while True:
              print("Current Offset ID is:", offset_id, "; Total Messages:", total_messages)
              history = await client(GetHistoryRequest(
                  peer=my_channel,
                  offset_id=offset_id,
                  offset_date=None,
                  add_offset=0,
                  limit=limit,
                  max_id=0,
                  min_id=0,
                  hash=0
              ))
              if not history.messages:
                  break
              messages = history.messages
              for message in messages:
                  all_messages.append(message.to_dict())
                  msgtime = message.to_dict().get("date")
                  print("now - msgtime = " + str(now - msgtime))
                  if (now - msgtime).total_seconds() > (spec['forLastXhours'] * 3600): 
                      gettinOld = True
                      break
                  if isinstance(message.to_dict().get("views"), int):
                      #print("is int")
                      if message.to_dict().get("views") > maxViewsInCurChannel:
                          maxViewsInCurChannel = message.to_dict().get("views")
                          #maxMsgInCurChannel = message.to_dict()
                          maxMsgInCurChannel = message
                 
              if gettinOld == True:
                  break
              
              offset_id = messages[len(messages) - 1].id
              total_messages = len(all_messages)
              if total_count_limit != 0 and total_messages >= total_count_limit:
                  break
  
   
  
          print("000")   
          
          if maxViewsInCurChannel > 0: 
              msgId = []
              msgId.append(maxMsgInCurChannel.to_dict().get("id"))
              QQQ = maxMsgInCurChannel.to_dict().get("message")
              print("begin maxMsgInCurChannel.to_dict()")
              print(maxMsgInCurChannel.to_dict())
              print("end maxMsgInCurChannel.to_dict()")
              textMsg = None
              #if(len(QQQ) == 0):
              if(maxMsgInCurChannel.to_dict().get("grouped_id") is not None):
                for message in all_messages:
                  if message.get("grouped_id") is not None: 
                    if message.get("grouped_id") == maxMsgInCurChannel.to_dict().get("grouped_id"):
                      if len(message.get("message")) > 0:
                        textMsg = message
                      if(message.get("id") != maxMsgInCurChannel.to_dict().get("id")):
                          msgId.append(message.get("id"))
                       
              print("111")
              for iii in range(0, len(top) + 1): 
                  inserting = False 
                  if iii == len(top):
                      inserting = True 
                  else:     
                      if maxMsgInCurChannel.to_dict().get("views") > top[iii].to_dict().get("views"):
                          inserting = True
                  MText = ''
                  if textMsg is not None: 
                    MText = str(textMsg.get("message"))
                  else:
                    MText = str(maxMsgInCurChannel.to_dict().get("message"))
                  
                  if inserting:
                      if isDuplicate(MText, spec, prevIn, 0.5):
                        inserting = False 
                      else:
                        if isFromDuplicateChannel(str(entity.username), spec):
                            inserting = False 
                        else:    
                            prevIn.append(MText)
                  
                  if inserting:
                      top.insert(iii, maxMsgInCurChannel)     
                      entitiesTop.insert(iii, entity)
                      textMsgTop.insert(iii, textMsg)
                      msgIdTop.insert(iii, msgId)
                      break
                      
          print("end " + str(entity.username))            
      
      num2show = spec['numTotal']
      
      #spec = {'type': 'text', 'source': 'SourceRU.json', 'numPerPost': 1, 'numTotal': 5, 'censorLinks': False, 'maxChar': 100000}
      
      if spec['type'] == 'repo':
        div = 1
      else:
        div = spec['numPerPost']
      
      r2n = math.ceil(min(num2show, len(top)) / div)
      for uuu in range (0, r2n):
        res2.append({});
        if spec['type'] == 'repo':
          res2[uuu]['type'] = 'repo'
          res2[uuu]['val'] = {}        
        else:
          res2[uuu]['type'] = 'text'
          res2[uuu]['val'] = ''
        #res2.append('')
      for uuu in range (0, len(top)):
          if uuu >= num2show:
              break
          msg = top[uuu].to_dict()    
          if spec['type'] == 'repo':  
            res2[uuu // div]['val']['from_chat_id'] = str(entitiesTop[uuu].username) 
            res2[uuu // div]['val']['message_id'] = msgIdTop[uuu]
            res2[uuu // div]['val']['text'] = str(msg.get("message"))
            if textMsgTop[uuu] is not None:
                  res2[uuu // div]['val']['text'] = str(textMsgTop[uuu].get("message"))
          else:
              ent = str(entitiesTop[uuu].username)
              SSS = str(msg.get("message"))
              #SSS = str(msg.get("bytes")) 
              if(len(SSS) == 0):
                SSS = "[len(SSS) == 0]"
                if textMsgTop[uuu] is not None:
                  SSS = str(textMsgTop[uuu].get("message"))
              if spec['censorLinks']:
                SSS =  SSS.replace('\n', ' ').replace('\r', '')
                SSS =  SSS.replace('https://','h**ps://').replace('.com','.c*m')
                SSS =  SSS.replace('.ru','.r*').replace('.ua','.u*')
                SSS =  SSS.replace('#','*').replace('&','*').replace('@','*')
              SSS = (SSS)[0:spec['maxChar']]
              #shortEnt = ent.replace("https://t.me/","")
              shortEnt = 'https://t.me/' + ent + '/' + str(msg.get("id")) + " ,views = " + str(msg.get("views"))
              SSS =  '(' + str(uuu) + ')' + shortEnt + ": " + SSS 
              print(SSS)
                
                #print('len(top) = ')
                #print(len(top))             
                #print('num2show = ')
                #print(num2show)           
                #print('r2n = ')
                #print(r2n)             
                #print('uuu = ')
                #print(uuu)          
                #print('res2[uuu // div][\'val\'] = ')
                #print(res2[uuu // div]['val'])
              res2[uuu // div]['val'] = res2[uuu // div]['val'] + SSS + "\n\n"
              #await client.forward_messages('@OpenNewsAggregatorRUUA', top[uuu])
              #await client.forward_messages('@OpenNewsAggregatorRUUA', top[uuu])
            
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

#res2[uuu // div]['val']['text'] = 
def add_msg_to_log(elRes, log):  
  log['blocks'].append({})
  log['blocks'][len(log['blocks']) - 1]['posts'] = []
  log['blocks'][len(log['blocks']) - 1]['posts'].append({})
  log['blocks'][len(log['blocks']) - 1]['posts'][0]['text'] = elRes['val']['text']
  log['blocks'][len(log['blocks']) - 1]['posts'][0]['channelName'] = elRes['val']['from_chat_id']
  #log['blocks'][len(log['blocks']) - 1]['posts'][0]['dtext'] = (elRes['val']['text']).encode('utf-8', 'replace').decode()
  #print(log['blocks'][len(log['blocks']) - 1]['posts'][0]['text'])
  #print("-------------------------------")
  #print(log['blocks'][len(log['blocks']) - 1]['posts'][0]['dtext'])
  
def send_msg_on_telegram(msg, type):
  async def main(phone):
    await client.start()
    print("Client Created")
    # Ensure you're authorized
    if await client.is_user_authorized() == False:
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))
  
    me = await client.get_me()
      
    #await client.forward_messages('@OpenNewsAggregatorRUUA', 4, '@vv_volodin') 
    print("send_msg1") 
    
    racdbnNewsTestGroup = type['dest'] 
    #if(type == "EN"):
    #  racdbnNewsTestGroup = 'OpenNewsAggregatorEN'
    #if(type == "RU"):  
    #  racdbnNewsTestGroup = 'OpenNewsAggregatorRUUA'

    print("send_msg2") 
    if msg['type'] == 'text':
     print("send_msg3") 
     telegram_api_url = f"https://api.telegram.org/bot{API_KEY}/sendMessage?chat_id=@{racdbnNewsTestGroup}&text={msg['val']}"
     tel_resp = requests.get(telegram_api_url)
     if tel_resp.status_code == 200:
      print ("Notification has been sent on Telegram") 
     else:
      print ("Could not send Message " + str(tel_resp.status_code) + str(tel_resp.text))
     print("send_msg4")  
    
    if msg['type'] == 'repo':
     print("send_msg5") 
     try:
        await client.forward_messages('@'+racdbnNewsTestGroup, msg['val']['message_id'], '@'+msg['val']['from_chat_id']) 
        if 'trans2' in type:
                sourceT = msg['val']['text']
                clientBoto = boto3.client('translate', region_name="us-east-1")
                result = clientBoto.translate_text(Text=sourceT, SourceLanguageCode="auto", TargetLanguageCode = type['trans2'])        
                if result['SourceLanguageCode'] == type['trans2']:
                    print('Already ' + type['trans2'])    
                else:
                    await client.send_message('@'+racdbnNewsTestGroup, """***Amazon Translate***
""" + result['TranslatedText'])
                #print('Now')
     except OSError:
        telegram_api_url = f"https://api.telegram.org/bot{API_KEY}/sendMessage?chat_id=@{racdbnNewsTestGroup}&text={'fail (privacy?) to load @' + msg['val']['from_chat_id']}"  
     print("send_msg6") 
     #telegram_api_url = f"https://api.telegram.org/bot{API_KEY}/forwardMessage?chat_id=@{racdbnNewsTestGroup}&from_chat_id=@{msg['val']['from_chat_id']}&message_id={msg['val']['message_id']}"
     #tel_resp = requests.get(telegram_api_url)
     #if tel_resp.status_code == 200:
     # print ("Notification has been sent on Telegram") 
     #else:
     # print ("Could not send Message " + str(tel_resp.status_code) + str(tel_resp.text))      
  with client:
    client.loop.run_until_complete(main(phone))
  return    



testing = False
#if testing: 
#    spec = {'type': 'repo', 'source': 'SourceRU.json', 'numTotal': 50, 'noDuplicatesNum': 10, 'noDuplicatesTresh': 0.7 }
#    isDuplicate('Как только, начнётся дефицит живой силы и полный отказ украинцев от желания воевать, так сразу Киев потеряет даже эту минимальную военную поддержку. Уже сейчас все фиксируют дефицит вооружения и живой силы в Украине. Зеленский при этом потеряет всё, а это для него куда важнее жизней рядовых украинцев. Все давно понимают, что цель запада не полная победа Украины, а ослабление РФ за счёт жизней украинцев. Жизнь украинцев и будущее Украины запада мало волнует. Украина в понимании западных сценаристов страна камикадзе. Вот нас в НАТО/ЕС никто не берёт. Запад не видит будущего Украины для себя, хотя сладко льют нам в уши лозунги, чтобы продлить способность украинцев умирать ради целей транснациональных корпораций.', spec, [], 0.5)
if testing: 
    sourceT = """Україна – тема номер один: вже сьогодні у Вільнюсі розпочинається саміт НАТО. 

Лідери військово-політичного блоку мають вирішити, чи отримає наша країна очікуване запрошення до членства та гарантії безпеки. Більшість учасників вже прибули до столиці Литви. Очікується і візит Зеленського.

Саміт почнеться о другій половині дня. Уважно слідкуємо і чекаємо хороших новин!"""

#    sourceT = 'Как только, начнётся дефицит живой силы и полный отказ украинцев от желания воевать, так сразу Киев потеряет даже эту минимальную военную поддержку. Уже сейчас все фиксируют дефицит вооружения и живой силы в Украине. Зеленский при этом потеряет всё, а это для него куда важнее жизней рядовых украинцев. Все давно понимают, что цель запада не полная победа Украины, а ослабление РФ за счёт жизней украинцев. Жизнь украинцев и будущее Украины запада мало волнует. Украина в понимании западных сценаристов страна камикадзе. Вот нас в НАТО/ЕС никто не берёт. Запад не видит будущего Украины для себя, хотя сладко льют нам в уши лозунги, чтобы продлить способность украинцев умирать ради целей транснациональных корпораций.'

    sourceT = """Танки противника, опасаясь быть сожженными в непосредственной близости от наших позиций, все чаще стараются работать издалека. 

Но даже на закрытых огневых позициях им не спрятаться от наших парней, которых хлебом не корми – дай вражескую технику спалить. 

Операторы дронов-камикадзе из 58-й армии обнаружили и уничтожили в районе Новоданиловки танк ВСУ, стрелявший по позициям ВС РФ в Работино. 
 
@wargonzo

*наш проект существует на средства подписчиков, карта для помощи. Also we all gay. 
4279 3806 9842 9521 """ 

    trans = Translator()
    result = trans.translate(sourceT, dest = 'ru')
    print(result)
    
    if result.src == 'ru':
        print('Already ru')    
    else:
        print('Now ru')
    
else:
    while(True):
      print("t3") 
      #send_msg_on_telegram("Б", "RU")
      #send_msg_on_telegram("О", "RU")
      #send_msg_on_telegram("Г", "RU")
      #send_msg_on_telegram(" ", "RU")
      #send_msg_on_telegram("Д", "RU")
      #send_msg_on_telegram("И", "RU")
      #send_msg_on_telegram("З", "RU")
      #send_msg_on_telegram("А", "RU")
      #send_msg_on_telegram("Й", "RU")
      #send_msg_on_telegram("Н", "RU")
      #send_msg_on_telegram("А", "RU") 
      
      #res =  grabTheTop("RU",5,"repo")
      #spec = {'type': 'text', 'source': 'SourceRU.json', 'numPerPost': 1, 'numTotal': 5, 'censorLinks': False, 'maxChar': 100000}
      
      spec = {'type': 'repo', 'source': 'SourceRU.json', 'numTotal': 5, 'noDuplicatesNum': 10, 'noDuplicatesTresh': 0.7, 'forLastXhours': 6, 'noChannelDuplicatesNum': 7}
      res =  grabTheTop(spec)
      #res = []
      
      now = datetime.now()
      FN = spec['source'].rsplit(".",1)[0] + '-[' + str(now).replace(".", "p").replace(":", "d") + '].log' 
      log = {'saveFile': FN}
      log['blocks'] = []
      #log['blocks'].append({})
      #log['blocks'][0]['posts'] = []
      #log['blocks'][0]['posts'].append({})
      #log['blocks'][0]['posts'][0]['text'] = 'test text yo'
      for i in range(0, len(res)):
        print("t4") 
        #time.sleep(5)
        print("i = " + str(len(res) - i - 1))
        print(res[len(res) - i - 1])
        send_msg_on_telegram(res[len(res) - i - 1], {'dest': 'OpenNewsAggregatorRUUA', 'trans2': 'ru'})
        add_msg_to_log(res[len(res) - i - 1], log)
      
      #original_stdout = sys.stdout
      with open('logs\\' + log['saveFile'], 'w') as f:
        #sys.stdout = f
        prettylog = json.dumps(log, indent=4)
        print(prettylog, f)
        f.write(prettylog)
        #sys.stdout = original_stdout
        f.close()
      
      send_msg_on_telegram({'type': 'text','val': "↑↑↑Топ" + str(spec['numTotal']) + " за прошедшие " + str(spec['forLastXhours']) + "ч. " }, {'dest': 'OpenNewsAggregatorRUUA'}) #+ str(datetime.now(timezone.utc)) + "(UTC)."
        
      # res =  grabTheTop('EN',25,"repo")
      #spec = {'type': 'repo', 'source': 'SourceENG2.json', 'numPerPost': 5, 'numTotal': 25, 'censorLinks': True, 'maxChar': 280}
      spec = {'type': 'repo', 'source': 'SourceENG2.json', 'numTotal': 5, 'noDuplicatesNum': 10, 'noDuplicatesTresh': 0.7, 'forLastXhours': 6, 'noChannelDuplicatesNum': 7}
      res =  grabTheTop(spec)
      
      print("t5") 
      now = datetime.now()
      FN = spec['source'].rsplit(".",1)[0] + '-[' + str(now).replace(".", "p").replace(":", "d") + '].log'
      log = {'saveFile': FN}
      log['blocks'] = []
      for i in range(0, len(res)):
        #time.sleep(5)
        print("i = " + str(len(res) - i - 1))
        print(res[len(res) - i - 1])
        send_msg_on_telegram(res[len(res) - i - 1], {'dest': 'OpenNewsAggregatorEN'})
        add_msg_to_log(res[len(res) - i - 1], log)

      #original_stdout = sys.stdout
      with open('logs\\' + log['saveFile'], 'w') as f:
        #sys.stdout = f
        prettylog = json.dumps(log, indent=4)
        #print(prettylog, f) 
        f.write(prettylog)
        #sys.stdout = original_stdout
        f.close()
        
      send_msg_on_telegram({'type': 'text','val': "↑↑↑Top" + str(spec['numTotal']) + " for the last " + str(spec['forLastXhours']) + "h. " }, {'dest': 'OpenNewsAggregatorEN'}) #+ str(datetime.now(timezone.utc)) + "(UTC)."
      print("git test")
      
      time.sleep((3600 * 3))