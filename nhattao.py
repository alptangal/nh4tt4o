import requests
from bs4 import BeautifulSoup as Bs4
import time
import os
import datetime
import random
from urllib.parse import unquote
import aiohttp


async def login(username, password):
    url = 'https://nhattao.com/login/login'
    data = {'login': username, 'password': password, 'cookie_check': '1', '_xfToken': '',
            'redirect': 'https://nhattao.com/', '_xfRequestUri': '/', '_xfNoRedirect': '1', '_xfResponseType': 'json'}
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
        async with session.get(url) as res:
            async with session.post(url, data=data) as res:
                if res.status < 400:
                    js = await res.json()
                    if 'error' not in js:
                        url = 'https://nhattao.com/'
                        async with session.get(url) as res:
                            content = await res.text()
                            if all(item not in content for item in ['Tài khoản của bạn đã bị treo']):
                                headers = {}
                                headers['cookie'] = ''
                                cookies = session.cookie_jar.filter_cookies(
                                    'https://nhattao.com')
                                for key, cookie in cookies.items():
                                    headers['cookie'] += cookie.key + \
                                        '='+cookie.value+';'
                                headers['user-agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0'
                                url = 'https://nhattao.com/'
                                async with session.get(url, headers=headers) as res:
                                    content = await res.text()
                                    soup = Bs4(content, 'html.parser')
                                    token = soup.find('input', {'name': '_xfToken'})[
                                        'value']
                                    print(username+' login success')
                                    return {'headers': headers, 'token': token, 'username': username, 'message': 'Login success'}
                            print(f'{username} Banned')
                            return {'headers': None, 'username': username, 'message': 'Banned'}
                    print(username+' login failed')
                return {'message': f'Error code {res.status}'}


async def getProducts(headers):
    urlM = 'https://nhattao.com/'
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
        async with session.get(urlM, headers=headers['headers']) as res:
            content = await res.text()
            soup = Bs4(content, 'html.parser')
            url = urlM+soup.find(
                'ul', {'class': 'headerBar-userPopup'}).find('a')['href']+'?tab=selling'
            async with session.get(url, headers=headers['headers']) as res:
                content = await res.text()
                soup = Bs4(content, 'html.parser')
                items = []
                if soup.find('div', {'class': 'Nhattao-CardList'}) and soup.find('div', {
                        'class': 'Nhattao-CardList'}).find_all('div', {'class': 'Nhattao-CardItem'}):
                    items = soup.find('div', {
                                      'class': 'Nhattao-CardList'}).find_all('div', {'class': 'Nhattao-CardItem'})
                arr = []
                for item in items:
                    url = urlM+item.find('a', {'class': 'title'})['href']
                    async with session.get(url, headers=headers['headers']) as res:
                        content = await res.text()
                        soup = Bs4(content, 'html.parser')
                        title = soup.find(
                            'h2', {'class': 'threadview-header--title'}).getText()
                        arr.append({'title': title, 'url': url,
                                   'id': url.split('.')[-1].replace('/', ''), 'owner': headers['username']})
                return arr
    return False


async def bumpThread(product, headers):
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
        async with session.get(product['url']+'up?=&_xfRequestUri='+product['url'].replace('https://nhattao.com', '')+'&_xfNoRedirect=1&_xfToken='+headers['token']+'&_xfResponseType=json', headers=headers['headers']) as res:
            js = await res.json()
            if '_redirectMessage' in js:
                print(product['title'] +
                      '\n'+js['_redirectMessage']+'\n'+product['url']+'\n')
                return js['_redirectMessage']
            elif 'templateHtml' in js and 'error' not in js:
                soup = Bs4(js['templateHtml'], 'html.parser')
                action = soup.find('form')['action']
                async with session.get('https://nhattao.com/'+action, headers=headers['headers']) as res:
                    if res.status < 400:
                        print(product['title']+'\n'+' bump success')
                        return product['title']+'\n'+' bump success'
            try:
                print(product['title']+'\n'+js['error']
                      ['0']+'\n'+product['url']+'\n')
                return js['error']['0']
            except:
                return False


async def updateInformation(headers):
    url = 'https://nhattao.com/account/classified'
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
        async with session.get(url, headers=headers['headers']) as res:
            content = await res.text()
            soup = Bs4(content, 'html.parser')
            print(headers['username'])
            phone = soup.find('input', {'name': 'phone_number'})['value']
            token = soup.find('input', {'name': '_xfToken'})['value']
            data = {
                'phone_number': phone,
                'phone_name': '✅ Mr An',
                'phone_secondaries[]': ['0333893909', 'qdvbp', 'alptangal'],
                'name_secondaries[]': ['✅ Mr An (CALL/SMS/ZALO)', '✅ Discord', '✅ Telegram'],
                'address[0]': '1 Quang Trung',
                'city_id[0]': 'HaNoi',
                'district_id[0]': 'QuanHoanKiem',
                'primary': '0',
                'existing[0]': '0',
                'address[1]': '',
                'city_id[1]': '',
                'district_id[1]': '',
                'existing[1]': '0',
                'save': 'Lưu',
                '_xfRequestUri': '/account/classified',
                '_xfNoRedirect': '1',
                '_xfToken': token,
                '_xfResponseType': 'json'
            }
            async with session.post(url, headers=headers['headers'], data=data) as res:
                if res.status < 400:
                    js = await res.json()
                    if '_redirectMessage' in js:
                        print(headers['username']+' updated information')
                        return True
                    print(js['error'][0])
                    return False


async def createProduct(headers, title, description, price, images, category=219):
    url = 'https://nhattao.com/creator/thread/suggestion'
    data = {
        'title': title,
        '_xfRequestUri': '/account/contact-details',
        '_xfNoRedirect': '1',
        '_xfToken': headers['token'],
        '_xfResponseType': 'json'
    }
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
        async with session.post(url, headers=headers['headers'], data=data) as res:
            if res.status < 400:
                js = await res.json()
                if js['node_id'] != 0:
                    category = js['node_id']
                url = 'https://nhattao.com/creator/thread?=&_xfRequestUri=/account/contact-details&_xfNoRedirect=1&_xfToken=' + \
                    headers['token']+'&_xfResponseType=json'
                async with session.get(url, headers=headers['headers']) as res:
                    js = await res.json()
                    soup = Bs4(js['templateHtml'], 'html.parser')
                    attToken = soup.find(
                        'input', {'name': 'attachment_hash'})['value']
                    for img in images:
                        data = {
                            'upload': open(img, 'rb'),
                            '_xfResponseType': 'json',
                            '_xfNoRedirect': '1',
                            '_xfToken': headers['token']
                        }
                        async with session.post('https://nhattao.com/attachments/do-upload.json?hash='+attToken+'&content_type=tinhte_globalcreator', headers=headers['headers'], data=data) as res:
                            js = await res.json()
                            print(img+' '+js['message'])
                    data = {
                        'title': title,
                        'attachment_hash': attToken,
                        'classified_price': price,
                        'classified_message_html_enabled': '1',
                        'message_html': description,
                        'parent_node_id': category,
                        'node_id': category,
                        'classified_status': '1',
                        'classified_storage': '512TB',
                        'classified_color': '#f8f6ef',
                        'classified_guarantee_enabled': '1',
                        'classified_guarantee_month': '12',
                        'classified_guarantee_year': '2299',
                        '_xfToken': headers['token'],
                        '_xfConfirm': '1',
                        'suggested_node_id': '0',
                        '_xfRequestUri': '/account/contact-details',
                        '_xfNoRedirect': '1',
                        '_xfResponseType': 'json'
                    }
                    async with session.post('https://nhattao.com/creator/add-thread', headers=headers['headers'], data=data) as res:
                        if res.status < 400:
                            js = await res.json()
                            if '_redirectMessage' in js:
                                print(js['_redirectMessage'])
                                return {'url': js['_redirectTarget'], 'title': title, 'id': js['_redirectTarget'].split('.')[-1].replace('/', ''), 'owner': headers['username']}
                            print(js['error'][0])
                        return False


async def updateProduct(headers, productUrl, title, description, price, images, category=219):
    url = productUrl+'edit?_xfNoRedirect=1&_xfToken=' + \
        headers['token']+'&_xfResponseType=json'
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
        async with session.get(url, headers=headers['headers']) as res:
            if res.status < 400:
                js = await res.json()
                soup = Bs4(js['templateHtml'], 'html.parser')
                oldImages = soup.find_all(
                    'div', {'class', 'NhattaoMods_UploadZonePreviewItem'})
                uploadUrl = soup.find(
                    'div', {'class': ['NhattaoMods_UploadZone', 'dz-started']})['data-upload-url']
                attToken = soup.find(
                    'input', {'name': 'attachment_hash'})['value']
                for img in oldImages:
                    if 'data-delete-url' in str(img):
                        url = 'https://nhattao.com/'+img['data-delete-url']
                        data = {
                            '_xfNoRedirect': '1',
                            '_xfToken': headers['token'],
                            '_xfResponseType': 'json'
                        }
                        async with session.post(url, headers=headers['headers'], data=data) as res:
                            if res.status < 400:
                                js = await res.json()
                                if '_redirectStatus' in js and js['_redirectStatus'] == 'ok':
                                    print('Old image deleted from '+url)
                for img in images:
                    data = {
                        'upload': open(img, 'rb'),
                        '_xfResponseType': 'json',
                        '_xfNoRedirect': '1',
                        '_xfToken': headers['token']
                    }
                    async with session.post(uploadUrl, headers=headers['headers'], data=data) as res:
                        js = await res.json()
                        print(img+' '+js['message'])
                url = 'https://nhattao.com/creator/thread/suggestion'
                data = {
                    'title': title,
                    '_xfRequestUri': '/account/contact-details',
                    '_xfNoRedirect': '1',
                    '_xfToken': headers['token'],
                    '_xfResponseType': 'json'
                }
                async with session.post(url, headers=headers['headers'], data=data) as res:
                    if res.status < 400:
                        js = await res.json()
                        if js['node_id'] != 0:
                            category = js['node_id']
                data = {
                    'title': title,
                    'attachment_hash': attToken,
                    'classified_price': price,
                    'classified_message_html_enabled': '1',
                    'message_html': description,
                    'parent_node_id': category,
                    'node_id': category,
                    'classified_status': '1',
                    'classified_storage': '512TB',
                    'classified_color': '#f8f6ef',
                    'classified_guarantee_enabled': '1',
                    'classified_guarantee_month': '12',
                    'classified_guarantee_year': '2299',
                    '_xfToken': headers['token'],
                    '_xfConfirm': '1',
                    'suggested_node_id': '0',
                    '_xfNoRedirect': '1',
                    '_xfResponseType': 'json'
                }
                async with session.post(productUrl+'save', headers=headers['headers'], data=data) as res:
                    if res.status < 400:
                        js = await res.json()
                        if '_redirectStatus' in js and js['_redirectStatus'] == 'ok':
                            url = js['_redirectTarget']
                            async with session.get(url, headers=headers['headers'], allow_redirects=False) as res:
                                if res.status == 301:
                                    print(res.headers['location'])
                                    print(js['_redirectMessage'] +
                                          ' in '+res.headers['location'])
                                    return {'url': res.headers['location'], 'title': title, 'id': res.headers['location'].split('.')[-1].replace('/', '')}
                            print(js['_redirectMessage'] +
                                  ' in '+productUrl)
                            return {'url': productUrl, 'title': title, 'id': productUrl.split('.')[-1].replace('/', '')}
                        print(js['error'][0])
                        return False
