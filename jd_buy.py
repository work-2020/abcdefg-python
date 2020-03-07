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

def tags_val(tag, key='', index=0):
    if len(tag) == 0 or len(tag) <= index:
        return ''
    elif key:
        txt = tag[index].get(key)
        return txt.strip(' \t\r\n') if txt else ''
    else:
        txt = tag[index].text
        return txt.strip(' \r\t\n') if txt else ''

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
    print('库存: {0}'.format(good_data['stockState']))
    print('价格: {0}'.format(good_data['price']))

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
if __name__ == '__main__':
    good_detail('18625729281')
