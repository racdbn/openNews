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

from collections.abc import Mapping


 

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

def totalMass(dddd):
    sum = 0
    for key in dddd:  
        sum += dddd[key]
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


def getPrevIdf(idf):
    try:
        with open(idf['saveFile'], 'r') as myfile:
            data = myfile.read()         
            log = json.loads(data)
            idf['channels'] = log['channels']
    except Exception:
        pass   
        
        
        
def getPrevEmb(spec, idf):   
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
                if(isinstance(postText, Mapping)):
                    postText = postText['text']
                
                
                ch = log['blocks'][j]['posts'][k]['channelName']
                
                #if 'trans2' in spec:
                #    if(len(postText) > 0):
                #        try:
                #            sourceT = postText
                #            clientBoto = boto3.client('translate', region_name="ap-southeast-1")
                #            result = clientBoto.translate_text(Text=sourceT, SourceLanguageCode="auto", TargetLanguageCode = spec['trans2'])        
                #            if result['SourceLanguageCode'] != spec['trans2']:
                #                postText = result['TranslatedText']
                #        except Exception:
                #            pass
                            
                if('message_id' in log['blocks'][j]['posts'][k]):
                    msgId = log['blocks'][j]['posts'][k]['message_id']
                    SWass.UpdateIDF(idf, ch, msgId, postText)
                    vec = SWass.Text2SimpleVec(postText, idf['channels'][ch])
                else:
                    vec = SWass.Text2SimpleVec(postText, None)
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
  

      

#def grabChInfoIDF(spec, idf):
#  print("t3.3") 
#
#  res = []
#  async def main(phone):
#      
#      
#      print("t3.2") 
#      
#      await client.start()
#      print("Client Created")
#
#      if await client.is_user_authorized() == False:
#          await client.send_code_request(phone)
#          try:
#              await client.sign_in(phone, input('Enter the code: '))
#          except SessionPasswordNeededError:
#              await client.sign_in(password=input('Password: '))
#  
#      me = await client.get_me()
#    
#      print("---------Channels---------------")
#
#      Channels = []
#
#      entities = []
#
#      with open(spec['source']) as f:
#          entities = (json.load(f)).get("channels")     
#    
#      async for dialog in client.iter_dialogs():
#          if dialog.is_channel:
#              print(f'{dialog.id}:{dialog.title}')  
#              foundInList = False
#              for ent in entities:
#                if str(dialog.entity.username).lower() in ent.lower():
#                  foundInList = True
#              if foundInList:
#                Channels.append(dialog)
#              else:
#                print("can't find " + str(dialog.entity.username))
#
#       
#      print("---------END Channels---------------")
#    
#
#   
#   
#      now = datetime.now(timezone.utc)
#      print("now = " + str(now))  
#   
#      ChInfoList = []
#      for i in range(0, len(Channels)):  
#          ChInfo = {} 
#      
#          dialog = Channels[i]
#          entity = dialog.entity
#          ChInfo['entity'] = entity
#          
#          print("start " + str(entity.username))
#          my_channel = dialog        
#          
#          maxViewsInCurChannel = -1
#          
#  
#          offset_id = 0
#          limit = 10
#          all_messages = []
#          total_messages = 0
#          total_count_limit = 100
#          
#          gettinOld = False
#          
#          if(str(entity.username) not in idf['channels'])
#            idf['channels'][str(entity.username)] = {'postsIds': {}, 'words': {}}
#  
#          while True:
#              print("Current Offset ID is:", offset_id, "; Total Messages:", total_messages)
#              history = await client(GetHistoryRequest(
#                  peer=my_channel,
#                  offset_id=offset_id,
#                  offset_date=None,
#                  add_offset=0,
#                  limit=limit,
#                  max_id=0,
#                  min_id=0,
#                  hash=0
#              ))
#              if not history.messages:
#                  break
#              messages = history.messages
#              for message in messages:
#                  
#                  msgtime = message.to_dict().get("date")
#                  print("now - msgtime = " + str(now - msgtime))
#                  if (now - msgtime).total_seconds() > (spec['forLastXhours'] * 3600): 
#                      gettinOld = True
#                         
#                  if not gettingOld:  
#                      all_messages.append(message)    
#                      if isinstance(message.to_dict().get("views"), int):
#                          if message.to_dict().get("views") > maxViewsInCurChannel:
#                              maxMsgInCurChannel = message
#                  
#                  if(message.to_dict().get("message"))
#                  
#                 
#              if gettinOld == True:
#                if len(idf['channels'][str(entity.username)]['postsIds']) > spec['minIDFPosts']:
#                  break
#              
#              offset_id = messages[len(messages) - 1].id
#              total_messages = len(all_messages)
#              if total_count_limit != 0 and total_messages >= total_count_limit: 
#                if len(idf['channels'][str(entity.username)]['postsIds']) > spec['minIDFPosts']:
#                  break
#           
#          ChInfo['all_messages'] = all_messages
#          ChInfo['maxMsgInCurChannel'] = maxMsgInCurChannel
#          if maxMsgInCurChannel.to_dict().get("views") > 0:
#            ChInfoList.append(ChInfo) 
#      
#
#      
#      return ChInfoList
#
#  with client:
#    res = client.loop.run_until_complete(main(phone))
#  return res 
  
  
def deleteOldCls(spec):
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
    
    for i in range(len(names) - 2):
        print('trying to delete ' + 'logs\\' + names[i])
        os.remove('logs\\' + names[i])          

def LoadPrevCl(spec, cl):
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
            cl['clusters'] = json.loads(data)['clusters']
 


def Intersects(Arr, Brr):
    for i in range(len(Arr)):
        for j in range(len(Brr)):
            if Arr[i] == Brr[j]:
                return True
    return False

def getMsgFromCl(chatId, messageId, cl):
    for q in range(len(cl['clusters'])):
        if cl['clusters'][q]['head']['from_chat_id'] == chatId:
             if Intersects(cl['clusters'][q]['head']['message_id'], messageId):                
                return cl['clusters'][q]['head']
        for j in range(len(cl['clusters'][q]['elems'])):
            if cl['clusters'][q]['elems'][j]['from_chat_id'] == chatId:
                if Intersects(cl['clusters'][q]['elems'][j]['message_id'], messageId):
                     return cl['clusters'][q]['elems'][j]
    
    return None 

def grabTheTop(spec, ChInfoList, cl, idf):
      res2 = []

      top = []
      entitiesTop = []
      textMsgTop = []
      msgIdTop = []
      EmbsTop = []
      TextsTop = []
      EmbsNumTop = []
      EmbstotalWTop = []
      
      prevIn = []
      prevInChan = []
      
      
      counter = 0
      prevEmb = []
      print("Go:getPrevEmb")
      prevEmb = getPrevEmb(spec, idf)
      print("End:getPrevEmb")
      
      StartTime = datetime.now(timezone.utc)
           
      LoadPrevCl(spec, cl)
      
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
            print("i = " + str(i) + ",len(all_messages) = " + str(len(all_messages)))
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
                
              MTextPT = {'text': MText, 'trans': False, 'ATR': 'None'} 
              if 'trans2' in spec:
                if(spec['noDuplicates'] == 'v2'):
                    if str(j) in TextSave[i]:
                        MTextPT = TextSave[i][str(j)]
                    else: 
                        sourceT = MTextPT['text']
                        if(len(sourceT) > 0):
                            try:
                                clientBoto = boto3.client('translate', region_name="ap-southeast-1")
                                result = clientBoto.translate_text(Text=sourceT, SourceLanguageCode="auto", TargetLanguageCode = spec['trans2'])        
                                if str(result['SourceLanguageCode']) != str(spec['trans2']):
                                    MTextPT = {'text': result['TranslatedText'], 'trans': True, 'ATR': str(result['SourceLanguageCode']) + '->' + str(spec['trans2'])} 
                                MTextPT['ATR'] = str(result['SourceLanguageCode']) + '->' + str(spec['trans2'])
                                TextSave[i][str(j)] = MTextPT
                            except Exception as e: 
                                 PrintEx(EEE, e, " GT for related posts")
                                 MTextPT['ATR']  = "ECPT:[" + str(e) +"]"
                                 TextSave[i][str(j)] = MTextPT
                        else:
                            MTextPT = {'text': '', 'trans': False, 'ATR': 'ZeroText'}
                            TextSave[i][str(j)] = MTextPT
                            
              TextSave[i][str(j)]['ATR'] = TextSave[i][str(j)]['ATR'] + ",trans2 in spec = " + str('trans2' in spec)
              TextSave[i][str(j)]['ATR'] = TextSave[i][str(j)]['ATR'] + ",str(j) in TextSave[i] = " + str(str(j) in TextSave[i]) 
              TextSave[i][str(j)]['ATR'] = TextSave[i][str(j)]['ATR'] + ",spec[noDuplicates] == v2 = " + str(spec['noDuplicates'] == 'v2') 
              TextSave[i][str(j)]['ATR'] = TextSave[i][str(j)]['ATR'] + ",len(sourceT) > 0 = " + str(len(sourceT) > 0)       
                
              inserting = True 

                
              isFromDuplicateChannelWeigth = 1.0
              if isFromDuplicateChannel(str(entity.username), spec, prevInChan):
                  #inserting = False    
                  isFromDuplicateChannelWeigth = 0.5    

              if isDuplicate(MText, spec, prevIn, 0.5):
                inserting = False 
                
              if type(MsgInCurChannel.to_dict().get("views")) != int:
                inserting = False
                print("MsgInCurChannel.to_dict().get(views) isnt int ")
                print("MsgInCurChannel.to_dict().get(views) = " + str(MsgInCurChannel.to_dict().get("views")))
              
  

                  
                  
              if(spec['noDuplicates'] == 'v2'):
                if str(j) in Save[i]:
                    MTextEmb = Save[i][str(j)]['emb']
                    
                    
                    closest = Save[i][str(j)]['closest']
                    getClosestUpd(MTextEmb['vec'], prevEmb, closest)
                    Save[i][str(j)]['closest'] = closest
                else:
                    sss = getMsgFromCl(entity.username, msgId, cl)
                    if sss == None:
                        SWass.UpdateIDF(idf, str(entity.username), msgId, MTextPT['text'])
                        MTextEmb = SWass.Text2SimpleVecPP(MTextPT['text'], idf['channels'][str(entity.username)])
                    else:
                        MTextEmb = {}
                        MTextEmb['vec'] = sss['emb']
                        MTextEmb['num'] = sss['embNum']
                        if 'totalW' in sss:
                            MTextEmb['totalW'] = sss['totalW']
                        else:
                            MTextEmb['totalW'] = -1
                        
                    if MTextEmb != None:
                        Save[i][str(j)] = {}
                        Save[i][str(j)]['emb'] = MTextEmb
                        
                        Save[i][str(j)]['from_chat_id'] = entity.username
                        Save[i][str(j)]['message_id'] = msgId
                        Save[i][str(j)]['text'] = MTextPT
                        Save[i][str(j)]['postTimeTS'] = MsgInCurChannel.to_dict().get("date").timestamp()
                        Save[i][str(j)]['views'] = MsgInCurChannel.to_dict().get("views")
                        Save[i][str(j)]['embNum'] = MTextEmb['num']
                        Save[i][str(j)]['totalW'] = MTextEmb['totalW']
                        Save[i][str(j)]['Secs'] = (StartTime - MsgInCurChannel.to_dict().get("date")).total_seconds() 
                        
                        closest = getClosest(MTextEmb['vec'], prevEmb)
                        Save[i][str(j)]['closest'] = closest
                            
              if inserting:
                  counter += 1               
                  if(spec['noDuplicates'] == 'v2'):
                    if MTextEmb != None:
                    
                        msgtime = MsgInCurChannel.to_dict().get("date")
                        print("StartTime - msgtime = " + str(StartTime - msgtime))
                        Secs = (StartTime - msgtime).total_seconds() 
                    
                    
                        curPoints = (closest['Dist2'] * MsgInCurChannel.to_dict().get("views")) * pow(min(5, MTextEmb['num']), 0.5) / pow(Secs + (5 * 60), 0.7) * isFromDuplicateChannelWeigth
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
                     candidate['text'] = MTextPT
                     if(spec['noDuplicates'] == 'v2'):
                        candidate['vec'] = MTextEmb['vec']
                        candidate['num'] = MTextEmb['num']
                        candidate['totalW'] = MTextEmb['totalW']
           
          top.append(candidate['top'])     
          entitiesTop.append(candidate['entitiesTop'])
          textMsgTop.append(candidate['textMsgTop'])
          msgIdTop.append(candidate['msgIdTop'])
          
          prevIn.append(candidate['MText'])
          prevInChan.append(str(candidate['entitiesTop'].username))
          if(spec['noDuplicates'] == 'v2'):
            prevEmb.append(candidate['vec']) 
            EmbsTop.append(candidate['vec'])
            TextsTop.append(candidate['text'])
            EmbsNumTop.append(candidate['num'])
            EmbstotalWTop.append(candidate['totalW'])
      
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
            #res2[uuu // div]['val']['text'] = str(msg.get("message"))
            res2[uuu // div]['val']['text'] = TextsTop[uuu]
            if(spec['noDuplicates'] == 'v2'):
                res2[uuu // div]['val']['emb'] = EmbsTop[uuu]
                res2[uuu // div]['val']['embNum'] = EmbsNumTop[uuu]
                res2[uuu // div]['val']['totalW'] = EmbstotalWTop[uuu]
#            if textMsgTop[uuu] is not None:
#                  res2[uuu // div]['val']['text'] = str(textMsgTop[uuu].get("message"))
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
      
      
      for i in range(len(res2)):
        cl['clusters'].append({})
        LLL =  len(cl['clusters'])
        cl['clusters'][LLL - 1]['head'] = {}
        cl['clusters'][LLL - 1]['head']['from_chat_id'] = res2[i]['val']['from_chat_id']
        cl['clusters'][LLL - 1]['head']['message_id'] = res2[i]['val']['message_id'] 
        cl['clusters'][LLL - 1]['head']['text'] = res2[i]['val']['text']
        cl['clusters'][LLL - 1]['head']['emb'] = res2[i]['val']['emb']
        cl['clusters'][LLL - 1]['head']['embNum'] = res2[i]['val']['embNum']
        cl['clusters'][LLL - 1]['head']['totalW'] = res2[i]['val']['totalW']
        
        cl['clusters'][LLL - 1]['elems'] = []
      
      #removing stuff from clusters which will not exist anymore 
      while(len(cl['clusters']) > spec['noDuplicatesNum'] + len(res2)):
        for i in range(len(cl['clusters'][0]['elems'])):
            mind2 = float('inf')
            minInd = -1          
            elem = cl['clusters'][0]['elems'][i]
            for k in range(len(cl['clusters']) - (spec['noDuplicatesNum'] + len(res2)), len(cl['clusters'])):
                dist2 = vDist2(elem['emb'], cl['clusters'][k]['head']['emb'])
                if dist2 < mind2:
                    mind2 = dist2
                    minInd = k 
            cl['clusters'][minInd]['elems'].append(elem)  
        cl['clusters'].pop(0)
      
      #relocating to the clusters which just appeared news that fit them better than their previous home 
      for j in range(len(cl['clusters']) - len(res2)):
            i = 0
            while i < len(cl['clusters'][j]['elems']):
                mind2 = float('inf')
                minInd = -1          
                elem = cl['clusters'][j]['elems'][i]
                for t in range(len(cl['clusters']) - len(res2), len(cl['clusters'])):
                    dist2 = vDist2(elem['emb'], cl['clusters'][t]['head']['emb'])
                    if dist2 < mind2:
                        mind2 = dist2
                        minInd = t   
                if(mind2 < vDist2(elem['emb'], cl['clusters'][j]['head']['emb'])):
                    cl['clusters'][minInd]['elems'].append(elem)
                    cl['clusters'][j]['elems'].pop(i) 
                else:
                    i += 1
                
      #removing news which are too old
      for j in range(len(cl['clusters'])): 
            i = 0
            while i < len(cl['clusters'][j]['elems']):         
                elem = cl['clusters'][j]['elems'][i]
                hoursSinceNews = (StartTime.timestamp()  - elem['postTimeTS']) / 3600
                if(hoursSinceNews > spec['forLastXhoursInCls']):
                    cl['clusters'][j]['elems'].pop(i) 
                else:
                    i += 1     

                    
      #adding news that we just got caught to clusters 
      for i in range(len(Save)):
        for StrPostNum in Save[i]:
            Emb = Save[i][StrPostNum]['emb']['vec']
            mind2 = float('inf')
            minInd = -1    
            for k in range(len(cl['clusters'])):
               dist2 = vDist2(Emb, cl['clusters'][k]['head']['emb'])
               if dist2 < mind2:
                   mind2 = dist2
                   minInd = k
            elem = {}
            elem['emb'] = Emb
            elem['from_chat_id'] = Save[i][StrPostNum]['from_chat_id']
            elem['message_id'] = Save[i][StrPostNum]['message_id']
            elem['text'] = Save[i][StrPostNum]['text']
            elem['postTimeTS'] = Save[i][StrPostNum]['postTimeTS']
            elem["views"] = Save[i][StrPostNum]['views']
            elem["embNum"] = Save[i][StrPostNum]['embNum']
            elem["totalW"] = Save[i][StrPostNum]['totalW']
            elem["Secs"] = Save[i][StrPostNum]['Secs']
            
            #notIn = True 
            #
            #for q in range(len(cl['clusters'])):
            #    if cl['clusters'][q]['head']['from_chat_id'] == elem['from_chat_id']:
            #         if cl['clusters'][q]['head']['message_id'] == elem['message_id']:                
            #            notIn = False
            #            break
            #    for j in range(len(cl['clusters'][q]['elems'])):
            #        if cl['clusters'][q]['elems'][j]['from_chat_id'] == elem['from_chat_id']:
            #            if cl['clusters'][q]['elems'][j]['message_id'] == elem['message_id']:
            #                notIn = False
            #                break
            
            if(getMsgFromCl(elem['from_chat_id'], elem['message_id'], cl) == None):
                cl['clusters'][minInd]['elems'].append(elem)
                
      #creating top for each cluster 
      for j in range(len(cl['clusters'])): 
        cl['clusters'][j]['top'] = []
        for zzz in range(spec['clusterSize']):  
            maxPoints = -1000000
            maxPointsInd = -1
            for i in range(len(cl['clusters'][j]['elems'])):
                elem = cl['clusters'][j]['elems'][i]
                mind2 = vDist2(elem['emb'], cl['clusters'][j]['head']['emb'])
                mindk = -1
                for k in range(len(cl['clusters'][j]['top'])):
                   topElem = cl['clusters'][j]['top'][k]
                   dist2 = vDist2(elem['emb'], topElem['emb'])
                   if dist2 < mind2:
                     mind2 = dist2
                     mindk = k
                curPoints = mind2 * elem["views"] * pow(min(5, elem['embNum']), 0.5) / pow(elem['Secs'] + (25 * 60), 0.5)
                if curPoints > maxPoints:
                    maxPoints = curPoints
                    maxPointsInd = i 
                    maxPointsmind2 = mind2 
                    maxPointsmindk = mindk
            if(maxPoints > 1000):       
                cl['clusters'][j]['elems'][maxPointsInd]['maxPointsmindk'] = maxPointsmindk        
                cl['clusters'][j]['elems'][maxPointsInd]['maxPointsmind2'] = maxPointsmind2        
                cl['clusters'][j]['elems'][maxPointsInd]['maxPoints'] = maxPoints        
                cl['clusters'][j]['top'].append(cl['clusters'][j]['elems'][maxPointsInd])     
          
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
def add_msg_to_log(cl, log):
  mmm = cl['clusters'][len(cl['clusters']) - 1]['head']
  log['blocks'].append({})
  log['blocks'][len(log['blocks']) - 1]['posts'] = []
  log['blocks'][len(log['blocks']) - 1]['posts'].append({})
  log['blocks'][len(log['blocks']) - 1]['posts'][0]['text'] = mmm['text']
  log['blocks'][len(log['blocks']) - 1]['posts'][0]['channelName'] = mmm['from_chat_id']
  log['blocks'][len(log['blocks']) - 1]['posts'][0]['message_id'] = mmm['message_id']
  #log['blocks'][len(log['blocks']) - 1]['posts'][0]['dtext'] = (elRes['val']['text']).encode('utf-8', 'replace').decode()
  #print(log['blocks'][len(log['blocks']) - 1]['posts'][0]['text'])
  #print("-------------------------------")
  #print(log['blocks'][len(log['blocks']) - 1]['posts'][0]['dtext'])
  
def PrintEx(EEE, e, SSS):
   EEE.write("An exception occurred" + "\n")
   EEE.write(str(e) + "\n")
   EEE.write(SSS + "\n")
   
   print("An exception occurred")
   print(str(e))
   print(SSS)
  
def send_msg_on_telegram(type, cl, EEE, idf):
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
    racdbnNewsTestGroupBSide = type['destBSide']
    #racdbnNewsTestGroup = 'racdbn'   
    #racdbnNewsTestGroupBSide = type['destBSide'] + "TT"
    #if(type == "EN"):
    #  racdbnNewsTestGroup = 'OpenNewsAggregatorEN'
    #if(type == "RU"):  
    #  racdbnNewsTestGroup = 'OpenNewsAggregatorRUUA'

    print("send_msg2") 
    #if msg['type'] == 'text':
    # print("send_msg3") 
    # telegram_api_url = f"https://api.telegram.org/bot{API_KEY}/sendMessage?chat_id=@{racdbnNewsTestGroup}&text={msg['val']}"
    # tel_resp = requests.get(telegram_api_url)
    # if tel_resp.status_code == 200:
    #  print ("Notification has been sent on Telegram") 
    # else:
    #  print ("Could not send Message " + str(tel_resp.status_code) + str(tel_resp.text))
    # print("send_msg4")  
    
    if True:
     print("send_msg5") 
     
      

                 
     for j in range(len(cl['clusters'])):    
         time.sleep(32)
         mmm = cl['clusters'][j]['head']
         try:
             await client.forward_messages('@'+racdbnNewsTestGroupBSide, mmm['message_id'], '@'+mmm['from_chat_id'])
         except Exception as e: 
             PrintEx(EEE, e, str(mmm['message_id']) + " " + str(mmm['from_chat_id']))
         try:
             msg222 = await client.send_message('@'+racdbnNewsTestGroupBSide, "Исходный пост(↑↑↑), есть " + str(len(cl['clusters'][j]['top'])) + " близких по теме ↓↓↓:")
         except Exception as e: 
             PrintEx(EEE, e, " ")
             
         cl['clusters'][j]['head']['idInBSide'] = msg222.to_dict().get("id")
         #try:
         #    await client.send_message('@'+racdbnNewsTestGroupBSide, "id = " + str(cl['clusters'][j]['head']['idInBSide']))
         #except Exception as e: 
         #    PrintEx(EEE, e, " ")
         
         #try:
         #    await client.forward_messages('@'+racdbnNewsTestGroupBSide, cl['clusters'][j]['head']['idInBSide'], '@'+racdbnNewsTestGroupBSide)
         #except Exception as e: 
         #    PrintEx(EEE, e, "cl['clusters'][j]['head']['idInBSide'] = " + str(cl['clusters'][j]['head']['idInBSide']) + " ," +  racdbnNewsTestGroupBSide)                
         
         #try:
         #    msg222 = await client.send_message('@'+racdbnNewsTestGroupBSide, "Репост(↑↑↑), есть , j = " + str(j))
         #except Exception as e: 
         #    PrintEx(EEE, e, " ")                
         
         
         #await client.send_message('@'+racdbnNewsTestGroupBSide, "Исходный пост(↑), Head j = " + str(j))
         #await client.send_message('@'+racdbnNewsTestGroupBSide, "TOP j = " + str(j) + ",len(cl['clusters'][j]['top'] = " + str(len(cl['clusters'][j]['top'])))
         for i in range(len(cl['clusters'][j]['top'])):
             mmm = cl['clusters'][j]['top'][i]
             try:
                 await client.forward_messages('@'+racdbnNewsTestGroupBSide, mmm['message_id'], '@'+mmm['from_chat_id'])
             except Exception as e: 
                 PrintEx(EEE, e,  str(mmm['message_id']) + " " +  str(mmm['from_chat_id']))                
             
             TextMM = mmm['text']
             if 'trans2' in type:
                 if(isinstance(mmm['text'], Mapping)):
                    TextMM = mmm['text']['text']
                    if(mmm['text']['trans'] == True):
                     try:
                             await client.send_message('@'+racdbnNewsTestGroupBSide, """***Amazon Translate***
""" +mmm['text']['text'])
                     except Exception as e:
                         PrintEx(EEE, e, "Amazon Translate ")
                     #if 'ATR' in mmm['text']: 
                     #    try:    
                     #       await client.send_message('@'+racdbnNewsTestGroupBSide + "TT", mmm['text']['ATR'])
                     #    except Exception as e:
                     #       PrintEx(EEE, e, "ATR")

             if j >  len(cl['clusters']) - 3:
                SSS = "TextMM = " + str(TextMM) + ",mmm['maxPoints'] = " + str(mmm['maxPoints']) + ",mmm['maxPointsmind2'] = " + str(mmm['maxPointsmind2']) + ",mmm['maxPointsmindk'] = " + str(mmm['maxPointsmindk']) + ", str(mmm['from_chat_id']) = " + str(mmm['from_chat_id']) + ",str(mmm['message_id']) = " + str(mmm['message_id']) + ", mmm['text'] = " + str(mmm['text']) 
                SSS = SSS + "\n" + SWass.AnnotateTextWithWeights(str(TextMM), idf['channels'][str(mmm['from_chat_id'])])
                if 'totalW' in mmm:
                    SSS = SSS + ", mmm['totalW'] = " + str(mmm['totalW'])
                try:
                    #await client.send_message('@'+racdbnNewsTestGroupBSide + "TT", SSS)
                    EEE.write(SSS + "\n")
                except Exception as e: 
                    PrintEx(EEE, e,  SSS) 
         await client.send_message('@'+racdbnNewsTestGroupBSide, "*** Это все, что у нас есть, из тематически близкого. ***")
         
         
         #await client.send_message('@'+racdbnNewsTestGroupBSide, "______\n \n \n \n \n \n \n \n \n \n ______") #TT
         for i in {3}:
             try:
                #await client.send_message('@'+racdbnNewsTestGroupBSide, 'b' + str(i))
                await client.forward_messages('@'+racdbnNewsTestGroupBSide, i, '@'+racdbnNewsTestGroupBSide)
                #await client.send_message('@'+racdbnNewsTestGroupBSide, 'e' + str(i))
             except Exception as e: 
                PrintEx(EEE, e,  " ")        
    
     mmm = cl['clusters'][len(cl['clusters']) - 1]['head']
     #print("racdbnNewsTestGroup = " + str(racdbnNewsTestGroup) + ",msg['val']['message_id'] = " + str(msg['val']['message_id']) + ",msg['val']['from_chat_id'] = " + str(msg['val']['from_chat_id']))
     try:
         await client.forward_messages('@'+racdbnNewsTestGroup, mmm['message_id'], '@'+mmm['from_chat_id']) 
     except Exception as e: 
         PrintEx(EEE, e, str(mmm['message_id']) + " " + str(mmm['from_chat_id']))
     
     if 'trans2' in type:
             #mmm = cl['clusters'][len(cl['clusters']) - 1]['head']               
             
             TextMM = mmm['text']
             if 'trans2' in type:
                 if(isinstance(mmm['text'], Mapping)):
                    TextMM = mmm['text']['text']
                    if(mmm['text']['trans'] == True):
                     try:
                             await client.send_message('@'+racdbnNewsTestGroup, """***Amazon Translate***
""" +mmm['text']['text'])
                     except Exception as e:
                         PrintEx(EEE, e, "Amazon Translate ")     
#         if(len(msg['val']['text']) > 0):
#             sourceT = msg['val']['text']
#             try:
#                 clientBoto = boto3.client('translate', region_name="ap-southeast-1")
#                 result = clientBoto.translate_text(Text=sourceT, SourceLanguageCode="auto", TargetLanguageCode = type['trans2'])        
#                 if result['SourceLanguageCode'] == type['trans2']:
#                     print('Already ' + type['trans2'])    
#                 else:
#                     await client.send_message('@'+racdbnNewsTestGroup, """***Amazon Translate***
#""" +result['TranslatedText'])
#             except Exception:
#                 pass           
     
     lastClHead = cl['clusters'][len(cl['clusters']) - 1]['head']
     try:
         EEE.write("Trying to do the linking to B-side")
         EEE.write("racdbnNewsTestGroup = " + racdbnNewsTestGroup)
         EEE.write("racdbnNewsTestGroupBSide = " + racdbnNewsTestGroupBSide)
         EEE.write("str(lastClHead['idInBSide']) = " + str(lastClHead['idInBSide']))
         msg222 = await client.send_message('@'+racdbnNewsTestGroup, "У нас есть еще " + str(len(cl['clusters'][len(cl['clusters']) - 1]['top'])) + " новостей близких по теме тут: https://t.me/" + racdbnNewsTestGroupBSide + "/" + str(lastClHead['idInBSide']), link_preview=False) 
     except Exception as e: 
         PrintEx(EEE, e, " ")
     cl['clusters'][j]['head']['idInMain'] = msg222.to_dict().get("id")
     
     for i in range(len(cl['clusters']) - 1):
         CLR = cl['clusters'][i]
         SSS = "У нас есть еще " + str(len(cl['clusters'][i]['top'])) + " новостей близких по теме тут: https://t.me/" + racdbnNewsTestGroupBSide + "/" + str( CLR['head']['idInBSide'])
         if type['maxClustersNum'] == len(cl['clusters']):
             if i == 0:
                 SSS = SSS + " (архив)"
         try:
             if 'idInMain' in CLR['head']:
                 print("trying to edit msg = " + str(CLR['head']['idInMain']))
                 await client.edit_message('@'+racdbnNewsTestGroup, CLR['head']['idInMain'], SSS, link_preview=False) 
         except Exception as e: 
             PrintEx(EEE, e, " ")   


             #print('Now')
     #except OSError:
     #   telegram_api_url = f"https://api.telegram.org/bot{API_KEY}/sendMessage?chat_id=@{racdbnNewsTestGroup}&text={'fail (privacy?) to load @' + msg['val']['from_chat_id']}"  
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
      now = datetime.now()
      with open('Exceptions\\Exc-[' + str(now).replace(".", "p").replace(":", "d") + ']' + '.txt', 'w', encoding="utf-8") as EEE:   
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
          
          spec = {'type': 'repo', 'source': 'SourceRU.json', 'numTotal': 1, 'noDuplicatesNum': 10, 'noDuplicatesTresh': 0.7, 'forLastXhours': 6, 'forLastXhoursInCls': 12, 'noChannelDuplicatesNum': (7 * 5), 'noDuplicates' : 'v2', 'lastNewsCap': 5, 'trans2': 'ru', 'clusterSize': 25}

          #res = []
          
          now = datetime.now()
          FN = spec['source'].rsplit(".",1)[0] + '-[' + str(now).replace(".", "p").replace(":", "d") + '].log' 
          log = {'saveFile': FN}
          log['blocks'] = []      
          
          clFN = "CLS-" + spec['source'].rsplit(".",1)[0] + '-[' + str(now).replace(".", "p").replace(":", "d") + '].txt' 
          cl = {'saveFile': clFN}
          cl['clusters'] = []
          
          idfFN = "IDF-" + spec['source'].rsplit(".",1)[0] + ".txt"
          idf = {'saveFile': idfFN}
          idf['channels'] = {}
          getPrevIdf(idf)
          
          #ChInfoList = grabChInfo(spec)
          ChInfoList = grabChInfo(spec)
          res =  grabTheTop(spec, ChInfoList, cl, idf)
          
          for i in range(0, len(res)):
            print("t4") 
            #print("i = " + str(len(res) - i - 1))
            #print(res[len(res) - i - 1])
            #send_msg_on_telegram(res[len(res) - i - 1], {'dest': 'OpenNewsAggregatorRUUA', 'trans2': 'ru'})
            send_msg_on_telegram({'dest': 'OpenNewsAggregatorRUUA', 'destBSide': 'OpenNewsAggregatorRUUA_BSides', 'trans2': 'ru', 'maxClustersNum': (spec['numTotal'] + spec['noDuplicatesNum'])}, cl, EEE, idf)
            add_msg_to_log(cl, log)
          
          with open('logs\\' + log['saveFile'], 'w') as f:
            prettylog = json.dumps(log, indent=4)
            f.write(prettylog)
            f.close()      
            
          with open('logs\\' + cl['saveFile'], 'w') as f:
            prettylog = json.dumps(cl, indent=4)
            f.write(prettylog)
            f.close()          
            
          with open(idf['saveFile'], 'w') as f:
            prettylog = json.dumps(idf, indent=4)
            f.write(prettylog)
            f.close()
            
          deleteOldCls(spec)  
          
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
          EEE.close()
          
      www = (3600 * 3 * 0.2) - (endTime - startTime).total_seconds()
      if(www > 0):
         time.sleep(www + 180)