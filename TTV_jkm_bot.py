#!/usr/bin/python
# -*- coding: utf8 -*-

import socket
import string
import time
import os, re
import random
from collections import deque

from saba import generate_saba
from weather import Weather

debug_mode = False

# whisper server
whisperServerHost = ('199.9.253.119', 6667)
# general chat server
chatServerHost = ('irc.twitch.tv', 6667)
nickname = 'jkmbot'   # TTV user name
password = 'oauth:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'   # login auth key
realname = '' # seems not using
channelName = 'tetristhegrandmaster3'   # channel full name
#socket read
read = ''

# ===== socket login =====

''' example i/o
< PASS oauth:twitch_oauth_token
< NICK twitch_username
> :tmi.twitch.tv 001 twitch_username :connected to TMI
> :tmi.twitch.tv 002 twitch_username :your host is TMI
> :tmi.twitch.tv 003 twitch_username :this server is pretty new
> :tmi.twitch.tv 004 twitch_username tmi.twitch.tv 0.0.1 w n
> :tmi.twitch.tv 375 twitch_username :- tmi.twitch.tv Message of the day - 
> :tmi.twitch.tv 372 twitch_username :- not much to say here
> :tmi.twitch.tv 376 twitch_username :End of /MOTD command

!!IMPORTANT NOTE!!
chinese comes from socket are in big5 codepage, this probably the windows default
page. not sure. Just when writing to db, the convertion should be carefully taken.

'''

def sendIrcMsg(msg):
    """
    send msg to target IRC server and log it
    all time zone are GMT+8
    the sendIrcMsg() DOES NOT ADD new line sybo (\r\n),
    so you should add that in the function argument
    """
    irc_sock.send(msg)
    time_src = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    output_msg = '[' + time_src + ']' + ' << ' + msg
    print(output_msg)

def recvIrcMsg(msg):
    """
    handle recv socket msg
    all time zone are GMT+8
    the recvIrcMsg() DOES ADD new line sybo (\r\n) if there's no sybo at end of line,
    """
    msgLines = msg.splitlines()
    # the splitlines DOES NOT keep newline symbol (\r or \n)
    for line in msgLines:
        time_src = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        output_msg = '[' + time_src + ']' + ' >> ' + line + '\r\n'

        print(output_msg)

def parseRawMsg(rawMsg):
    """
    parse chat message to user, msg
    ':jkm!jkm@jkm.tmi.twitch.tv PRIVMSG #trumpsc :needs Kappa'
    to
    user: jkm
    channel: trumpsc
    msg: needs Kappa
    """

    try:
        userLongStr = rawMsg.split(':')[1]            # 'jkm!jkm@jkm.tmi.twitch.tv'
        user = userLongStr.split('!')[0]              # 'jkm'
        channel = rawMsg.split('#')[1].split(' ')[0]  # not very good though
        msg = rawMsg.split(':', 2)[2]                 # 'needs Kappa'
    except:
        print 'not a channel msg, as below'
        user = ''
        channel = 'x'
        msg = rawMsg
    
    return user, channel, msg

def sendGeneralChatMsg(channelName, msg, interval=2):
    """
    send general chat message with interval
    also check if there's block string in message
    if so, the user ask to send will be append to black list
    """
    time.sleep(interval)
    # filter block strings before actual send it
    if check_block_string(msg):
        sendIrcMsg('PRIVMSG #' + channelName + ' :' + msg + '\r\n')
        return True
    else:
        ban_user_and_record(user, msg)
        msg = user  + ' 已被加入黑名單'
        sendIrcMsg('PRIVMSG #' + channelName + ' :' + msg + '\r\n')
        return False

def check_block_string(string):
    block_string_list = ['od9', '歐滴', 'testban']
    # filter url
    if re.match(r"[\w\d]+\.[\w\d]{2,}", string) is not None:
        return False
    # filter block sting
    for block_string in block_string_list:
        if (block_string in string.lower():
            return False
    return True

def ban_user_and_record(user, msg):
    """
    ban user and save it's previous command and user name to ban_list.txt
    """
    blocked_user_list.append(user)
    print blocked_user_list
    with open('ban_list.txt', 'a') as f:
        f.write('[' + user + ']: ')
        f.write(msg)
        f.write('\n')
        f.flush()
    

# ======================= main script ============================
irc_sock = socket.socket()
irc_sock.connect(chatServerHost)

if not os.path.exists(channelName):
    os.makedirs(channelName)

# password 1st, then nickname
sendIrcMsg('CAP REQ :twitch.tv/commands\r\n')  # this is for twitch whisper
sendIrcMsg('PASS ' + password + '\r\n')
sendIrcMsg('NICK ' + nickname + '\r\n')

login = False
channelJoined = False

# login loop
while not login:
    read = irc_sock.recv(2048)

    # if not join channel, join it 
    if read.find('tmi.twitch.tv 376')!= -1 and not channelJoined:
        sendIrcMsg('JOIN #' + channelName + '\r\n')
        sendIrcMsg('TWITCHCLIENT 3' + '\r\n')
        channelJoined = True
        login = True

    print 'login...'

print 'LOGON'

# ================= prepare necessary globals ===================

broadcaster_trigger = True
banned_msg = 'tmi.twitch.tv CLEARCHAT #' + channelName + ' :'

saba_filter_user_list = ['nightbot']
admin_list = ['jackmoo']
last_command_user = ''
last_command = ''
blocked_user_list = []

# saba 
saba_close_time = 0.0
last_saba_time = 0.0
saba_supervisor_list = deque([], maxlen=10)
saba_supervisor = ''
saba_supervisor_time = 0.0

# ult code
ult_code_upper = 100
ult_code_lower = 1
ult_code = random.randint(ult_code_lower+1, ult_code_upper-1)  # actually only 2~99 is allowed
wrong_number_times = 0  
#ult_code = 87

# weather
last_weather_time = 0.0

# vote
vote_option_list = []
vote_record = []
is_voting = False
vote_timer = 0.0
VOTE_PERIOD = 60

bar_icon_list = ['tgm3RU', 'tgm3Qblock', 'tgm3HIDE', 'tgm3Cgua2',
                 'tgm3AMON', 'tgm3GOMI', 'tgm3Cgua', 'tgm3GA',
                 'tgm3OD', 'tgm3GG']

# bot reset message
_msg = ' MrDestructoid 毛爸公告: 系統已重置 功能更新中    '
sendGeneralChatMsg(channelName, _msg)

while 1:
    # read from IRC socket
    read = irc_sock.recv(2048)
    
    # anti-idle mechanism, if received PING, send PONG
    if read.find('PING :tmi.twitch.tv') != -1:
        print('============= PING RECEIVED ===============')
        sendIrcMsg('PONG :tmi.twitch.tv'+'\r\n')
        print('============= PONG SENT ===============')

    # ==============================================================
    # vote report if time's up
    if (time.time() - vote_timer) > VOTE_PERIOD and is_voting:
        #report result
        vote_num_result = []
        for option_record in vote_record:
            vote_num_result.append(len(option_record))
        
        _msg = '開票: tgm300 '
        for idx, option in enumerate(vote_option_list):
            _msg = _msg + str(idx+1) + '. ' + vote_option_list[idx] + ' ' + str(len(vote_record[idx])) + '票 tgm300 '
        sendGeneralChatMsg(channelName, _msg)
        is_voting = False
        

    # ==============================================================
    # handle incoming msg
    msgLines = read.splitlines()
    # the splitlines DOES NOT keep newline symbol (\r or \n)
    for line in msgLines:
        user, channel, msg = parseRawMsg(line)
        print '[' + user + ']: ' + msg

        # append to block list if last command is banned
        # ex: ':tmi.twitch.tv CLEARCHAT #tetristhegrandmaster3 :jkmbot'
        
        # if banned user is this bot
        if line == banned_msg + nickname:
            with open('ban_list.txt', 'a') as f:
                msg = 'bot is banned, time: ' + time.strftime("%Y%m%d_%H_%M_%S", time.localtime())
                f.write(msg)
                f.write('\n')
                f.flush()
            ban_user_and_record(last_command_user, last_command)
            _msg = last_command_user  + ' 已被加入黑名單 '
            sendGeneralChatMsg(channelName, _msg)
        # if banned user is other ppl
        elif re.search(banned_msg+'(.+)', line) is not None:
            # catch with try, since group(1) may not exist
            try:
                qq_user = re.search(banned_msg+'(.+)', line).group(1)
                _msg = 'tgm3GG ' + qq_user + ' 已被送進魚缸深處 tgm3GG '
                sendGeneralChatMsg(channelName, _msg)
            except:
                if debug_mode:
                    print line
                pass


        # for other system msg, pass it, for debug, show's it
        if 'twitch.tv' in user:
            if debug_mode:
                print line
            continue

        # append speaking user into saba_supervisor_list
        if (user and
           user not in saba_supervisor_list and
           user not in saba_filter_user_list):
            saba_supervisor_list.append(user)

        # check if command
        if msg.startswith('!'):
            # record user that sent command
            last_command_user = user
            last_command = msg

            # === boardcaster/admin user controls ===
            if user == channelName or user in admin_list:
                if msg == '!關閉毛bot' or msg == '!關閉毛爸' or msg == '!毛爸 off':
                    broadcaster_trigger = False
                    _msg = '==== 毛bot已關 ===='
                    sendGeneralChatMsg(channelName, _msg)
                elif msg == '!開啟毛bot' or msg == '!開啟毛爸' or msg == '!毛爸 on':
                    broadcaster_trigger = True
                    _msg = '==== 毛bot已開 ===='
                    sendGeneralChatMsg(channelName, _msg)
                elif msg == '!毛爸 密碼':
                    broadcaster_trigger = True
                    _msg = str(ult_code)
                    sendGeneralChatMsg(channelName, _msg)
                elif msg.startswith('!毛爸 黑名單'):
                    msg = msg.replace('!毛爸 黑名單', '')
                    msg = msg.strip()
                    if msg == '':
                        _msg = ' '.join(blocked_user_list)
                        sendGeneralChatMsg(channelName, _msg)
                    # manually add user into black list
                    else:
                        b_user = msg
                        blocked_user_list.append(b_user)
                        _msg = msg + ' 已被加入黑名單後選 tgm3GG '
                        sendGeneralChatMsg(channelName, _msg)
                # load data in 'tower.txt' and send in chat
                elif msg == '!蓋':
                    with open('tower.txt', 'r') as f:
                        all_file = f.read()
                    file_line_list = all_file.splitlines()
                    for _line in file_line_list:
                        sendGeneralChatMsg(channelName, _line, 1.5)
 
            # bot activate/deactivate switch
            if broadcaster_trigger:
                pass
            else:
                continue

            # ======= filter nightbot's command =======
            # ignore nightbot's command to avoid chain reaction
            if user == 'nightbot':
                continue

            # ======= BLACK LIST  =======
            # the command sent by user in black list will be ignored
            if user in blocked_user_list:
                continue
 
            # ================== 魚攤相關 =====================
            if msg == '!魚攤':
                # 魚攤 cooldown 600s
                if (time.time() - last_saba_time) < 600:
                    _msg = '魚攤CD中ㄛ'
                    sendGeneralChatMsg(channelName, _msg)
                elif (time.time() - saba_close_time ) > 3600:
                    saba_list = generate_saba(max_width=4, max_height=5, probability=random.random())
                    for idx, _line in enumerate(saba_list):
                        _msg = str(idx+1) + ' ' + ' '.join(_line)
                        sendGeneralChatMsg(channelName, _msg)
                    last_saba_time = time.time()
                else:
                    _msg = '魚攤收攤中 距離可擺攤還有' + str(3600 - int(time.time()-saba_close_time)) + '秒'
                    sendGeneralChatMsg(channelName, _msg)
            elif msg == '!收攤':
                saba_close_time = time.time()
                _msg = '魚攤收一小'
                sendGeneralChatMsg(channelName, _msg)
            elif msg == '!魚攤老闆':
                if (time.time() - saba_supervisor_time) > 10:
                    saba_supervisor = random.choice(saba_supervisor_list)
                    saba_supervisor_time = time.time()
                    _msg = '魚攤老闆目前是:  ' + saba_supervisor + ' 請在10秒內輸入"!開攤"來開攤'
                    sendGeneralChatMsg(channelName, _msg)
                else:
                    _msg = '魚攤老闆目前是:  ' + saba_supervisor
                    sendGeneralChatMsg(channelName, _msg)
            elif msg == '!開攤':
                print saba_supervisor
                if user != saba_supervisor:
                    _msg = '你不是老闆喔ㄏㄏ'
                    sendGeneralChatMsg(channelName, _msg)
                elif (time.time() - saba_supervisor_time) > 10:
                    _msg = '過期ㄌ 請再輸入"!魚攤老闆"決定新老闆'
                    sendGeneralChatMsg(channelName, _msg)
                else:
                    saba_close_time = 0.0
                    _msg = '魚攤開張瞜'
                    sendGeneralChatMsg(channelName, _msg)

            # ================== 終極密碼 ====================
            elif msg == '!終極密碼' or msg == '!猜密碼':
                _msg = 'tgm3Qblock ' + str(ult_code_lower) + ' 到 ' + str(ult_code_upper) + ' tgm3Qblock 請用指令"!猜密碼 <數字>"'
                sendGeneralChatMsg(channelName, _msg)
            elif msg.startswith('!猜密碼'):
                number = msg.replace('!猜密碼 ', '')
                # regex passed and in range
                if (re.match(r"^[\d]{1,3}$", number) is not None and
                   int(number) < ult_code_upper and
                   int(number) > ult_code_lower):
                    # do number check
                    # hit
                    if int(number) == ult_code:
                        time.sleep(1.5)
                        if ult_code == 87:
                            _msg = '恭喜 GivePLZ ' + user + ' TakeNRG 猜中87 ㄛㄏ'
                        else:
                            _msg = user + ' 猜中ㄌ 答案是 GivePLZ ' + str(ult_code) + ' TakeNRG ' + \
                                   '(' + str(wrong_number_times+1) + ')'
                        sendGeneralChatMsg(channelName, _msg)
                        ult_code_upper = 100
                        ult_code_lower = 1
                        wrong_number_times = 0
                        ult_code = random.randint(ult_code_lower+1, ult_code_upper-1)
                    # miss
                    else:
                        time.sleep(1.5)
                        if int(number) > ult_code:
                            ult_code_upper = int(number)
                        elif int(number) < ult_code:
                            ult_code_lower = int(number)
                        wrong_number_times = wrong_number_times + 1
                        _msg = '廢 沒猜到 tgm3OD '+ str(ult_code_lower) + ' 到 ' + \
                        str(ult_code_upper) + ' tgm3OD ' + '(' + str(wrong_number_times) + ')'
                        sendGeneralChatMsg(channelName, _msg)
                # regex not pass or not in range
                else:
                    _msg = '正常猜好ㄇ Kappa'
                    sendGeneralChatMsg(channelName, _msg)

            # ============ 圖像拉霸 ==============
            elif msg == '!拉霸':
                icon_list = []
                for i in xrange(3):
                    icon_list.append(random.choice(bar_icon_list))
                _msg = ' '.join(icon_list)
                sendGeneralChatMsg(channelName, _msg)

            # ============ TRPG 骰 ================
            elif msg.startswith('!骰骰'):
                dice = msg.replace('!骰骰 ', '')
                if re.match(r"^[\d]+d[\d]+$", dice) is not None:
                    dice_num = int(dice.split('d')[0])
                    dice_size = int(dice.split('d')[1])
                    if dice_num > 1000 or dice_size > 1000:
                        _msg = '超過上限1000ㄌ'
                        sendGeneralChatMsg(channelName, _msg)
                        continue
                    ret = sum(random.randint(1, dice_size) for i in range(dice_num))
                    _msg = str(ret)
                    sendGeneralChatMsg(channelName, _msg)
                else:
                    _msg = '正常骰好ㄇ 格式: 5d3'
                    sendGeneralChatMsg(channelName, _msg)

            # ============ 天氣 ================
            elif msg == '!天氣' and user in admin_list:
                if (time.time() - last_weather_time) < 30:
                    _msg = '天氣CD中'
                    sendGeneralChatMsg(channelName, _msg) 
                    continue
                towns_name, weather_dict = Weather().get_weather('台北', '中山區')
                specials = u''
                print weather_dict['specials']
                if weather_dict['specials']:
                    specials = weather_dict['specials'][0]['desc']

                _msg = u'%s 想查地區天氣請用 格式: !天氣 高雄 大寮區' % specials
                sendGeneralChatMsg(channelName, _msg.encode('utf-8'))

            elif msg.startswith('!天氣') and user in admin_list:
                # weather cooldown 30s
                if (time.time() - last_weather_time) < 30:
                    _msg = '天氣CD中'
                    sendGeneralChatMsg(channelName, _msg)
                    continue
                location = msg.replace('!天氣', '')
                location = location.strip()
                if re.match(r"^.*\s.*$", location) is not None:
                    city = location.split(' ', 1)[0]
                    towns = location.split(' ', 1)[1]
                    towns_name, weather_dict = Weather().get_weather(city, towns)
                    last_weather_time = time.time()
                    if weather_dict:
                        #print weather_dict['specials']
                        _msg = u'%s %s, 溫度: %s, 體感溫度: %s, 濕度: %s, 雨量: %s, 日出時間: %s, 日落時間: %s' % \
                               (towns_name,
                                weather_dict['desc'],
                                weather_dict['temperature'],
                                weather_dict['felt_air_temp'],
                                weather_dict['humidity'],
                                weather_dict['rainfall'],
                                weather_dict['sunrise'],
                                weather_dict['sunset'],
                                )
                        sendGeneralChatMsg(channelName, city + _msg.encode('utf-8'))
                    else:
                        _msg = '資料錯誤或格式錯誤 格式: !天氣 高雄 大寮區'
                        sendGeneralChatMsg(channelName, _msg)  
                else:
                    _msg = '格式錯誤 格式: !天氣 高雄 大寮區'
                    sendGeneralChatMsg(channelName, _msg)

            # ============ 投票 this would repeat user msg, should handle carefully ==============
            elif msg.startswith('!辦投票') and user in admin_list:
                if (time.time() - vote_timer) < VOTE_PERIOD:
                    _msg = '投票進行中'
                    sendGeneralChatMsg(channelName, _msg)
                    continue
                vote_option = msg.replace('!辦投票', '')
                vote_option = vote_option.strip()
                vote_option_list = vote_option.split(' ')
                vote_record = []
                _msg = '投票期間為' + str(VOTE_PERIOD) + '秒 投票格式: "!投票 2" 選項為 tgm300 '
                for idx, option in enumerate(vote_option_list):
                    _msg = _msg + str(idx+1) + '. ' + option + ' tgm300 '
                    vote_record.append([])
                ret = sendGeneralChatMsg(channelName, _msg)
                if not ret:
                    continue
                vote_timer = time.time()
                is_voting = True
            elif msg.startswith('!投票'):
                # check if voting
                if (time.time() - vote_timer) > VOTE_PERIOD:
                    _msg = '目前無投票'
                    sendGeneralChatMsg(channelName, _msg)
                    continue
                vote = msg.replace('!投票', '')
                vote = vote.strip()
                if re.match(r"^\d+$", vote) is not None and vote != '0':
                    idx = int(vote) - 1
                    # vote out of range
                    if int(vote) > len(vote_record):
                        _msg = '沒有此選項'
                        sendGeneralChatMsg(channelName, _msg)
                        continue
                    # check user already voted
                    voted = False
                    for vote_option_voter in vote_record:
                        if user in vote_option_voter:
                            voted = True
                            break
                    # if user voted, ignore him
                    if voted:
                        continue
                    # if not voted, append user to record
                    else:
                        vote_record[idx].append(user)

                else:
                    _msg = '投票格式錯誤 格式: "!投票 2"'
                    ret = sendGeneralChatMsg(channelName, _msg)
                    if not ret:
                        continue

            # ============ 粉 ================
            elif msg == '!給我粉':
                _msg = 'PJSalt PJSalt PJSalt'
                ret = sendGeneralChatMsg(channelName, _msg)

        # message are not starting with '!', leave for future feature
        else:
            pass

