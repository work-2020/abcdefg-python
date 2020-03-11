# -*- coding: utf-8 -*-
"""
Created on Sat Mar  7 15:56:12 2020

@author: PC
"""

# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from bs4 import BeautifulSoup
import requests
import time
import json

sess = requests.Session()
headers = {}
def tags_val(tag, key='', index=0):
    if len(tag) == 0 or len(tag) <= index:
        return ''
    elif key:
        txt = tag[index].get(key)
        return txt.strip(' \t\r\n') if txt else ''
    else:
        txt = tag[index].text
        return txt.strip(' \r\t\n') if txt else ''

def login(user,pwd):
    url_login = 'https://passport.jd.com/new/login.aspx'
    try:
        resp = sess.get(url_login)
        #print(resp.text)
        soup = BeautifulSoup(resp.text, 'lxml')
        display = soup.selecct('#o-authcode')[0].get('style')
        if not display:
            print('需要验证码')
            auth_code_url = soup.select('#JD_Verification1')[0].get('src2')
                                        
        uuid = soup.select('#uuid')[0].get('value')
        eid = soup.select('#eid')[0].get('value')
        print(uuid)                
    except Exception as e:
        print('Exp {0}'.format(e))

def good_detail(stock_id, area_id=None):
    good_data = {
        'id': stock_id,
        'name': '',
        'link': '',
        'price': '',
        'stockState': '',
        'stockStateName': '',
    }
    
    try:
        stock_link = 'https://item.jd.com/{0}.html'.format(stock_id)
        resp = sess.get(stock_link)
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        tags = soup.select('div#name h1')
        if len(tags) == 0:
            tags = soup.select('div.sku-name')
        good_data['name'] = tags[0].text.strip()
        
        tags = soup.select('a#InitCartUrl')
        link = tags_val(tags, key='href')
        if link[:2] == '//':
            link = 'https:' + link
        good_data['link'] = link
        #print(tags_val(tags, key='href'))
    except Exception as e:
        print('Exp {0}'.format(e))
        
    good_data['price'] = good_price(stock_id)
    good_data['stockState'], good_data['stockStateName'] = good_stock(stock_id=stock_id, area_id=area_id)

    print('商品详情')
    print('名称: {0}'.format(good_data['name']))
    print('编号: {0}'.format(good_data['id']))
    print('库存: {0}'.format(good_data['stockStateName']))
    print('价格: {0}'.format(good_data['price']))
    print('链接: {0}'.format(good_data['link']))
    
    return good_data

def good_price(stock_id):
    url = 'https://p.3.cn/prices/mgets'
    payload = {
        'type'    : '1',
        'pduid'   : int(time.time()*1000),
        'skuIds'  : 'J_' + stock_id,
    }
    price = '?'
    try:
        resp = sess.get(url, params=payload)
        price = json.loads(resp.text[1:-2]).get('p')
    except Exception as e:
        print('Exp {0}'.format(e))
    return price
     
def good_stock(stock_id, area_id=None):
    stock_url = 'http://c0.3.cn/stocks'
    payload = {
        'type'    : 'getstocks',
        'skuIds' : stock_id,
        'area'    : area_id or '22_1930_50947_52198',
    }
    
    try:
        resp = sess.get(stock_url, params=payload)
        if resp.status_code != requests.codes.OK:
            print('获取商品库存失败！{0}'.format(resp.text))
            return (0,'')
        stock_info = json.loads(resp.text)
        return(stock_info[stock_id]['StockState'],stock_info[stock_id]['StockStateName'])
    except Exception as e:
        print('Exp {0}'.format(e))
        
def buy(stock_id, count):
    good_data = good_detail(stock_id)
    while_count = 0
    while good_data['stock'] != 33 and while_count < 10:
        time.sleep(3)
        good_data['stock'], good_data['stockName'] = good_stock(stock_id = stock_id)
        while_count = while_count + 1
    
    link = good_data['link']
    if good_data['stock'] != 33 or link == '':
        return False
    
    if count != 1:
        link = link.replace('pcount=1','pcount={0}'.format(count))
    #resp = sess.get(link, cookies=cookies)
        
    
if __name__ == '__main__':
    #good_detail('18625729281')
    login('work_2020', 'bTE7LRXmWjMKQ+QrwADnALR05smJFIi39WdiGSfvUZK1krFC8kZULgkC2MJgFso9UOe8aDZIG44OIVKqz06ug71HyFIaRUglPbo+sh6/IgEYez+9JZU+wQqAa0I3jMggjYJwXKa2Jbshlk6Ec3IqOlP0qHDd8RlFJ/MevHxwkCw=')