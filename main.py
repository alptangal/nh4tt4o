import asyncio
import re
import discord
from discord.ext import commands, tasks
from discord.utils import get
import random
from nhattao import *
from guild import *
import server



intents = discord.Intents.default()
client = discord.Client(intents=intents)

HEADERS = []
THREADS = []
USERNAMES = []
CALLING = ['Bán', 'Đẩy', 'Ủn', 'Sút', 'Đá', 'Dọn', 'Thanh lý', 'Dọn dẹp', 'Tìm chủ mới',
           'Kén chồng', 'Kén vợ', 'Tìm chồng', 'Tìm vợ', 'Hạ giá', 'Bù lỗ', 'Thu hồi vốn', 'Tàu']
CALLING1 = ['gấp', 'nhanh', 'gấp gấp', 'nhanh lẹ',
            'lẹ', 'siêu nhanh', 'lẹ lẹ', 'fast']
GUILD_ID=1122707918177960047

@client.event
async def on_ready():
    global HEADERS, THREADS, USERNAMES
    try:
        req=requests.get('http://localhost:8888')
        print(req.status_code)
        await client.close() 
        print('Client closed')
        exit()
    except:
        server.b()  
        guild = client.get_guild(GUILD_ID)
        result = await getBasic(guild)
        THREADS = result['threads']
        if not os.path.isdir('images'):
            os.mkdir('images')
        for msg in result['usernames']:
            username = msg.content
            username = username.strip()
            if '\n' in username:
                users = username.split('\n')
                for user in users:
                    username = user.strip()
                    header = await login(username, result['password'])
                    if 'headers' in header and 'headers' != None:
                        HEADERS.append(header)
                        products = await getProducts(header)
                        random.shuffle(products)
                        for product in products:
                            rs = await bumpThread(product['url'], header)
                    else:
                        await msg.delete()
                        tags = result['logsCh'].available_tags
                        for tag in tags:
                            if tag.name.lower() == 'deleted':
                                await result['logsCh'].create_thread(name=username, content=header["message"])
            else:
                header = await login(username, result['password'])
                if 'headers' in header and header['headers'] != None:
                    HEADERS.append(header)
                    await updateInformation(header)
                    products = await getProducts(header)
                    for product in products:
                        rs = await bumpThread(product, header)
                else:
                    await msg.delete()
                    tags = result['logsCh'].available_tags
                    for tag in tags:
                        if tag.name.lower() == 'deleted':
                            await result['logsCh'].create_thread(name=username, content=header["message"], applied_tags=[tag])
        if not bumpTask.is_running():
            bumpTask.start(guild)
        if not updateThread.is_running():
            updateThread.start(guild)
        if not updateUsername.is_running():
            updateUsername.start(guild)


@tasks.loop(seconds=1)
async def updateThread(guild):
    global HEADERS, THREADS, CALLING, CALLING1
    print('updateThread is running')
    result = await getBasic(guild)
    products = []
    for header in HEADERS:
        products += await getProducts(header)
    for thread in result['threads']:
        if thread.name.split('-')[-1].strip() not in str(products):
            await thread.delete()
            THREADS.remove(thread)
    random.shuffle(result['contents'])
    for content in result['contents']:
        needUpdate = False
        msgs = [msg async for msg in content.history()]
        for i, msg in enumerate(msgs):
            if i == 0 and 'need update' in msg.content.lower() and msg.author.bot:
                needUpdate = True
                await msg.delete()
            elif i == len(msgs)-1 and needUpdate:
                files = []
                description = msg.content
                for i, att in enumerate(msg.attachments):
                    if 'text' in att.content_type:
                        description = await att.read()
                        description = description.decode('utf-8')
                    elif 'image' in att.content_type:
                        await att.save('images/update-product'+str(i)+'.'+att.content_type.split('/')[1])
                        files.append('images/update-product'+str(i)+'.' +
                                     att.content_type.split('/')[1])
                random.shuffle(files)
                title = content.name.strip()[1:-1].strip()
                stop = False
                while not stop:
                    r = random.choice(CALLING)+' ' + \
                        random.choice(CALLING1)+' '+title
                    if len(r) <= 100:
                        title = r
                        stop = True
                price = re.search(r'.*Giá mong muốn:\s(.*?)\s\(.*',
                                  description).group(1)
                titleM = content.name
                for thread in THREADS:
                    msgs1 = [msg async for msg in thread.history(oldest_first=True)]
                    url = [msg async for msg in thread.history(oldest_first=True)][0].content
                    username = [msg async for msg in thread.history(oldest_first=True)][1].content[1:]
                    for header in HEADERS:
                        if username in header['username']:
                            header = header
                            break
                    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
                        async with session.get(url) as res:
                            if res.status < 400:
                                html = await res.text()
                                if titleM[1:-1] in html:
                                    product = await updateProduct(header, url, title.title().strip(), description, price, files)
                                    if product:
                                        title = product['title'][0:94-len(product['id'])]+(
                                            '...' if len(product['title']) > 94 else '')+'- '+product['id']
                                        threadNew = await thread.parent.create_thread(name=title, content=product['url'])
                                        await threadNew.thread.send('✅ '+header['username'])
                                        THREADS.append(threadNew.thread)
                                        THREADS.remove(thread)
                                        await thread.delete()
                                        print(product['url']+' updated')
                for file in files:
                    if os.path.isfile(file):
                        os.remove(file)
        for username in result['usernames']:
            username = username.content
            isset = False
            for product in products:
                if product['owner'] == username and content.name[1:-1].strip().lower() in product['title'].lower():
                    isset = True
            if not isset:
                files = []
                msg = [msg async for msg in content.history(oldest_first=True)][0]
                description = msg.content
                for i, att in enumerate(msg.attachments):
                    if 'text' in att.content_type:
                        description = await att.read()
                        description = description.decode('utf-8')
                    elif 'image' in att.content_type:
                        await att.save('images/new-product'+str(i)+'.'+att.content_type.split('/')[1])
                        files.append('images/new-product'+str(i)+'.' +
                                     att.content_type.split('/')[1])
                random.shuffle(files)
                title = content.name.strip()[1:-1]
                stop = False
                while not stop:
                    r = random.choice(CALLING)+' ' + \
                        random.choice(CALLING1)+' '+title
                    if len(r) <= 100:
                        title = r
                        stop = True
                price = re.search(r'.*Giá mong muốn:\s(.*?)\s\(.*',
                                  description).group(1)
                for header in HEADERS:
                    if username in header['username']:
                        header = header
                        break
                product = await createProduct(header, title.title().strip(), description, price, files)
                if product:
                    products.append(product)
                else:
                    break
                for file in files:
                    if os.path.isfile(file):
                        os.remove(file)
        print(content.name)


@tasks.loop(seconds=1)
async def updateUsername(guild):
    global HEADERS
    print('updateUsername is running')
    result = await getBasic(guild)
    for msg in result['usernames']:
        username = msg.content
        username = username.strip()
        if '\n' in username:
            users = username.split('\n')
            for user in users:
                username = user.strip()
                header = await login(username, result['password'])
                if 'headers' in header and header['headers'] != None:
                    await updateInformation(header)
                    if header and username not in str(HEADERS):
                        HEADERS.append(header)
                else:
                    await msg.delete()
                    tags = result['logsCh'].available_tags
                    for tag in tags:
                        if tag.name.lower() == 'deleted':
                            await result['logsCh'].create_thread(name=username, content=header["message"], applied_tags=[tag])
                    for header in HEADERS:
                        if username in header['username']:
                            HEADERS.remove(header)
        else:
            header = await login(username, result['password'])
            if 'headers' in header and header['headers'] != None:
                if 'headers' in header and 'headers' != None:
                    if header and username not in str(HEADERS):
                        HEADERS.append(header)
            else:
                rs = await msg.delete()
                tags = result['logsCh'].available_tags
                for tag in tags:
                    if tag.name.lower() == 'deleted':
                        await result['logsCh'].create_thread(name=username, content=header["message"], applied_tags=[tag])
                for header in HEADERS:
                    if username in header['username']:
                        HEADERS.remove(header)


@tasks.loop(seconds=60)
async def bumpTask(guild):
    global HEADERS, THREADS
    print('bumpTask is running')
    try:
        result = await getBasic(guild)
        for header in HEADERS:
            products = await getProducts(header)
            random.shuffle(products)
            for product in products:
                try:
                    rs = await bumpThread(product, header)
                except:
                    break
                if rs and product['id'] in str(THREADS):
                    for thread in THREADS:
                        if product['id'] in thread.name:
                            try:
                                msgs = [msg async for msg in thread.history()]
                            except:
                                break
                            for i, msg in enumerate(msgs):

                                if len(msgs)-i > 2 and not msg.author.system and 'channel_name_change' not in msg.type:
                                    await msg.delete()
                            await thread.send(rs)
                elif rs and product['id'] not in str(THREADS):
                    title = product['title'][0:94-len(product['id'])]+(
                        '...' if len(product['title']) > 94 else '')+'- '+product['id']
                    thread = await result['threadsCh'].create_thread(name=title, content=product['url'])
                    await thread.thread.send('✅ '+header['username'])
                    await thread.thread.send(rs)
                    THREADS.append(thread.thread) 
    except Exception as err:
        print(err)
        pass

client.run(os.environ.get('botToken'))
