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
import datetime
import time
import os
import random
import re
import json
import pickle

sess = requests.Session()
headers = {}
cookies = {}

def get_strtime_now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def tags_val(tag, key='', index=0):
    if len(tag) == 0 or len(tag) <= index:
        return ''
    elif key:
        txt = tag[index].get(key)
        return txt.strip(' \t\r\n') if txt else ''
    else:
        txt = tag[index].text
        return txt.strip(' \r\t\n') if txt else ''
    
def login_by_QR():
    try:
        print('%s 请打开京东手机客户端，准备扫码登录' %(get_strtime_now()))
        url_login = 'https://passport.jd.com/new/login.aspx'

        # step1 open login page
        resp = sess.get(url_login)
        if resp.status_code != requests.codes.OK:
            print("%s 获取登录界面失败" %(get_strtimr_now()))
            return False
        ## save cookies
        for k, v in resp.cookies.items():
            cookies[k] = v
            
        # step2 get qr image
        url_show_qr = 'https://qr.m.jd.com/show'
        resp = sess.get(
            url_show_qr,
            cookies=cookies,
            params={
                'appid':133,
                'size':147,
                't':(time.time()*1000)
                }
            )
        if resp.status_code != requests.codes.OK:
            print('%s 获取二维码失败' %(get_strtime_now()))
            return False
        ## save cookies
        for k, v in resp.cookies.items():
            cookies[k] = v
        ## save qr code
        image_file = 'qr.png'
        with open(image_file, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024):
                f.write(chunk)
        ## open qr code
        os.system('start '+image_file)

        #step3 check scan result
        url_check = 'https://qr.m.jd.com/check'
        retry_times = 100
        qr_ticket = None
        headers['Host'] = 'qr.m.jd.com'
        headers['Referer'] = 'https://passport.jd.com/new/login.aspx'
        while retry_times:
            retry_times -= 1
            resp = sess.get(
                url_check,
                headers = headers,
                cookies = cookies,
                params = {
                    'callback':'jQuery%u' % random.randint(1000000,9999999),
                    'appid': 133,
                    'token':cookies['wlfstk_smdl'],
                    '_':int((time.time()*1000))
                    }
                )
            if resp.status_code != requests.codes.OK:
                continue;
            js_data = json.loads(re.match(r'jQuery\d+\(([\s\S]+)\)', resp.text)[1])
            if js_data['code'] == 200:
                qr_ticket = js_data['ticket']
                break
            else:
                print('%s %s' %(get_strtime_now(), js_data['msg']))
            time.sleep(3)
        if not qr_ticket:
            print('%s 二维码登录失败' %(get_strtime_now()))
            return False

        #step4 validate scan result
        headers['Host'] = 'passport.jd.com'
        headers['Referer'] = 'https://passport.jd.com/uc/login?ltype=logout'
        url_ticket = 'https://passport.jd.com/uc/qrCodeTicketValidation'
        resp = sess.get(
            url_ticket,
            headers = headers,
            cookies = cookies,
            params = {
                't' : qr_ticket
                }
            )
        if resp.status_code != requests.codes.OK:
            print('%s 二维码登录校验失败' %(get_strtime_now()))
            return False
        #print(resp.text)
        #print(resp.headers)
        if not resp.headers.get('P3P'):
            if json.loads(resp.text).has_key('url'):
                print('%s 需要手动安全验证' %(get_strtime_now()))
                return False
            else:
                print('%s %s' %(get_strtime_now(), resp.text))
                return False
        ## login succeed
        headers['P3P'] = resp.headers['P3P']
        for k, v in resp.cookies.items():
            cookies[k] = v
        with open('cookie','wb') as f:
            pickle.dump(cookies, f)
        print('%s 登录成功' %(get_strtime_now()))
        return True
    except Exception as e:
        print('%s 异常 %s' %(get_strtime_now(), e))
        raise
    return False

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
    
    try:
        if count != 1:
            link = link.replace('pcount=1','pcount={0}'.format(count))
        resp = sess.get(link,cookies=cookies)
        soup = BeautifulSoup(resp.text,'html.parser')
        
        tag = soup.select('h3.ftx-02')
        if tag is None:
            tag = soup.select('div.p-name a')
        
        if tag is None or len(tag) == 0:
            print('添加购物车失败')
            return False
    except Exception as e:
        print("Exp {0}".format(e))
    else:
        cart_detail()
        return order_info(options.submit)
    return False
    #resp = sess.get(link, cookies=cookies)
        
    
def cart_detail():
    cart_url = 'https://cart.jd.com/cart.action'
    cart_header = u'购买    数量    价格        总价        商品'
    cart_format = u'{0:8}{1:8}{2:12}{3:12}{4}'
    
    try:
        resp = sess.get(cart_url,cookies=cookies)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text,'html.parser')
        
        print('购物车明细')
        print(cart_header)
        for item in soup.select('div.item-form'):
            check = tags_val(item.select('div.cart-checkbox input'), key='checked')
            check = '+' if check else '-'
            count = tags_val(item.select('div.quantity-form input'), key='value')
            price = tags_val(item.select('div.p-price strong'))
            sums = tags_val(item.select('div.p-sum strong'))
            gname = tags_val(item.select('div.p-name a'))
            print(cart_format.format(check,count,price[1:],sums[1:],gname))
        
        t_count = tags_val(soup.select('div.amout-sum em'))
        t_value = tags_val(soup.select('span.sumPrice em'))
        print(u'总数: {0}'.format(t_count))
        print(u'总额： {0}'.format(t_value[1:]))
    except Exception as e:
        print('Exp {0}'.format(e))
        
def order_info(submit=False):
    print('订单详情')
    try:
        order_url = 'http://trade.jd.com/shopping/order/getOrderInfo.action'
        payload = {
                'rid':str(int(time.time()*1000)),
                }
        
        rs = sess.get(order_url,params=payload,cookies=cookies)
        soup = BeautifulSoup(rs.text,'html.parser')
        
        payment = tag_val(soup.find(id='sumPayPriceId'))
        detail = soup.find(class_='fc-consignee-info')
        
        if detail:
            snd_usr = tag_val(detail.find(id='sendNobile'))
            snd_add = tag_val(detail.find(id='sendAddr'))
            print(u'应付款: {0}'.format(payment))
            print(snd_usr)
            print(snd_add)
            
        if not submit:
            return False
        
        payload = {
                'overseaPurchaseCookies':'',
                'submitOrderParam.btSupport':'1',
                'submitOrderParam.ignorePriceChange':'0',
                'submitOrderParam.sopNotPutInvoice':'false',
                'submitOrderParam.eid': eid,
                'submitOrderParam.fp': fp,
                }
        order_url = 'http://trade.jd.com/shopping/order/submitOrder.action'
        rp = sess.post(order_url,params=payload,cookies=cookies)
        
        if rp.status_code != requests.codes.OK:
            js = json.loads(rp.text)
            if js['success'] == True:
                print('下单成功 请付款')
                return True
            else:
                print('下单失败 {0}:{1}'.format(js['resultCode'], js['message']))
                if js['resultCode'] == '60017':
                    time.sleep(1)
        else:
            print('请求失败 statuscode: {0}'.format(rp.status_code))
    except Exception as e:
        print('Exp {0}'.format(e))
    
    return False
            
if __name__ == '__main__':
    good_detail('18625729281')
    #login('work_2020', 'bTE7LRXmWjMKQ+QrwADnALR05smJFIi39WdiGSfvUZK1krFC8kZULgkC2MJgFso9UOe8aDZIG44OIVKqz06ug71HyFIaRUglPbo+sh6/IgEYez+9JZU+wQqAa0I3jMggjYJwXKa2Jbshlk6Ec3IqOlP0qHDd8RlFJ/MevHxwkCw=')