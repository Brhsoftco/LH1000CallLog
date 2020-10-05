#!/usr/bin/python3

from Arc import *
import sys
import requests
from lxml import html
import pandas as pd



login_url_initial = "http://" + modem_ip + "/login.htm"
result = session_requests.get(login_url_initial)

#use Arc.py's findToken
authenticity_token = findToken()

##############################################
### MODEM LOGIN CREDENTIALS (MUST UPDATE!) ###
##############################################
usr = "admin"
pws = "Telstra"

#hash transforms for the credentials above
usr = ArcMd5(usr)
pws = ArcMd5(pws)

#post data
payload = {
    "usr": usr, 
    "pws": pws, 
    "httoken": authenticity_token
}

#post URL
login_url_second = "http://" + modem_ip + "/login.cgi"

#server POST and store reply
result = session_requests.post(
    login_url_second, 
    data = payload, 
    headers = dict(
        origin="http://" + modem_ip,
        referer=login_url_initial
    )
)

#inform user
print("get table and parse...\n")

#call log URL
url = 'http://' + modem_ip + '/mmpbx_log.htm?m=adv'
r = requests.get(url)
tree = html.fromstring(r.text)

#print(r.content)

printCallLogTable()

print("logout...")
logout_url = "http://" + modem_ip + "/logout.cgi?_tn=" + authenticity_token
result = session_requests.get(logout_url)