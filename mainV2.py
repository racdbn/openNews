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

import RacdbnSecrets

import sys

import boto3
import SWass
 

API_KEY = RacdbnSecrets.API_KEY
App_api_id = RacdbnSecrets.App_api_id
App_api_hash = RacdbnSecrets.App_api_hash
Telegram_username = RacdbnSecrets.Telegram_username
phone = RacdbnSecrets.phone

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
                 print("!!!" + filename)
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
            log = json.loads(data)
        for j in range(len(log['blocks'])):    
            for k in range(len(log['blocks'][j]['posts'])):
                postText = log['blocks'][j]['posts'][k]['text']
                PDict = text2Dict(postText)
                if statDist(MDict, PDict) < tresh:
                    return True
    return False 
    
    
def getPrevEmb(spec):   
    res = []
    directory = os.fsencode('logs')
    names = []
    for file in os.listdir(directory):
         filename = os.fsdecode(file)
         if filename.endswith(".log"):
             if filename.startswith(spec['source'].rsplit(".",1)[0] + "-"):
                 print("lala = " + filename)
                 names.append(filename)
             continue
         else:
             continue
             
    names = sorted(names, key=str.upper) 
    
    for i in range(1, spec['noDuplicatesNum'] + 1): 
        if len(names) - i < 0:
            return res
        with open('logs\\' + names[len(names) - i], 'r') as myfile:
            data = myfile.read()         
            log = json.loads(data)
        for j in range(len(log['blocks'])):    
            for k in range(len(log['blocks'][j]['posts'])):
                postText = log['blocks'][j]['posts'][k]['text']
                
                if 'trans2' in spec:
                    if(len(postText) > 0):
                        try:
                            sourceT = postText
                            clientBoto = boto3.client('translate', region_name="ap-southeast-1")
                            result = clientBoto.translate_text(Text=sourceT, SourceLanguageCode="auto", TargetLanguageCode = spec['trans2'])        
                            if result['SourceLanguageCode'] != type['trans2']:
                                postText = result['TranslatedText']
                        except Exception:
                            pass
                                    
                vec = SWass.Text2SimpleVec(postText)
                if vec != None:
                    res.append(vec)
    return res 


def vDist2(v1, v2):
    res = 0
    for xx in range(len(v1)):
        res += (v1[xx] - v2[xx])*(v1[xx] - v2[xx])
    return res

def getClosest(MTextEmb, prevEmb):
    res = {}
    res['Dist2'] = float('inf')
    for k in range(len(prevEmb)):
        dist2 = vDist2(MTextEmb, prevEmb[k])
        if dist2 < res['Dist2']:
            res['Dist2'] = dist2
            res['num'] = k
    return res 

def getClosestUpd(MTextEmb, prevEmb, closest):
    dist2 = vDist2(MTextEmb, prevEmb[len(prevEmb) - 1])
    if dist2 < closest['Dist2']:
        closest['Dist2'] = dist2
        closest['num'] = len(prevEmb) - 1
      
    
def isFromDuplicateChannel(chName, spec, prevInChan):

    for i in range(len(prevInChan)):
        name = prevInChan[i]
        if name == chName:
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
def grabChInfo(spec):
  print("t3.3") 

  res = []
  async def main(phone):
      #await client.forward_messages('@OpenNewsAggregatorRUUA', 4, '@vv_volodin') 
      
      print("t3.2") 
      
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
    

   
   
      now = datetime.now(timezone.utc)
      print("now = " + str(now))  
   
      ChInfoList = []
      for i in range(0, len(Channels)):  
          ChInfo = {} 
      
          dialog = Channels[i]
          entity = dialog.entity
          ChInfo['entity'] = entity
          
          print("start " + str(entity.username))
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
                  
                  msgtime = message.to_dict().get("date")
                  print("now - msgtime = " + str(now - msgtime))
                  if (now - msgtime).total_seconds() > (spec['forLastXhours'] * 3600): 
                      gettinOld = True
                      break
                  all_messages.append(message)    
                  if isinstance(message.to_dict().get("views"), int):
                      if message.to_dict().get("views") > maxViewsInCurChannel:
                          maxMsgInCurChannel = message
                 
              if gettinOld == True:
                  break
              
              offset_id = messages[len(messages) - 1].id
              total_messages = len(all_messages)
              if total_count_limit != 0 and total_messages >= total_count_limit:
                  break
           
          ChInfo['all_messages'] = all_messages
          ChInfo['maxMsgInCurChannel'] = maxMsgInCurChannel
          if maxMsgInCurChannel.to_dict().get("views") > 0:
            ChInfoList.append(ChInfo) 
      
      #cut here?
      #cut here?
      #cut here?
      
      return ChInfoList

  with client:
    res = client.loop.run_until_complete(main(phone))
  return res 

def loadPrevCl(spec, cl):
    directory = os.fsencode('logs')
    names = []
    for file in os.listdir(directory):
         filename = os.fsdecode(file)
         if filename.endswith(".txt"):
             if filename.startswith("CLS-" + spec['source'].rsplit(".",1)[0] + "-"):
                 print(filename)
                 names.append(filename)
             continue
         else:
             continue
             
    names = sorted(names, key=str.upper) 
    
    if len(names) > 0:
        with open('logs\\' + names[len(names) - 1], 'r') as myfile:
            data = myfile.read()         
            #print(data)
            #print(names[len(names) - i])
            #print('e data')
            cl = json.loads(data)
 


def grabTheTop(spec, ChInfoList, cl):
      res2 = []

      top = []
      entitiesTop = []
      textMsgTop = []
      msgIdTop = []
      
      prevIn = []
      prevInChan = []
      
      
      counter = 0
      prevEmb = []
      print("Go:getPrevEmb")
      prevEmb = getPrevEmb(spec)
      print("End:getPrevEmb")
      
      StartTime = datetime.now(timezone.utc)
           
      
      
      Save = []
      TextSave = []
      for i in range(0, len(ChInfoList)):
        Save.append({})
        TextSave.append({})
      
      for zzz in range(spec['numTotal']):
          maxPoints = -1;
          candidate = {}
          
          for i in range(0, len(ChInfoList)): 
           
            entity = ChInfoList[i]['entity']
            all_messages = ChInfoList[i]['all_messages']
            for j in range(0, min(len(all_messages), spec['lastNewsCap'])): 
              print("i = " + str(i) + ",len(ChInfoList) = " + str(len(ChInfoList)) + ",j = " + str(j) + ",len(all_messages) = " + str(len(all_messages)))
              MsgInCurChannel = all_messages[j]

              msgId = []
              msgId.append(MsgInCurChannel.to_dict().get("id"))
              QQQ = MsgInCurChannel.to_dict().get("message")
     
              textMsg = None
     
              if(MsgInCurChannel.to_dict().get("grouped_id") is not None):
                for msg in all_messages:
                  message = msg.to_dict() 
                  if message.get("grouped_id") is not None: 
                    if message.get("grouped_id") == MsgInCurChannel.to_dict().get("grouped_id"):
                      if len(message.get("message")) > 0:
                        textMsg = message
                      if(message.get("id") != MsgInCurChannel.to_dict().get("id")):
                          msgId.append(message.get("id"))
              
              MText = ''
              if textMsg is not None: 
                MText = str(textMsg.get("message"))
              else:
                MText = str(MsgInCurChannel.to_dict().get("message"))
                
              MTextPT = MText 
              if 'trans2' in spec:
                if(spec['noDuplicates'] == 'v2'):
                    if str(j) in TextSave[i]:
                        MTextPT = TextSave[i][str(j)]
                    else: 
                        sourceT = MTextPT
                        if(len(sourceT) > 0):
                            try:
                                clientBoto = boto3.client('translate', region_name="ap-southeast-1")
                                result = clientBoto.translate_text(Text=sourceT, SourceLanguageCode="auto", TargetLanguageCode = spec['trans2'])        
                                if result['SourceLanguageCode'] != type['trans2']:
                                    MTextPT = result['TranslatedText']
                                TextSave[i][str(j)] = MTextPT
                            except Exception:
                                pass
                        
                
              inserting = True   
              
              if isFromDuplicateChannel(str(entity.username), spec, prevInChan):
                  inserting = False    

              if isDuplicate(MText, spec, prevIn, 0.5):
                inserting = False 
                
              if type(MsgInCurChannel.to_dict().get("views")) != int:
                inserting = False
                print("MsgInCurChannel.to_dict().get(views) isnt int ")
                print("MsgInCurChannel.to_dict().get(views) = " + str(MsgInCurChannel.to_dict().get("views")))
              
  
              if inserting:
                  counter += 1
                  
                  
                  if(spec['noDuplicates'] == 'v2'):
                    if str(j) in Save[i]:
                        MTextEmb = Save[i][str(j)]['emb']
                        closest = Save[i][str(j)]['closest']
                        getClosestUpd(MTextEmb, prevEmb, closest)
                        Save[i][str(j)]['closest'] = closest
                    else:
                        MTextEmb = SWass.Text2SimpleVecPP(MTextPT)
                        if MTextEmb != None:
                            Save[i][str(j)] = {}
                            Save[i][str(j)]['emb'] = MTextEmb
                            closest = getClosest(MTextEmb['vec'], prevEmb)
                            Save[i][str(j)]['closest'] = closest
                    if MTextEmb != None:
                    
                        msgtime = MsgInCurChannel.to_dict().get("date")
                        print("StartTime - msgtime = " + str(StartTime - msgtime))
                        Secs = (StartTime - msgtime).total_seconds() 
                    
                    
                        curPoints = (closest['Dist2'] * MsgInCurChannel.to_dict().get("views")) * pow(min(5, MTextEmb['num']), 0.5) / pow(Secs + (5 * 60), 0.7)
                    else: 
                        curPoints = -1000000
                  else:
                    curPoints = MsgInCurChannel.to_dict().get("views")
                  
                  if curPoints > maxPoints:
                     maxPoints = curPoints
                     candidate['top'] = MsgInCurChannel
                     candidate['entitiesTop'] = entity
                     candidate['textMsgTop'] = textMsg
                     candidate['msgIdTop'] = msgId
                     candidate['MText'] = MText
                     if(spec['noDuplicates'] == 'v2'):
                        candidate['vec'] = MTextEmb['vec']
           
          top.append(candidate['top'])     
          entitiesTop.append(candidate['entitiesTop'])
          textMsgTop.append(candidate['textMsgTop'])
          msgIdTop.append(candidate['msgIdTop'])
          
          prevIn.append(candidate['MText'])
          prevInChan.append(str(candidate['entitiesTop'].username))
          if(spec['noDuplicates'] == 'v2'):
            prevEmb.append(candidate['vec'])            
      
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
          
      EndTime = datetime.now(timezone.utc)
      print("EndTime - StartTime = " + str(EndTime - StartTime))
      
      LoadPrevCl(cl)
      
          
      return res2  


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
        print("racdbnNewsTestGroup = " + str(racdbnNewsTestGroup) + ",msg['val']['message_id'] = " + str(msg['val']['message_id']) + ",msg['val']['from_chat_id'] = " + str(msg['val']['from_chat_id']))
        try:
            await client.forward_messages('@'+racdbnNewsTestGroup, msg['val']['message_id'], '@'+msg['val']['from_chat_id']) 
        except:
            print("An exception occurred")
        if 'trans2' in type:
            if(len(msg['val']['text']) > 0):
                sourceT = msg['val']['text']
                try:
                    clientBoto = boto3.client('translate', region_name="ap-southeast-1")
                    result = clientBoto.translate_text(Text=sourceT, SourceLanguageCode="auto", TargetLanguageCode = type['trans2'])        
                    if result['SourceLanguageCode'] == type['trans2']:
                        print('Already ' + type['trans2'])    
                    else:
                        await client.send_message('@'+racdbnNewsTestGroup, """***Amazon Translate***
""" + result['TranslatedText'])
                except Exception:
                    pass
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
      startTime = datetime.now() 
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
      
      spec = {'type': 'repo', 'source': 'SourceRU.json', 'numTotal': 1, 'noDuplicatesNum': (10 * 5), 'noDuplicatesTresh': 0.7, 'forLastXhours': 6, 'noChannelDuplicatesNum': (7 * 5), 'noDuplicates' : 'v2', 'lastNewsCap': 5, 'trans2': 'ru'}

      #res = []
      
      now = datetime.now()
      FN = spec['source'].rsplit(".",1)[0] + '-[' + str(now).replace(".", "p").replace(":", "d") + '].log' 
      log = {'saveFile': FN}
      log['blocks'] = []      
      
      clFN = "CLS-" + spec['source'].rsplit(".",1)[0] + '-[' + str(now).replace(".", "p").replace(":", "d") + '].txt' 
      cl = {'saveFile': clFN}
      cl['clusters'] = []
      
      ChInfoList = grabChInfo(spec)
      res =  grabTheTop(spec, ChInfoList, cl)
      
      for i in range(0, len(res)):
        print("t4") 
        print("i = " + str(len(res) - i - 1))
        print(res[len(res) - i - 1])
        #send_msg_on_telegram(res[len(res) - i - 1], {'dest': 'OpenNewsAggregatorRUUA', 'trans2': 'ru'})
        send_msg_on_telegram(res[len(res) - i - 1], {'dest': 'OpenNewsAggregatorRUUA', 'trans2': 'ru'})
        add_msg_to_log(res[len(res) - i - 1], log)
      
      with open('logs\\' + log['saveFile'], 'w') as f:
        prettylog = json.dumps(log, indent=4)
        f.write(prettylog)
        f.close()      
        
      with open('logs\\' + cl['saveFile'], 'w') as f:
        prettylog = json.dumps(cl, indent=4)
        f.write(prettylog)
        f.close()
      
      #send_msg_on_telegram({'type': 'text','val': "↑↑↑Топ" + str(spec['numTotal'])  + " новостей телеграма по просмотрам за прошедшие " + str(spec['forLastXhours']) + "ч. " }, {'dest': 'OpenNewsAggregatorRUUA'}) #+ str(datetime.now(timezone.utc)) + "(UTC)."
        
      #spec = {'type': 'repo', 'source': 'SourceENG2.json', 'numTotal': 5, 'noDuplicatesNum': 10, 'noDuplicatesTresh': 0.7, 'forLastXhours': 6, 'noChannelDuplicatesNum': 7}
      #res =  grabTheTop(spec)
      #
      #print("t5") 
      #now = datetime.now()
      #FN = spec['source'].rsplit(".",1)[0] + '-[' + str(now).replace(".", "p").replace(":", "d") + '].log'
      #log = {'saveFile': FN}
      #log['blocks'] = []
      #for i in range(0, len(res)):
      #  print("i = " + str(len(res) - i - 1))
      #  print(res[len(res) - i - 1])
      #  send_msg_on_telegram(res[len(res) - i - 1], {'dest': 'OpenNewsAggregatorEN'})
      #  add_msg_to_log(res[len(res) - i - 1], log)
      #
      #with open('logs\\' + log['saveFile'], 'w') as f:
      #  prettylog = json.dumps(log, indent=4)
      #  f.write(prettylog)
      #  f.close()
      #  
      #send_msg_on_telegram({'type': 'text','val': "↑↑↑Top" + str(spec['numTotal']) + " telegram news posts by views for the last " + str(spec['forLastXhours']) + "h. " }, {'dest': 'OpenNewsAggregatorEN'}) #+ str(datetime.now(timezone.utc)) + "(UTC)."
      #print("git test22222")
      endTime = datetime.now()
      
      www = (3600 * 3 * 0.2) - (endTime - startTime).total_seconds()
      if(www > 0):
        time.sleep(www + 180)