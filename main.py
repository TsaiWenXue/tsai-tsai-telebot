import configparser
import telegram
import random

from flask import Flask, request
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# paper scissors rock
hands = ['rock', 'paper', 'scissors']

emoji = {
    'rock': '👊',
    'paper': '✋',
    'scissors': '✌️'  
}

# load config
config = configparser.ConfigParser()
config.read('config.ini')

# init Flask
app = Flask(__name__)

# init telegram bot
bot = telegram.Bot(token=config['Telegram']['access_token'])

@app.route('/hook', methods=['POST'])
def webhook_handler():
    if request.method == 'POST':
        update = telegram.Update.de_json(request.get_json(force=True), bot)

        dispatcher.process_update(update)
    return 'ok'

def start(bot, update):
    player_hands_button, bot_hands_str = init_hands()
    # bot_hands_str = 我的牌\n👊👊👊👊👊
    start_str = '剪刀石頭布!\n'+ bot_hands_str +'\n你的牌'
    update.message.reply_text(start_str, reply_markup = InlineKeyboardMarkup([player_hands_button]))

def play(bot, update):
    try:
        data = update.callback_query.data
        player_hands, bot_hands, mine, yours, score = parse_callback(data)

        result = '我出{}，你出{}，{}!\n再來r\n'.format(emoji[mine], emoji[yours], judge(mine, yours))
        player_button_hands, bot_display_str = hands_to_button(player_hands, bot_hands, score)
        start_str = bot_display_str +'\n你的牌'

        if len(player_hands) > 0:
            update.callback_query.edit_message_text(result + start_str, reply_markup = InlineKeyboardMarkup([player_button_hands]))
        else:
            end_str = '我總共贏了{}場~哈哈哈'.format(score)
            update.callback_query.edit_message_text(result + end_str)
    except Exception as e:
        print(e)

def init_hands():
    bot_hands = random.choices(hands, k=5)
    player_hands = random.choices(hands, k=5)
    return hands_to_button(player_hands, bot_hands, 0)

def parse_callback(data):
    # data = idx|玩家的牌,分數|機器人的牌
    # data = 0|rock,rock,scissors,paper,rock,0|rock,rock,scissors,paper,paper
    parse_data = data.split('|')
    choose_idx = int(parse_data[0])
    player_hands = parse_data[1].split(',')
    bot_hands = parse_data[2].split(',')

    score = int(player_hands.pop(-1))
    yours = player_hands.pop(choose_idx)
    #找可以贏的牌
    for idx, hand in enumerate(bot_hands):
        if judge(hand, yours) == '我贏了':
            mine = bot_hands.pop(idx)
            score += 1
            return player_hands, bot_hands, mine, yours, score
    #找平手的牌
    for idx, hand in enumerate(bot_hands):
        if judge(hand, yours) == '平手':
            mine = bot_hands.pop(idx)
            return player_hands, bot_hands, mine, yours, score
    #隨機出牌
    length = len(bot_hands)
    mine = ''
    if length > 1:
        rand_int = random.randint(0, length-1)
        mine = bot_hands.pop(rand_int) 
    else:
        mine = bot_hands[0]

    return player_hands, bot_hands, mine, yours, score

def judge(mine, yours):
    if mine == yours:
        return '平手'
    elif (hands.index(mine) - hands.index(yours)) % 3 == 1:
        return '我贏了'
    else:
        return '我輸了'

def hands_to_button(player_hands, bot_hands, score):
    bot_str = ','.join(bot_hands)
    player_str = ','.join(player_hands) + ',' + str(score)
    # string解析成button
    player_button_list = []
    for idx, hand in enumerate(player_hands):
        callback_data = str(idx) + '|' + player_str + '|' + bot_str
        player_button_list.append(InlineKeyboardButton(emoji[hand], callback_data=callback_data))
    
    bot_display_str = '我的牌\n'
    for hand in bot_hands:
        bot_display_str += emoji[hand] + ' '

    return player_button_list, bot_display_str

# new dispatcher
dispatcher = Dispatcher(bot, None)
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CallbackQueryHandler(play))

if __name__ == '__main__':
    app.run(debug = True)