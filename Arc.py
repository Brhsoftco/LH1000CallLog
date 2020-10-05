#generic imports
import requests
import base64
import hashlib
import time
import math
import json
import re
import pandas as pd
import os

#######################################
### MODEM IP ADDRESS (MUST UPDATE!) ###
#######################################
modem_ip = "192.168.0.1"

#this is a global, so it goes first
session_requests = requests.session()

def consoleClear():
    os.system('cls' if os.name == 'nt' else 'clear')

def sha512(text):
    return hashlib.sha512(text.encode()).hexdigest()

def md5(text):
    return hashlib.md5(text.encode()).hexdigest()

def ArcMd5(text):
    return sha512(md5(text))
    
def contains(original, compare):
    return original.find(compare) > -1

def dictString(obj):
    return json.dumps(obj, indent=4, sort_keys=True)

def isHtml(pageResponse):
    return contains(pageResponse, '<!DOCTYPE html')

def isLogin(pageHtml):
    if isHtml(pageHtml):
        if contains(pageHtml, 'setTimeout("reload()",500);'):
            return True
        elif contains(pageHtml, 'name="loginForm"'):
            return True
    #default
    return False

def text(elt):
    return elt.text_content().replace(u'\xa0', u' ')

def noTrailingComma(text):
    return re.sub("/,\s*$/", "", text)
    
def findTokenHtml(pageHtml):
    #locate the base64 hidden in the 'spacer' div
    token = base64.b64decode( # The token is stored hidden in the base 64
        re.search('data:image/gif;base64,[^"]+', # of an inline image in the page
                  pageHtml).group(0)[78:]) # right at the very end!
    
    #token base64 is decoded and returned
    return token.decode()

def findToken(url = ""):
    #modem IP is made accessible
    global modem_ip
    
    #default to login page if nothing else is specified
    if url == "":
        url = "http://" + modem_ip + "/login.htm"
    
    #report status
    print("Obtaining token: " + url)
    
    #download page HTML
    response = session_requests.get(url)
    
    #base64 find and decode
    return findTokenHtml(response.text)

def fetchWithReferrer(url, referer_):
    #server POST and store reply
    result = session_requests.get(
        url, 
        headers = dict(
            origin="http://" + modem_ip,
            referer=referer_
        )
    )
    return result

def callLogToDict(jsText):
    regEx = "logs = [^\]]*"
    log = re.search(regex, jsText).group(0)
    log = noTrailingComma(log)
    
def tokenise(url, token, silent = False):
    #UNIX epoch
    currentEpoch = int(time.time())
    url = url + "?_tn=" + token + "&_t=" + str(currentEpoch) + "&_=" + str(currentEpoch + 1)
    if not silent:
        print('Tokenise: ' + url)
    return url
    
def cgiInit(token = "", url = ""):
    #fetch a new token if necessary
    if token == "":
        if url != "":
            token = findToken(url)
        else:
            url = "http://" + modem_ip + "/mmpbx_book.htm?m=adv"
            token = findToken(url)
    
    url = "http://" + modem_ip + "/cgi/cgi_init.js"
    url = tokenise(url, token)
    response = fetchWithReferrer(url, "http://" + modem_ip + "/mmpbx_book.htm?m=adv")
    
    return response.text

def callLogJS(silent = False):
    #modem IP is made accessible
    global modem_ip
    
    if not silent:
        print("Downloading script...")
    
    log_url = "http://" + modem_ip + "/mmpbx_book.htm?m=adv"
    url = "http://" + modem_ip + "/cgi/cgi_tel_call_list.js"
    
    #new token for new page
    url = tokenise(url, findToken(log_url), silent)
    r = fetchWithReferrer(url, log_url)
    
    if not silent:
        print("Call Log Get: " + url + "\n")
    
    return r.text
    
def callLogJson(silent = False):
    j = callLogJS(silent)
    value = re.findall(r'voip_call_logs.*?=\s*(.*?);', j, re.DOTALL | re.MULTILINE)[0]
    
    #cleans the newline and trailing comma
    value = value[:-3] + ']'
    
    #cleans the newline
    value = '[' + value[2:]
    
    #reencodes the result as JSON data
    return json.loads(value)
    
def silentPandasCallLog():
    #download the authorised call log silently (don't print anything)
    json = callLogJson(True)
    gexpTrim = r'/^\s+|\s+$/gm';
    
    #printable dataframe list
    printList = []
    
    #caller log column definitions
    columnDefs = [
        "Type",
        "Time",
        "Duration",
        "Caller",
        "VOIP #",
        "Handset",
        "Loss",
        "Jitter",
        "Latency",
        "Status",
        "Event"
    ]
    
    #build dictionary
    for call in json:
        
        #don't operate on null values
        if call is None or call == '':
            continue
        
        #split entries at comma
        lineSplit = call.split(",")
        
        #RegEx and display name-cleaning
        for i in lineSplit:
            
            #Regex
            if i == None:
                i = 'null'
            else:
                i = re.sub(gexpTrim, '', i)
                
            #name-cleaning
            i = i.split("|")[0]
                
        #add new list to array
        printList.append(lineSplit)
    
    #pandas DataFrame (for table printing)
    df = pd.DataFrame(printList)
    
    #apply new labelled column names
    df.columns = columnDefs
    
    #return the full DataFrame
    return df
    
def printCallLogTable():
    #clear console of existing crap
    consoleClear()
    
    print("\nObtaining call log data...\n")
    
    df = silentPandasCallLog()
    
    #allow full DataFrame printing
    pd.set_option("display.max_rows", None, "display.max_columns", None, "display.width", None)
    
    #finally, print to the console
    print(df)
    print('\n\n')
    
def ArcLogin(un, pw):
    #hashing digest
    un = ArcMd5(un)
    pw = ArcMd5(pw)