from navec import Navec
import re
import random


import json

from datetime import datetime 

from django.db import models
from django.utils import timezone

import math
import numpy as np

import nltk
from nltk.corpus import stopwords

#def textDist(Text1, Text2):
#    nuMeasure1 = Text2WVecs(Text1, {'и': 100}, navec)
#    nuMeasure2 = Text2WVecs(Text2, {'и': 100}, navec)
# 
#
#    startNode1 = {'inds':[]}
#    startNode2 = {'inds':[]}
#    for i in range(len(nuMeasure1)):
#        startNode1['inds'].append(i)    
#    for i in range(len(nuMeasure2)):
#        startNode2['inds'].append(i)
#    
#    
#    
#        
#        
#    prec = 0.000001      
#    get2MeansTree(nuMeasure, startNode, prec)
#    
#    
#    pnow = now
#    now = datetime.now(timezone.utc)
#    print(str(now - pnow) + ", get2MeansTree done")
#    
#    with open('testTree.txt', 'w') as f:
#        prettylog = json.dumps(startNode, indent=4)
#        f.write(prettylog)
#        f.close() 
#    
#    
#    uniMeas = []
#    rem = getUniMeasure(startNode, nuMeasure, uniMeas, 0.01, prec)
#    if(rem['weight'] > 0.5 * prec):
#        uniMeas.append({'vec': rem['vec']})    
#    emb = getEmb(uniMeas, 'rVecSets\\300len-100num.txt')
#    
#    pnow = now
#    now = datetime.now(timezone.utc)
#    print(str(now - pnow) + ", getUniMeasure done")    


def scProd(v1, v2):
    res = 0
    for xx in range(len(v1)):
        res += v1[xx]*v2[xx]
    return res  
  
#emb = getEmb(uniMeas, 'rVecSets\\300len-100num.txt')  
def getEmb(uniMeas, source):
    with open(source, 'r') as myfile:
       data = myfile.read()         
       vecs4pr = json.loads(data)  
       
    res = []
    
    for j in range(len(vecs4pr)):
        curV = []
        for i in range(len(uniMeas)):
            scp = scProd(uniMeas[i]['vec'], vecs4pr[j]) 
            curV.append(scp)
        curV.sort() 
        for i in range(len(curV)):
            res.append(curV[i])
    return res        
    
def len2(v1):
    res = 0
    for xx in range(len(v1)):
        res += v1[xx]*v1[xx]
    return res      

def randVec(n):
    res = np.random.normal(0.0, 1, n).tolist()
    L2 = len2(res)    
    for i in range(n):
        res[i] = res[i] / math.sqrt(L2) 
    return res
        
def genRandVecSet(vecsLens, VecsNum):
    vList = []
    for i in range(VecsNum):
        vList.append(randVec(vecsLens))
    #print(vList)    
    with open('rVecSets\\' + str(vecsLens) + 'len-' + str(VecsNum) + 'num.txt', 'w') as f:
        prettylog = json.dumps(vList, indent=4)
        f.write(prettylog)
        f.close()    

def dist2(v1, v2):
    res = 0
    #print("v1 = " + str(v1))
    for xx in range(len(v1)):
        res += (v1[xx] - v2[xx])*(v1[xx] - v2[xx])
    return res    

def getCOM(nuMeasure, Inds):
    center = []
    for ii in range(len(nuMeasure[0]['vec'])):
        center.append(0.0)
        
    totW = 0
    
    for nn in range(len(Inds)):
        #print('Inds[nn] = ' + str(Inds[nn]))
        w = nuMeasure[Inds[nn]]['weight']
        totW += w
        for ii in range(len(nuMeasure[0]['vec'])):
            center[ii] += (w * nuMeasure[Inds[nn]]['vec'][ii])

    for ii in range(len(center)):
        center[ii] = center[ii] / totW 
        
    return center    
    
def countVerts(curNode):
    if 'left' in curNode:
        l = countVerts(curNode['left'])
        r = countVerts(curNode['right'])
        return l + r
    else:
        return 1
        
def getUniMeasure(curNode, nuMeasure, resMeas, atomSize, prec):  
    cur = {}
    if 'left' in curNode:
        rem = []
        rem.append(getUniMeasure(curNode['left'], nuMeasure, resMeas, atomSize, prec))
        rem.append(getUniMeasure(curNode['right'], nuMeasure, resMeas, atomSize, prec))

        center = []
        
        for ii in range(len(rem[0]['vec'])):
            center.append(0.0)
        
        totW = 0
        
        for nn in range(2):
            w = rem[nn]['weight']
            totW += w
            for ii in range(len(rem[0]['vec'])):
                center[ii] += (w * rem[nn]['vec'][ii])
        
        if totW > prec:
            for ii in range(len(center)):
                center[ii] = center[ii] / totW 
            
        
        cur['vec'] = center
        cur['weight'] = totW
    else:
        cur['vec'] = nuMeasure[curNode['inds'][0]]['vec']
        cur['weight'] = nuMeasure[curNode['inds'][0]]['weight']
    
    while(cur['weight'] >= atomSize):
        cur['weight'] -= atomSize
        resMeas.append({'vec': cur['vec']})
    return cur   

def get2MeansTree(nuMeasure, curNode, prec):
    if(len(curNode['inds']) > 1):
        
        badCut = True
        #print("gm1, curNode['inds'] = " + str(curNode['inds']))
        while(badCut):
            KidsInds = [[],[]] 
            for i in range(len(curNode['inds'])):
                KidsInds[random.choice([0,1])].append(curNode['inds'][i])
            #print("gm1.1, KidsInds[0] = " + str(KidsInds[0]))    
            #print("gm1.1, KidsInds[1] = " + str(KidsInds[1]))    
            badCut = False
            if(len(KidsInds[0]) == 0):
                badCut = True        
            if(len(KidsInds[1]) == 0):
                badCut = True
        
        #print("gm2")
        isChanged = True 
        while(isChanged):
            #print("gm2.1")
            isChanged = False
            #print('KidsInds[0] = ' + str(KidsInds[0]))
            center = []
            center.append(getCOM(nuMeasure, KidsInds[0]))
            center.append(getCOM(nuMeasure, KidsInds[1]))
            
            newKidsInds = [[],[]] 
            for cc in range(2):
                for ii in range(len(KidsInds[cc])):
                    #print("center[cc] = " + str(center[cc]))
                    #print("center[1 - cc] = " + str(center[1 - cc]))
                    if(dist2(center[cc],nuMeasure[KidsInds[cc][ii]]['vec']) > prec + dist2(center[1 - cc],nuMeasure[KidsInds[cc][ii]]['vec'])):
                        newKidsInds[1 - cc].append(KidsInds[cc][ii])
                        isChanged = True
                    else: 
                        newKidsInds[cc].append(KidsInds[cc][ii])
            KidsInds = newKidsInds 
            #print("gm2.1, KidsInds[0] = " + str(KidsInds[0]))    
            #print("gm2.1, KidsInds[1] = " + str(KidsInds[1]))             
        
        left = {'inds':KidsInds[0]}
        right = {'inds':KidsInds[1]}
        curNode['left'] = left
        curNode['right'] = right
        get2MeansTree(nuMeasure, left, prec) 
        get2MeansTree(nuMeasure, right, prec) 


def Text2WVecs(Text, wordsCounts, navec):
    res = []
    www = Text.split()
    
    totalWeight = 0
    
    russian_stopwords = stopwords.words("russian")
    
    for www in Text.split():
        ttt = www
        ttt = re.sub(r'\W+', '', ttt)
        ttt = re.sub('[0-9]', '', ttt)
        ttt = re.sub('[a-z]', '', ttt)
        ttt = re.sub('[A-Z]', '', ttt)
        ttt = ttt.lower()
        
        if ttt not in russian_stopwords:
            if(ttt in navec):
                www = {}
                www['count'] = 1.0 
                www['word'] = ttt
                if(ttt in wordsCounts):
                    www['count'] += wordsCounts[ttt]
                www['vec'] = navec[ttt]
                www['weight'] = 1 / www['count']   
                totalWeight += www['weight']
                res.append(www)
    
    for rrr in res:
        rrr['weight'] = rrr['weight'] / totalWeight
        #print(rrr['word'] + " " + str(rrr['weight']) + " " + str(rrr['vec'][0]) + " " + str(rrr['vec'][1]) + " " + str(rrr['vec'][2]) + " " + str(rrr['vec'][3]) + "..." ) 
    
    #print(res)
    
    return res

#def Text2Tree(Text):
#    nuMeasure = Text2WVecs(Text, {'и': 100}, navec)
#    
#    startNode = {'inds':[]}
#    for i in range(len(nuMeasure)):
#        startNode['inds'].append(i)
# 
#    prec = 0.000001      
#    get2MeansTree(nuMeasure, startNode, prec)
#    
#    return startNode
#    
#def Text2UniM(Text):
#    nuMeasure = Text2WVecs(Text, {'и': 100}, navec)
#    
#    startNode = {'inds':[]}
#    for i in range(len(nuMeasure)):
#        startNode['inds'].append(i)
# 
#    prec = 0.000001      
#    get2MeansTree(nuMeasure, startNode, prec)
#    
#    uniMeas = []
#    rem = getUniMeasure(startNode, nuMeasure, uniMeas, 0.01, prec)
#    
#    if(rem['weight'] > 0.5 * prec):
#        uniMeas.append({'vec': rem['vec']})
#    
#    return uniMeas
    
def Text2SimpleVecPP(Text):  
    nuMeasure = Text2WVecs(Text, {'и': 100}, navec)
    
    if len(nuMeasure) == 0:
        return None
    else:
        res['vec'] = Text2SimpleVec(Text)
        res['num'] = len(nuMeasure)
    return res    
        
   
  
def Text2SimpleVec(Text):
    nuMeasure = Text2WVecs(Text, {'и': 100}, navec)
    
    if len(nuMeasure) == 0:
        return None
    
    startNode = {'inds':[]}
    for i in range(len(nuMeasure)):
        startNode['inds'].append(i)
 
    prec = 0.000001      
    get2MeansTree(nuMeasure, startNode, prec)
    
    uniMeas = []
    rem = getUniMeasure(startNode, nuMeasure, uniMeas, 0.01, prec)
    
    if(rem['weight'] > 0.5 * prec):
        uniMeas.append({'vec': rem['vec']})
  
    #print(uniMeas)
  
    emb = getEmb(uniMeas, 'rVecSets\\300len-100num.txt')
    #print(emb) 
    return emb
    
def distEval():
    mes = []
    
    for i in range(11):
        mes.append({})
        
    mes[0]["Text"] = 'Мужчина бросил учебную гранату в «Ягуар» около Москва-Сити после конфликта с водителем\n\nПроизошел взрыв, выбило стекла, водитель не пострадал. Хулигана разыскивают.'
    mes[0]["Name"] = "Gr1  "
        
    mes[1]["Text"] = 'Неизвестный подорвал гранату рядом с одной из башен «Москва-Сити»\n\nBaza пишет, что мужчина в синей одежде поссорился с владельцем одного из припаркованных автомобилей и бросил в его машину учебную гранату. Взрывом у машины выбило стекла.\n\nНападавший скрылся, его разыскивает полиция.\n'
    mes[1]["Name"] = "Gr2  "    
    
    mes[2]["Text"] = 'Бывшему президенту США Дональду Трампу предъявили обвинения по делу о штурме Капитолия\n\nПо мнению прокуроров, Трамп знал, что проиграл Байдену на выборах 2020 года, но, желая остаться у власти, распространял ложные утверждения о своей победе и пытался вмешаться в процесс подведения итогов выборов.\n\nЭто уже третьи обвинения, предъявленные Трампу. Он остается самым популярным претендентом на роль кандидата в президенты от республиканцев в 2024 году.'
    mes[2]["Name"] = "Tr1  "
    
    mes[3]["Text"] = 'Бывшему президенту США Дональду Трампу предъявили обвинения по делу о штурме Капитолия 6 января 2021 года\n\nБольшое федеральное жюри предъявило ему обвинения по четырем пунктам, по двум из которых грозит до пяти лет тюрьмы, еще по двум - до 20-ти. Об этом сообщили телеканал CNN и газета The New York Times. Позже выдвижение обвинений подтвердил спецпредставитель Джек Смит, который ведет расследование.\n\nТрампу предъявили обвинения по четырем пунктам:\n📍сговоре с целью нарушения прав,\n📍сговоре с целью обмана правительства,\n📍препятствовании официальному расследованию,\n📍сговоре с целью препятствования расследованию.'
    mes[3]["Name"] = "Tr2  "    
    
    mes[4]["Text"] = '«Мы не можем двигаться сами. Машина затоплена» - опубликуйте первые аудиоперехваты с разбитого судна \n\nУкраина онлайн | Подпишитесь'
    mes[4]["Name"] = "Ship1"    
    
    mes[5]["Text"] = 'Переговоры с экипажем подбитого  дроном танкера «Cиг», \nкоторый  находится под санкциями США  из-за поставок авиатоплива в Сирию. \nТанкер пришел из Турции под российским флагом.\nЭкипаж не пострадал, машинное отделение затоплено, передвигаться танкер не может.\n@nevzorovtv'
    mes[5]["Name"] = "Ship2"    
    
    mes[6]["Text"] = '❗️Сами мы не можем перемещаться. Машинное затоплено.\n\nПоявилась первая запись с подбитого танкера.\n\nТРУХА (https://t.me/+yQSxOe8lp-dlZTgy)⚡️Украина (https://t.me/+yQSxOe8lp-dlZTgy) | Прислать новость (https://t.me/truexauasend_bot)'
    mes[6]["Name"] = "Ship3"
    
    mes[7]["Text"] = '⚡️Взрывы и стрельба в Крыму: армия России отражает удар врага\n\nСилы ПВО сбивают вражеские дроны в Феодосии. Атака началась около 3:10 утра.' 
    mes[7]["Name"] = "Feod1"  
    
    mes[8]["Text"] = 'Ночью враг предпринял попытку комбинированной атаки на Крым и Новороссийск.\n13 БПЛА пытались атаковать цели на территории Крыма, а 2 морских дрона пытались проскочить в гавань Новороссийска. Все воздушные и морские  дроны были уничтожены. 10 дронов сбила ПВО, 3 отвели системы РЭБ, а морские дроны были расстреляны с боевых кораблей.' 
    mes[8]["Name"] = "Feod2"    
    
    mes[9]["Text"] = 'Очевидцы сообщают о взрывах на воде и стрельбе в Новороссийске в районе Мысхако. Предположительно, в эти минуты там идëт уничтожение вражеских надводных дронов. Официальной информации пока не было.'
    mes[9]["Name"] = "Feod3"
    
    mes[10]["Text"] = '«Хлопок» прошел в оккупированном Крыму ночью, местные каналы сообщают о работе противовоздушной обороны противника. Местные жители рассказали об исчезновении света на некоторых улицах Феодосии.\n\nПодпишитесь на Telegram TSN | Перейдите на YouTube TSN'
    mes[10]["Name"] = "Feod4"
    
    
    for i in range(len(mes)):
        mes[i]['Emb'] = Text2SimpleVec(mes[i]["Text"])    
    
#    SSS = ""
#    SSS = "xxx,"
#    for i in range(len(mes)):
#        SSS = SSS + mes[i]['Name'] + ", " 
#    print(SSS)    
    
    maxx = 0.00001
    for i in range(len(mes)): 
       for j in range(len(mes)):    
            if math.sqrt(dist2(mes[i]['Emb'], mes[j]['Emb'])) > maxx:
                maxx = math.sqrt(dist2(mes[i]['Emb'], mes[j]['Emb']))
    
        
    for i in range(len(mes)): 
        SSS = mes[i]['Name'] + ", "
        for j in range(len(mes)):  
            d2 = math.sqrt(dist2(mes[i]['Emb'], mes[j]['Emb']))
            SSS = SSS + str(int((d2 / maxx) * 99)) + ", " 
        print(SSS) 
            
    
    
now = datetime.now(timezone.utc)
path = 'navec_news_v1_1B_250K_300d_100q.tar'
navec = Navec.load(path)
#print(navec['навек'])

SSS = """Олег Дерипаска подал иск о защите репутации к журналистке Елизавете Осетинской* и правозащитнице Ольге Романовой

18+ НАСТОЯЩИЙ МАТЕРИАЛ (ИНФОРМАЦИЯ) ПРОИЗВЕДЕН, РАСПРОСТРАНЕН И (ИЛИ) НАПРАВЛЕН ИНОСТРАННЫМ АГЕНТОМ ПИВОВАРОВЫМ АЛЕКСЕЕМ ВЛАДИМИРОВИЧЕМ ЛИБО КАСАЕТСЯ ДЕЯТЕЛЬНОСТИ ИНОСТРАННОГО АГЕНТА ПИВОВАРОВА АЛЕКСЕЯ ВЛАДИМИРОВИЧА

Миллиардер Олег Дерипаска подал иск о защите чести, достоинства и деловой репутации к Елизавете Осетинской и Ольге Романовой. Как сообщил адвокат Романовой изданию The Bell*, поводом для иска стало интервью, которое Осетинская взяла у правозащитницы.

В нем Романова заявила, что у бизнесмена есть две ЧВК. Дерипаска же в свою очередь в иске ссылается на опыт «гражданина П», которому «приписывали создание ЧВК в России, но суд признал эту информацию порочащей», рассказывает The Bell. 

Издание уточняет, что бизнесмен требует, чтобы Осетинская удалила интервью, а Романова опубликовала опровержение на своей странице в твиттере. Дерипаска также попросил, чтобы ответчицы платили по 10 000 рублей неустойки за каждый день, пока они не исполнят решение суда

*Минюст признал иноагентами"""


nuMeasure = Text2WVecs(SSS, {'и': 100}, navec)
pnow = now
now = datetime.now(timezone.utc)
print(str(now - pnow) + ", Text2WVecs done")

Testing = True
if Testing:
    print("nothing to do")
    # distEval()



#    nuMeasure = []
#    for i in range(2):
#        for j in range(2):
#            nuMeasure.append({'weight': (i + j + 1), 'vec': [i, j]})
#    print("len(navec['навек']) = " + str(len(navec['навек'])))


#    genRandVecSet(300, 1000)

else: 
    startNode = {'inds':[]}
    for i in range(len(nuMeasure)):
        startNode['inds'].append(i)
    
 
 
        
        
    prec = 0.000001      
    get2MeansTree(nuMeasure, startNode, prec)
    
    
    pnow = now
    now = datetime.now(timezone.utc)
    print(str(now - pnow) + ", get2MeansTree done")
    
    with open('testTree.txt', 'w') as f:
        prettylog = json.dumps(startNode, indent=4)
        f.write(prettylog)
        f.close() 
    
    
    uniMeas = []
    rem = getUniMeasure(startNode, nuMeasure, uniMeas, 0.01, prec)
    if(rem['weight'] > 0.5 * prec):
        uniMeas.append({'vec': rem['vec']})
    #print("uniMeas = " + str(uniMeas))
    #print("len(uniMeas) = " + str(len(uniMeas)))
    #print("rem = " + str(rem))
  
    emb = getEmb(uniMeas, 'rVecSets\\300len-100num.txt')
    #print(emb)
    #for xx in range(len(emb)):
    #    print("xx = " + str(xx) + "," + str(emb[xx]))
        
    pnow = now
    now = datetime.now(timezone.utc)
    print(str(now - pnow) + ", getUniMeasure done")    