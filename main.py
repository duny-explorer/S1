import time
from telethon.sync import TelegramClient, functions
import requests
from slovnet import NER
from navec import Navec


navec = Navec.load('navec_news_v1_1B_250K_300d_100q.tar')
ner = NER.load('slovnet_ner_news_v1.tar')
ner.navec(navec)


def get_vk_companies(posts):
    """
    Возвращает кол-венную статистику упоминания компаний и других групп
    :param posts: отобранные посты из группы
    :return:
    """

    companies = dict()
    c = []

    for post in posts:
        if "copyright" in post: # если пост имеет пометку "источник"
            companies[post["copyright"]["name"]] = companies.setdefault(post["copyright"]["name"], 0)
        else:
            markup = ner(post["text"])
            spans = markup.spans
            for i in range(len(spans)):
                if spans[i].type == 'ORG':
                    org_spans = spans[i]
                    start, stop = org_spans.start, org_spans.stop
                    c.append([post["text"], (start, stop)])

    return companies


def vk_parser(url):
    """
    Получает список из указанной группы в вк с информацией о постах, которые предположительно рекламные
    :param url:  адрес на группу в вк
    :return: информацию из группы о постах, которые предположительно имеют рекламу
    """

    token = "token"
    posts = []
    offset = 0
    while True:
        r = requests.get("https://api.vk.com/method/wall.get", params={"domain": url.split("/")[-1],
                                                                       "count": 100,
                                                                       "access_token": token,
                                                                       "offset": str(offset),
                                                                       "v": "5.131"})

        offset += 100

        if len(r.json()['response']['items']) == 0:
            break

        posts.extend(list(filter(lambda x: x['marked_as_ads'] or "https:" in x['text'] or ('copyright' in x and
                                                                                               "vk.com" in x['copyright']["link"]),
                                     r.json()['response']['items']))) # если пост имеет пометку "источник" и этот "источник" из вк или есть пометка "реклама" или в тексте поста есть ссылка

        time.sleep(1)

    return posts


def get_tg_companies(posts):
    """
    Возвращает кол-венную статистику упоминания компаний и других каналов
    :param posts: отобранные посты с канала
    :return:
    """

    companies = dict()

    for post in posts:
        pass

    return companies


def tg_parser(url):
    """
    Получает список из указанного телеграмм канала с информацией о постах, которые предположительно рекламные
    :param url:  адрес на канал в телеграме
    :return: информацию из канала о постах, которые предположительно имеют рекламу
    """
    api_id = "api_id"
    api_hash = "api_hash"
    posts = []
    offset = 0

    with TelegramClient('session_name', api_id, api_hash) as client:
        channel_entity = client.get_entity(url)

        while True:
            r = client(functions.messages.GetHistoryRequest(
                peer=channel_entity,
                limit=100,
                offset_date=None,
                offset_id=0,
                max_id=0,
                min_id=0,
                add_offset=offset,
                hash=0)).messages

            if len(r) == 0:
                break

            posts.extend(list(filter(lambda x: x.message != None and "https:" in x.message, r))) # если в тексте поста есть ссылка
            offset += 100
            time.sleep(1)

    return posts
