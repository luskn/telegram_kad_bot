# -*- coding: utf-8 -*-
# using telepot bot API for telegram

import telepot
import requests
from telepot.loop import MessageLoop
import urllib3
from pprint import pprint
import logging
import time
import json
import re

import test_config as config
import ref_books

pat_cn = re.compile('\d{1,2}:\d{1,2}:\d{1,}:\d{1,}')

# If you using proxy, then uncommit
proxy_url = "http://192.168.0.20:8080/"
telepot.api._pools = {
    'default': urllib3.ProxyManager(proxy_url=proxy_url, num_pools=3, maxsize=10, retries=False, timeout=30),
}
telepot.api._onetime_pool_spec = (
urllib3.ProxyManager, dict(proxy_url=proxy_url, num_pools=1, maxsize=1, retries=False, timeout=30))

# end of the stuff that's only needed for proxy users

def checkText(text):
    """
    * Check text for right command and by patern.
    """
    logging.debug(text)
    stime = time.time()
    wcommand_count = 0
    text = text.strip()
    if text == '/start':
        new_text = """
Добро пожаловать! Я бот кадастровой палаты,
и я могу дать Вам информацию по объкту на
основе кадастрового номера, для этого
введите комманду ввида:
/get_by_cn 61:11:1234567:123
        """
        wcommand_count = 0
    elif text == '/help':
        new_text = """
        Доступные команды:
        /get_by_cn -- даёт информацию по указанному КН;
        /help -- выводит это меню
        """
        wcommand_count = 0
    elif text.startswith('/get_by_cn'):
        cn = text.split(' ')[-1]
        new_text = get_by_cn(cn)
        # new_text = """КН {}""".format(cn)
        wcommand_count = 0
    elif pat_cn.match(text):
        new_text = get_by_cn(text)
    else:
        new_text = "Введена не верная команда"
    logging.debug('checkText: ', time.time() - stime)
    return new_text


def getfromjson(elem, args=None):
    stime = time.time()
    # print(args, elem)
    try:
        if not args:
            rez = elem
            # print('returned', rez)
            return rez

        if len(args) > 1:
            return getfromjson(elem[args[0]], args[1:])
        else:
            return getfromjson(elem[args[0]])
    except TypeError:
        rez = '-'
        return rez
    finally:
        pass
        #print('getfromjson: ', time.time() - stime)


def getjson(cn, obj_type):
    stime = time.time()
    uri = "http://pkk5.rosreestr.ru/api/features/{}/{}".format(obj_type, cn)
    try:
        uResponse = requests.get(uri)
        print('get uri: ', time.time() - stime)
    except requests.ConnectionError as e:
        print('ERROR: ', str(e))
        getjson(cn, obj_type)
        # return "Connecton error"
    jResponse = json.loads(uResponse.text)
    # pprint(['jResponse: ', jResponse])
    print('getjson: ', time.time() - stime)
    return jResponse


def getKI(data):
    """
    Получаем имя кадаствого иннженера.
    Возможно три случая:
    1) когда КИ представлен физ лицом;
    2) когда КИ предсталвен организацией;
    3) когда КИ отсутствует
    :param data:
    :return:
    """
    stime = time.time()
    KI = ''
    try:
        if data['rc_type'] == 0:
            KI = ' '.join([data['ci_surname'], data['ci_first'], data['ci_patronymic']])
        else:
            KI = data['co_name']
    except (KeyError, TypeError):
        KI = '-'
    except:
        raise
    finally:
        print('getKI: ', time.time() - stime)
        return KI


def formatRezZU(rawtext):
    stime = time.time()
    rezText = """
*Тип объекта:* {objtype};
*Кадастровый номер:* {cad_num};
*Статус:* {status};
*Адрес:* {address};
*Категория земель:* {cat_type};
*Форма собственности:* {right_form};
*Стоимость:* {payment};
*Площадь({area_type}):* {area_value};
*Разрешенное использование:* {util_code};
*по документу:* {util_by_doc};
*Кадастровый инженер:* {ki}
*Дата постановки:* {date_create};
*Дата изменения сведений:* {date_change};
    """.format(objtype=nvl(ref_books.obj_type[rawtext["feature"]["type"]], '-'),  # Тип объекта
               # rawtext["feature"]["attrs"]["adate"],  # Вид объекта
               cad_num=nvl(getfromjson(rawtext, ("feature", "attrs", "cn")), '-'),  # Кадастровый номер
               status=nvl(ref_books.status[rawtext["feature"]["attrs"]["statecd"]], '-'),  # Статус
               address=nvl(getfromjson(rawtext, ("feature", "attrs", "address")), '-'),  # Адрес
               cat_type=nvl(ref_books.category[rawtext["feature"]["attrs"]["category_type"]], '-'),  # Категория земель
               right_form=nvl(ref_books.right_form[rawtext["feature"]["attrs"]["fp"]], '-'),  # Форма собственности
               payment=nvl(getfromjson(rawtext, ("feature", "attrs", "cad_cost")), '-'),  # Стоимость
               payment_unit=nvl(getfromjson(rawtext, ("feature", "attrs", "cad_unit")), '-'),  # Единица стоимости
               area_type=nvl(ref_books.area_type[rawtext["feature"]["attrs"]["area_type"]], '-'),  # Тип площади
               area_value=nvl(getfromjson(rawtext, ("feature", "attrs", "area_value")), '-'),  # Площадь
               util_code=nvl(ref_books.util_code[rawtext["feature"]["attrs"]["util_code"]], '-'),  # РУ
               util_by_doc=nvl(getfromjson(rawtext, ("feature", "attrs", "util_by_doc")), '-'),  # РУ по док-ту
               ki=nvl(getKI(rawtext['feature']['attrs']['cad_eng_data']), '-'),  # КИ
               date_create=nvl(getfromjson(rawtext, ("feature", "attrs", "date_create")), '-'),  # Дата постановки
               date_change=nvl(getfromjson(rawtext, ("feature", "attrs", "cad_record_date")), '-')
               # Дата изменения св-ний
               )
    print('formatRezZU: ', time.time() - stime)
    return rezText


def formatRezOKS(rawtext):
    stime = time.time()
    rezText = """
*Тип объекта:* {objtype};
*Кадастровый номер:* {cad_num};
*Статус:* {status};
*Наименование:* {name};
*Адрес:* {address};
*Форма собственности:* {right_form};
*Стоимость:* {payment};
*Общая площадь:* {area_value};
""".format(
        name=nvl(getfromjson(rawtext, ("feature", "attrs", "name")), '-'),
        objtype=nvl(ref_books.oks_type[getfromjson(rawtext, ("feature", "attrs", "oks_type"))], '-'),  # Тип объекта
        # rawtext["feature"]["attrs"]["adate"],  # Вид объекта
        cad_num=nvl(getfromjson(rawtext, ("feature", "attrs", "cn")), '-'),  # Кадастровый номер
        status=nvl(ref_books.status[rawtext["feature"]["attrs"]["statecd"]], '-'),  # Статус
        address=nvl(getfromjson(rawtext, ("feature", "attrs", "address")), '-'),  # Адрес
        right_form=nvl(ref_books.right_form[rawtext["feature"]["attrs"]["fp"]], '-'),  # Форма собственности
        payment=nvl(getfromjson(rawtext, ("feature", "attrs", "cad_cost")), '-'),  # Стоимость
        payment_unit=nvl(getfromjson(rawtext, ("feature", "attrs", "cad_unit")), '-'),  # Единица стоимости
        area_value=nvl(getfromjson(rawtext, ("feature", "attrs", "area_value")), '-'),  # Площадь

    ) + mainChar(rawtext) + \
              """
*Назначение:* {purpose};
*Кадастровый инженер:* {ki};
*Дата постановки:* {date_create};
*Дата изменения сведений:* {date_change};
                  """.format(
                  ki=nvl(getKI(rawtext["feature"]["attrs"]["cad_eng_data"]), '-'),  # КИ
                  date_create=nvl(getfromjson(rawtext, ("feature", "attrs", "date_create")), '-'),  # Дата постановки
                  date_change=nvl(getfromjson(rawtext, ("feature", "attrs", "cad_record_date")), '-'),
                  # Дата изменения св-ний
                  # относящиеся только к окс
                  purpose=nvl(getfromjson(rawtext, ("feature", "attrs", "purpose")), '-')
              )
    print('formatRezOKS: ', time.time() - stime)
    return rezText


def get_by_cn(cn):
    stime = time.time()
    """
    Подготавливаем КН и после этого выполняем поиск сначало по ЗУ,
    и если результат отричательный, то производим поиск по ОКС
    :param cn:
    :return:
    """
    cn_prepared = prepareCN(cn)
    jsontext = getjson(cn_prepared, 1)
    try:
        if jsontext['feature']:
            rez = formatRezZU(jsontext)
        else:
            jsontext = getjson(cn_prepared, 5)
            if jsontext['feature']:
                rez = formatRezOKS(jsontext)
            else:
                rez = "По кадастровому номеру *" + cn + "* объект не найден."
    except TypeError:
        print('error', jsontext, type(jsontext))
    # pprint(rez)
    print('get_by_cn: ', time.time() - stime)
    return rez


def handle(msg):
    stime = time.time()
    content_type, chat_type, chat_id = telepot.glance(msg)
    if "message_id" in msg:
        text = msg["text"]
        text = checkText(text)
        chat_id = msg["chat"]["id"]
        # print('text: ',text)
        bot.sendMessage(chat_id, text, parse_mode='Markdown')
    # return "OK"
    print('handle: ', time.time() - stime)
    # pprint(msg)


def mainChar(data):
    stime = time.time()
    obj_type = data["feature"]["attrs"]["oks_type"]
    attrs = data["feature"]["attrs"]
    mchar = ''
    if obj_type == 'building':
        mchar = """*Основные характеристики*
  *общая этажность:* {floors};
  *подземная этажность:* {unfloors};
  *завершение строительства:* {year_built};
  *ввод в эксплуатацию:* {year_used};""".format(
            floors=nvl(attrs['floors'], '-'),
            unfloors=nvl(attrs['underground_floors'], '-'),
            # wtype = ref_books.wall_type[attrs['elements_constuct']] #  *материал стен:* {wtype}; убрал на время тестовой версии
            year_built=nvl(attrs['year_built'], '-'),
            year_used=nvl(attrs['year_used'], '-')
        )
    elif obj_type == 'incomplete':
        mchar = ""
    elif obj_type == 'construction':
        mchar = """*Основные характеристики*
  *высота:* {height};
  *глубина:* {depth};
  *протяженность:* {spread};
  *объем:* {volume};
  *площадь застройки:* {area_dev};
  *завершение строительства:* {year_built};
  *ввод в эксплуатацию:* {year_used};""".format(
            height=nvl(attrs['height'], '-'),
            depth=nvl(attrs['depth'], '-'),
            spread=nvl(attrs['spread'], '-'),
            volume=nvl(attrs['volume'], '-'),
            area_dev=nvl(attrs['area_dev'], '-'),
            year_built=nvl(attrs['year_built'], '-'),
            year_used=nvl(attrs['year_used'], '-')
        )
    print('mainChar: ', time.time() - stime)
    return mchar


def nvl(item, replacer):
    if item:
        return item
    else:
        return replacer


def prepareCN(cn):
    """
    * Remove leading 0. If it's kvartal leave one 0.
    """
    stime = time.time()
    cn_splited = cn.split(':')
    cn_splited = [x.lstrip('0') for x in cn_splited]
    if not cn_splited[2]:
        cn_splited[2] = '0'
    cn_prepared = ':'.join(cn_splited)
    print('prepareCN: ', time.time() - stime)
    return cn_prepared

        
if __name__ == '__main__':
    bot = telepot.Bot(config.token)
    # bot.deleteWebhook()
    pprint(bot.getMe())
    # response = bot.getUpdates()
    # pprint(response)

    MessageLoop(bot, handle).run_as_thread()
    print('Listening ...')

    while 1:
        time.sleep(5)
