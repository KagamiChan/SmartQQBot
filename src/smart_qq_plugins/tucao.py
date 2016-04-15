# -*- coding: utf-8 -*-
import re
import os
import random
import cPickle
import logging

from smart_qq_bot.signals import (
    on_all_message,
    on_group_message,
)

TUCAO_PATH = 'smart_qq_plugins/tucao/'


class TucaoCore(object):

    def __init__(self):
        self.tucao_dict = dict()

    def save(self, group_id):
        """
        :type group_id: int, 用于保存指定群的吐槽存档
        """
        global TUCAO_PATH
        try:
            tucao_file_path = TUCAO_PATH + str(group_id) + ".tucao"
            with open(tucao_file_path, "w+") as tucao_file:
                cPickle.dump(self.tucao_dict[str(group_id)], tucao_file)
            logging.info("RUNTIMELOG tucao saved. Now tucao list:  {0}".format(str(self.tucao_dict)))
        except Exception:
            logging.error("RUNTIMELOG Fail to save tucao.")
            raise IOError("Fail to save tucao.")

    def load(self, group_id):
        """
        :type group_id: int, 用于读取指定群的吐槽存档
        """
        global TUCAO_PATH
        if str(group_id) in self.tucao_dict.keys():
            return

        tucao_file_path = TUCAO_PATH + str(group_id) + ".tucao"
        if not os.path.isdir(TUCAO_PATH):
            os.makedirs(TUCAO_PATH)
        if not os.path.exists(tucao_file_path):
            with open(tucao_file_path, "w") as tmp:
                tmp.close()
        with open(tucao_file_path, "r") as tucao_file:
            try:
                self.tucao_dict[str(group_id)] = cPickle.load(tucao_file)
                logging.info("RUNTIMELOG tucao loaded. Now tucao list:  {0}".format(str(self.tucao_dict)))
            except EOFError:
                self.tucao_dict[str(group_id)] = dict()
                logging.info("RUNTIMELOG tucao file is empty.")



core = TucaoCore()

@on_group_message(name='tucao')
def tucao(msg, bot):
    global core
    reply = bot.reply_msg(msg, return_function=True)
    group_code = str(msg.group_code)

    match = re.match(r'^(?:!|！)(learn|delete)(?:\s?){(.+)}(?:\s?){(.+)}', msg.content)
    if match:
        core.load(group_code)

        logging.info("RUNTIMELOG tucao command detected.")
        command = str(match.group(1)).decode('utf8')
        key = str(match.group(2)).decode('utf8')
        value = str(match.group(3)).decode('utf8')

        if command == 'learn':
            if group_code not in core.tucao_dict:
                core.load(group_code)
            if key in core.tucao_dict[group_code] and value not in core.tucao_dict[group_code][key]:
                core.tucao_dict[group_code][key].append(value)
            else:
                core.tucao_dict[group_code][key] = [value]
            reply("学习成功！快对我说" + str(key) + "试试吧！")
            core.save(group_code)
            return True

        elif command == 'delete':
            if key in core.tucao_dict[group_code] and core.tucao_dict[group_code][key].count(value):
                core.tucao_dict[group_code][key].remove(value)
                reply("呜呜呜我再也不说" + str(value) + "了")
                core.save(group_code)
                return True
    else:
        core.load(group_code)
        for key in core.tucao_dict[group_code].keys():
            if str(key) in msg.content and core.tucao_dict[group_code][key]:
                logging.info("RUNTIMELOG tucao pattern detected, replying...")
                reply(random.choice(core.tucao_dict[group_code][key]))
                return True
    return False

@on_group_message(name='current_tucao')
def current_tucao_list(msg, bot):
    # webqq接受的消息会以空格结尾

    global core
    reply = bot.reply_msg(msg, return_function=True)
    group_code = str(msg.group_code)

    match = re.match(r'^(?:!|！)([^\s\{\}]+)\s*$', msg.content)
    if match:
        core.load(group_code)

        command = str(match.group(1))
        logging.info("RUNTIMELOG command format detected, command: " + command)

        if command == "吐槽列表":
            result = ""
            for key in core.tucao_dict[group_code].keys():
                result += "关键字：{0}\t\t回复：{1}\n".format(key, " / ".join(core.tucao_dict[group_code][key]))
            result = result[:-1]
            logging.info("RUNTIMELOG Replying the list of tucao for group {}".format(group_code))
            reply(result)
    return

@on_group_message(name='delete_tucao')
def delete_tucao(msg, bot):
    global core
    reply = bot.reply_msg(msg, return_function=True)
    group_code = str(msg.group_code)

    match = re.match(r'^(?:!|！)([^\s\{\}]+)(?:\s?)\{([^\s\{\}]+)\}\s*$', msg.content)
    if match:
        core.load(group_code)

        command = str(match.group(1))
        arg1 = str(match.group(2))
        logging.info("RUNTIMELOG command format detected, command:{0}, arg1:{1}".format(command, arg1))
        if command == "删除关键字" and unicode(arg1) in core.tucao_dict[group_code]:
            core.tucao_dict[group_code].pop(unicode(arg1))
            reply("已删除关键字:{0}".format(arg1))
            core.save(group_code)
            return True
    return False
