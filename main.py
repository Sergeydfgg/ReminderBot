import telebot
from telebot import types
import MyDay
import bot_db
from collections import defaultdict
from datetime import datetime
import threading
from threading import Timer
import StatAnalise
import re

TOKEN = '6283742934:AAF7k_fr7fzXxT-h2DJstqux56ZQ_KJeo8o'


def main() -> None:
    tb = telebot.TeleBot(TOKEN)

    users_dict = defaultdict(MyDay.MyDay)

    def say_hi(message: telebot.types.Message) -> None:
        tb.reply_to(message, "Здарова, братулек")

    def get_info(message: telebot.types.Message):
        bot_db.get_task_info(message.chat.id)

    def get_period(message: telebot.types.Message):
        tb.reply_to(message, "Укажите период в формате: (начало) ГГГГ-ММ-ДД ГГГГ-ММ-ДД (конец)")
        tb.register_next_step_handler(message, get_stat)

    def get_stat(message: telebot.types.Message):
        tb.reply_to(message, "Ожидайте")
        try:
            date_parts = message.text.split()
            StatAnalise.get_stat(message.chat.id, date_parts[0], date_parts[1])
        except (IndexError, ZeroDivisionError):
            tb.reply_to(message, "Ошибка при вводе переиода. Повторите")
            tb.register_next_step_handler(message, get_stat)

    def check_users_notices():
        for chat_id, user in users_dict.items():
            for task in user.tasks_list:
                if task.notice == str(datetime.now()).split('.')[0]:
                    tb.send_message(chat_id, f'Скоро дедлайн задания: {task.name}')
                if task.deadline == str(datetime.now()).split('.')[0]:
                    users_dict[chat_id].delete_task_by_name(task.name, chat_id)
        Timer(1, check_users_notices).start()

    t1 = threading.Thread(target=check_users_notices, daemon=True)
    t1.start()

    def db_add_user(message: telebot.types.Message) -> None:
        tb.reply_to(message, "Как вас зовут?")
        tb.register_next_step_handler(message, bot_db.add_user)

    def show_checked_user(message: telebot.types.Message) -> None:
        user_name = bot_db.check_user(message)[1]
        try:
            msg_text = f"План пользователя {user_name} на сегодня:\n\n"
            for task in users_dict[message.chat.id].show_tasks():
                msg_text += f'{task[0]}) {task[1]} до {task[2].split()[1]}\n'
            tb.send_message(message.chat.id, msg_text)
        except TypeError:
            tb.reply_to(message, f"Дел у {user_name} на сегодня нет")

    def db_check_user(message: telebot.types.Message) -> None:
        tb.reply_to(message, "Имя пользователя?")
        tb.register_next_step_handler(message, show_checked_user)

    def finish_task_choice(message: telebot.types.Message, create_new=True):
        try:
            keyboard = types.InlineKeyboardMarkup()
            cur_user = users_dict[message.chat.id]
            keys_list = [types.InlineKeyboardButton(text=task.name, callback_data=f'{task.name}:finish')
                         for task in cur_user.tasks_list]
            if len(keys_list) == 0:
                tb.reply_to(message, 'Задач пока нет')
                return
            for key in keys_list:
                keyboard.add(key)
            question = 'Выберите задачу, которую хотите завершить'
            if create_new:
                tb.reply_to(message, text=question, reply_markup=keyboard)
            else:
                return keyboard
        except (KeyError, TypeError, IndexError):
            tb.reply_to(message, 'Задач пока нет')

    def change_task_choice(message: telebot.types.Message, create_new=True):
        try:
            keyboard = types.InlineKeyboardMarkup()
            cur_user = users_dict[message.chat.id]
            keys_list = [types.InlineKeyboardButton(text=task.name, callback_data=f'{task.name}:change')
                         for task in cur_user.tasks_list]
            if len(keys_list) == 0:
                tb.reply_to(message, 'Задач пока нет')
                return
            for key in keys_list:
                keyboard.add(key)
            question = 'Выберите задачу, которую хотите изменить'
            if create_new:
                tb.reply_to(message, text=question, reply_markup=keyboard)
            else:
                return keyboard
        except (KeyError, TypeError, IndexError):
            tb.reply_to(message, 'Задач пока нет')

    def remove_task_choice(message: telebot.types.Message, create_new=True):
        try:
            keyboard = types.InlineKeyboardMarkup()
            cur_user = users_dict[message.chat.id]
            keys_list = [types.InlineKeyboardButton(text=task.name, callback_data=f'{task.name}:delete')
                         for task in cur_user.tasks_list]
            if len(keys_list) == 0:
                tb.reply_to(message, 'Задач пока нет')
                return
            for key in keys_list:
                keyboard.add(key)
            question = 'Выберите задачу, которую хотите удалить'
            if create_new:
                tb.reply_to(message, text=question, reply_markup=keyboard)
            else:
                return keyboard
        except (KeyError, TypeError, IndexError):
            tb.reply_to(message, 'Задач пока нет')

    def change_task_element_choice(message: telebot.types.Message, task_name: str):
        keyboard = types.InlineKeyboardMarkup()
        key_name = types.InlineKeyboardButton(text='Имя задачи', callback_data=f'{task_name}:task')
        keyboard.add(key_name)
        key_deadline = types.InlineKeyboardButton(text='Дедлайн', callback_data=f'{task_name}:deadline')
        keyboard.add(key_deadline)
        key_notice = types.InlineKeyboardButton(text='Время отправки уведомления', callback_data=f'{task_name}:notice')
        keyboard.add(key_notice)
        key_back = types.InlineKeyboardButton(text='Назад', callback_data=f'{task_name}:back')
        keyboard.add(key_back)
        return keyboard

    def create_tasks_list(message: telebot.types.Message) -> None:
        if message.text != 'Отмена':
            cur_day = MyDay.MyDay(name='test', chat_id=message.chat.id)
            try:
                result = cur_day.create_list(list(map(lambda task: task.strip(), message.text.split(','))))
                if result == 0:
                    users_dict[message.chat.id] = cur_day
                    tb.reply_to(message, "Список дел добавлен")
                else:
                    tb.reply_to(message, "Один из дедлайнов уже просрочен. Повторите")
                    tb.register_next_step_handler(message, create_tasks_list)
            except (IndexError, TypeError, ValueError):
                tb.reply_to(message, "Ошибка ввода. Повторите")
                tb.register_next_step_handler(message, create_tasks_list)
        else:
            tb.reply_to(message, "Создание отменено")
            return

    def show_tasks_list(message: telebot.types.Message) -> None:
        try:
            user_name = bot_db.get_user(message.chat.id)[1]
        except TypeError:
            user_name = 'незнакомец'
        try:
            msg_text = f"Ваш план на сегодня, {user_name}:\n\n"
            for task in users_dict[message.chat.id].show_tasks():
                msg_text += f'{task[0]}) {task[1]} до {task[2].split()[1]}\n'
            tb.send_message(message.chat.id, msg_text)
        except TypeError:
            tb.reply_to(message, "Пока дел у вас нет")

    def get_task(message: telebot.types.Message) -> None:
        try:
            tb.reply_to(message, "Напишите название вашего дела: Дело_1;дедлайн(ЧЧ:ММ);"
                                 "за сколько часов до дедлайна прислать уведомление")
            tb.register_next_step_handler(message, users_dict[message.chat.id].add_task)
        except TypeError:
            tb.reply_to(message, "Сначала создайте список дел")

    def get_tasks_list(message: telebot.types.Message) -> None:
        tb.reply_to(message, "Перечислите свои дела через запятую: Дело_1;дедлайн(ЧЧ:ММ);"
                             "за сколько часов до дедлайна прислать уведомление, "
                             "... и тд\n"
                             "Пример: Лечь;23:00;1\n"
                             "Чтобы отменить операцию, напишите - Отмена")
        tb.register_next_step_handler(message, create_tasks_list)

    def change_task_name(message: telebot.types.Message, task_name):
        users_dict[message.chat.id].change_task_name(task_name, message.text)
        tb.reply_to(message, 'Имя успешно изменено')

    def change_deadline(message: telebot.types.Message, task_name):
        try:
            if re.fullmatch(r'\d\d:\d\d', message.text):
                users_dict[message.chat.id].change_deadline(task_name, message.text, message.chat.id)
                tb.reply_to(message, 'Дедлайн успешно изменен')
            else:
                raise ValueError
        except (ValueError, IndexError):
            tb.reply_to(message, 'Неверный формат. Повторите')
            tb.register_next_step_handler(message, change_deadline, message.text.split(':')[0])

    def change_notice(message: telebot.types.Message, task_name):
        try:
            users_dict[message.chat.id].change_notice(task_name, message.text)
            tb.reply_to(message, 'Время отправки уведомления успешно изменено')
        except (ValueError, IndexError):
            tb.reply_to(message, 'Неверный формат. Повторите')
            tb.register_next_step_handler(message, change_notice, message.text.split(':')[0])

    @tb.callback_query_handler(func=lambda call: True)
    def keyboard_control(call):
        if call.data.split(':')[1] not in ['task', 'deadline', 'notice', 'back']:
            if call.data.split(':')[1] == 'finish':
                try:
                    users_dict[call.message.chat.id].finish_task(call.data, call.message.chat.id)
                    tb.edit_message_reply_markup(call.message.chat.id, call.message.id,
                                                 reply_markup=finish_task_choice(call.message, create_new=False))
                except TypeError:
                    tb.reply_to(call.message, "Задача не найдена")
            elif call.data.split(':')[1] == 'change':
                try:
                    tb.edit_message_reply_markup(call.message.chat.id, call.message.id,
                                                 reply_markup=change_task_element_choice(call.message,
                                                                                         call.data.split(':')[0]))
                except TypeError:
                    tb.reply_to(call.message, "Задача не найдена")
            elif call.data.split(':')[1] == 'delete':
                try:
                    users_dict[call.message.chat.id].delete_task(call.data.split(':')[0], call.message.chat.id)
                    tb.edit_message_reply_markup(call.message.chat.id, call.message.id,
                                                 reply_markup=remove_task_choice(call.message, create_new=False))
                except ValueError:
                    tb.reply_to(call.message, "Такого у вас в планах не было")
                except TypeError:
                    tb.reply_to(call.message, "Сначала создайте список дел")

        else:
            if call.data.split(':')[1] == 'task':
                tb.reply_to(call.message, 'Введите новое название')
                tb.register_next_step_handler(call.message, change_task_name, call.data.split(':')[0])
            elif call.data.split(':')[1] == 'deadline':
                tb.reply_to(call.message, 'Укажите новый дедлайн')
                tb.register_next_step_handler(call.message, change_deadline, call.data.split(':')[0])
            elif call.data.split(':')[1] == 'notice':
                tb.reply_to(call.message, 'Укажите за сколько часов отправить уведомление?')
                tb.register_next_step_handler(call.message, change_notice, call.data.split(':')[0])
            elif call.data.split(':')[1] == 'back':
                tb.edit_message_reply_markup(call.message.chat.id, call.message.id,
                                             reply_markup=change_task_choice(call.message, False))

    @tb.message_handler(commands=['start'])
    def command_start(message: telebot.types.Message) -> None:
        tb.reply_to(message, 'Вас приветствует бот для напоминаний и помощи в контроле задач. '
                             'Используйте /help для дополнительной информации')

    @tb.message_handler(commands=['help'])
    def command_help(message: telebot.types.Message) -> None:
        tb.reply_to(message, 'Помощи ждать неоткуда')

    control_dict = {"Привет": say_hi,
                    "Создать список дел": get_tasks_list,
                    "/create_tasks": get_tasks_list,
                    "Мои дела": show_tasks_list,
                    "/tasks": show_tasks_list,
                    "Добавить дело": get_task,
                    "/add_task": get_task,
                    "Убрать дело": remove_task_choice,
                    "/delete_task": remove_task_choice,
                    "dbgen": bot_db.db_creation,
                    "CheckUser": db_check_user,
                    "/reg": db_add_user,
                    "/finish_task": finish_task_choice,
                    "Закончить задачу": finish_task_choice,
                    "/change_task": change_task_choice,
                    "Изменить задачу": change_task_choice,
                    "TableTest": get_info,
                    "GetStat": get_period,
                    }

    @tb.message_handler(content_types=['text'])
    def check_message(message: telebot.types.Message) -> None:
        try:
            control_dict[message.text](message)
        except KeyError:
            tb.reply_to(message, 'Че ты пишешь?')

    tb.polling()
    tb.polling(none_stop=True)
    tb.polling(interval=2)

    while True:
        pass


if __name__ == "__main__":
    main()
