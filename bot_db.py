import sqlite3
import telebot
from telebot import types

TOKEN = ''
tb = telebot.TeleBot(TOKEN)


def db_creation(message: telebot.types.Message) -> None:
    with sqlite3.connect('DataBase/usersdb.db') as conn:
        cur = conn.cursor()

        cur.execute("""CREATE TABLE users(
                   userid INT,
                   user_name TEXT);
                """)
        conn.commit()


def add_user(message: telebot.types.Message) -> None:
    with sqlite3.connect('DataBase/usersdb.db') as conn:
        cur = conn.cursor()
        user_data = get_user(message.chat.id)
        if user_data is None:
            try:
                cur.execute("INSERT INTO users VALUES(?, ?);", (message.chat.id, message.text))
                conn.commit()
                tb.reply_to(message, "Поздравляем с регистрацией")
            except ValueError:
                tb.reply_to(message, "Что-то пошло не так")
                return
        else:
            try:
                cur.execute("DELETE FROM users WHERE userid=(?);", (message.chat.id,))
                conn.commit()
                cur.execute("INSERT INTO users VALUES(?, ?);", (message.chat.id, message.text))
                tb.reply_to(message, 'Данные обновлены')
            except TypeError:
                tb.reply_to(message, 'Пользователь не найден')


def check_user(message: telebot.types.Message) -> tuple:
    with sqlite3.connect('DataBase/usersdb.db') as conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM users WHERE user_name=(?);", (message.text,))
            one_result = cur.fetchone()
            if message is None:
                return 0, 0
            else:
                return one_result
        except (TypeError, ValueError):
            return 0, 0


def get_user(user_id) -> tuple:
    with sqlite3.connect('DataBase/usersdb.db') as conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM users WHERE userid=(?);", (user_id,))
            return cur.fetchone()
        except ValueError:
            return 0, 0


def set_task_info(user_id, task_name, cur_date, status, duration) -> None:
    with open('DataBase/dates.csv', 'a', encoding='utf-8') as f:
        f.write(f'{user_id},{task_name},{cur_date.split()[0]},{status},{duration}\n')


def get_task_info(user_id) -> None:
    with open('DataBase/dates.csv', 'r') as f:
        for line in f:
            print(line)
