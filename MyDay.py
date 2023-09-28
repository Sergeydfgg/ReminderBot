import re

import telebot
from telebot import types
from datetime import datetime
import bot_db

TOKEN = ''
tb = telebot.TeleBot(TOKEN)


class MyDay:

    class Task:
        def __init__(self, name: str, deadline: str, notice_time: str) -> None:
            self.name = name
            cur_date = str(datetime.now()).split()[0]
            ded_time = deadline.split(':')
            self.notice = f'{cur_date} {int(ded_time[0]) - int(notice_time)}:{ded_time[1]}:00'
            self.deadline = f'{cur_date} {int(ded_time[0])}:{ded_time[1]}:00'
            self.task_date = str(datetime.now())

    def __init__(self, name: str, chat_id: int) -> None:
        self.user_name = name
        self.user_chat_id = chat_id
        self.tasks_list = []

    def create_list(self, got_list: list) -> int:
        cur_time = str(datetime.now()).split()[1]
        self.tasks_list = [self.Task(task.split(';')[0], task.split(';')[1], task.split(';')[2])
                           for task in got_list if all([int(cur_time.split(':')[0]) <=
                                                        int(task.split(';')[1].split(':')[0]) <= 23,
                                                        re.fullmatch(r'\d\d:\d\d', task.split(';')[1]),
                                                        int(task.split(';')[1].split(':')[1]) <= 59])]
        if len(self.tasks_list) < len(got_list):
            return 1
        return 0

    def add_task(self, msg: telebot.types.Message) -> None:
        if all([re.fullmatch(r'\d\d:\d\d', msg.text.split(';')[1]),
                int(msg.text.split(';')[1].split(':')[0]) <= 23,
                int(msg.text.split(';')[1].split(':')[1]) <= 59]):
            self.tasks_list.append(self.Task(msg.text.split(';')[0], msg.text.split(';')[1], msg.text.split(';')[2]))
            tb.reply_to(msg, "Задача добавлена")
        else:
            raise TypeError

    def delete_task(self, task_name: str, chat_id: int) -> None:
        for task in self.tasks_list:
            if task.name == task_name:
                cur_time = str(datetime.now()).split()[1]
                duration = (int(cur_time.split(':')[0]) - int(task.task_date.split()[1].split(':')[0])) * 60 + \
                           (int(cur_time.split(':')[1]) - int(task.task_date.split()[1].split(':')[1]))
                bot_db.set_task_info(chat_id, task.name, task.task_date, 'Отменено', duration)
                self.tasks_list.remove(task)
                break

    def delete_task_by_name(self, task_name: str, chat_id: int) -> None:
        for task in self.tasks_list:
            if task.name == task_name:
                cur_time = str(datetime.now()).split()[1]
                duration = (int(cur_time.split(':')[0]) - int(task.task_date.split()[1].split(':')[0])) * 60 + \
                           (int(cur_time.split(':')[1]) - int(task.task_date.split()[1].split(':')[1]))
                bot_db.set_task_info(chat_id, task.name, task.task_date, 'Просрочено', duration)
                self.tasks_list.remove(task)
                break
        tb.send_message(chat_id, f"Время на выполнение задачи \'{task_name}\' истекло")

    def finish_task(self, task_name: str, chat_id: int) -> None:
        task_name = task_name.split(':')[0]
        for task in self.tasks_list:
            if task.name == task_name:
                cur_time = str(datetime.now()).split()[1]
                duration = (int(cur_time.split(':')[0]) - int(task.task_date.split()[1].split(':')[0])) * 60 + \
                           (int(cur_time.split(':')[1]) - int(task.task_date.split()[1].split(':')[1]))
                bot_db.set_task_info(chat_id, task.name, task.task_date, 'Сделано', duration)
                self.tasks_list.remove(task)
                break
        tb.send_message(chat_id, f"Задача \'{task_name.split(':')[0]}\' выполнена")

    def change_task_name(self, task_name: str, new_task_name: str) -> None:
        for task in self.tasks_list:
            if task.name == task_name:
                task.name = new_task_name
                return

    def change_deadline(self, task_name: str, deadline: str, chat_id: int) -> None:
        for task in self.tasks_list:
            if task.name == task_name:
                cur_time = str(datetime.now()).split()[1]
                duration = (int(cur_time.split(':')[0]) - int(task.task_date.split()[1].split(':')[0])) * 60 + \
                           (int(cur_time.split(':')[1]) - int(task.task_date.split()[1].split(':')[1]))
                bot_db.set_task_info(chat_id, task.name, task.task_date, 'Дедлайн перенесен', duration)
                cur_date = str(datetime.now()).split()[0]
                ded_time = deadline.split(':')
                task.deadline = f'{cur_date} {int(ded_time[0])}:{ded_time[1]}:00'
                return

    def change_notice(self, task_name: str, notice: str) -> None:
        for task in self.tasks_list:
            if task.name == task_name:
                cur_date = str(datetime.now()).split()[0]
                deadline = task.deadline.split()[1].split(':')
                deadline = f'{deadline[0]}:{deadline[1]}'
                ded_time = deadline.split(':')
                task.notice = f'{cur_date} {int(ded_time[0]) - int(notice)}:{ded_time[1]}:00'
                return

    def show_tasks(self) -> tuple:
        for ind, task in enumerate(self.tasks_list):
            yield ind + 1, task.name, task.deadline
