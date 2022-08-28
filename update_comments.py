import time
from bs4 import BeautifulSoup
import json
from os import path
from os import listdir
import re
import requests
import csv
from datetime import datetime

rezka_host = "http://kinopub.me/"
news_id = 23576
page = 0
base_link = "http://kinopub.me/films/action/23576-dzhon-uik-2-2017.html"
link = f"{rezka_host}ajax/get_comments/?t={time.time()-100}&news_id={news_id}&cstart={page}&type=0&comment_id=0&skin=hdrezka"


def parse_comments_html(html):
    final_result = []

    soup = BeautifulSoup(html, "html.parser")
    for comment_tree in soup.find_all("li", class_="comments-tree-item"):
        try:
            if comment_tree.attrs["data-indent"] != "0":
                continue
            message_html = str(comment_tree.find("div", class_="message"))
            if message_html.find("<!--dle_spoiler-->") != -1:
                message_html = message_html.replace(">спойлер<", "> <")
                message_html = message_html.replace(
                    "<!--spoiler_text-->", "###OPEN_SPOILER###"
                )
                message_html = message_html.replace(
                    "<!--spoiler_text_end-->", "###CLOSE_SPOILER###"
                )
                message_soup = BeautifulSoup(message_html, "html.parser")
            else:
                message_soup = BeautifulSoup(message_html, "html.parser")
            res = message_soup.find("div", class_="text").find("div").text
            comment_parts = []
            for part in res.split("\n"):
                clear_part = part.strip()
                if clear_part.find("###OPEN_SPOILER###") != -1:
                    clear_part = clear_part.replace(
                        "###OPEN_SPOILER###", "<tg-spoiler>"
                    )
                if clear_part.find("###CLOSE_SPOILER###") != -1:
                    clear_part = clear_part.replace(
                        "###CLOSE_SPOILER###", "</tg-spoiler>"
                    )
                comment_parts.append(clear_part)
            comment_parts = list(filter(lambda x: x != "", comment_parts))
            res = " ".join(comment_parts)
            message_text = res.strip()
            try:
                message_likes = (
                    message_soup.find(class_="b-comment__likes_count")
                    .text.replace(")", "")
                    .replace("(", "")
                )
            except:
                message_likes = 0
            final_result.append((message_text, int(message_likes)))
        except Exception as e:
            print(e)
            continue
    return final_result


def parse_comments_api(response, **kwargs):
    news_id = kwargs["news_id"]

    if not path.exists(f"comments/{news_id}.txt"):
        comments_string = json.dumps([])
        with open(f"comments/{news_id}.txt", "w") as f:
            f.write(comments_string)

    data = json.loads(response.text)
    comments_html_unicode = data["comments"]
    comments_html_text = comments_html_unicode.encode("utf-8").decode("utf-8")
    comments = parse_comments_html(comments_html_text)
    if comments:
        with open(f"comments/{news_id}.txt", "r") as f:
            comments_string = f.read()
        old_comments = json.loads(comments_string)
        print("Количество старых комментариев", len(old_comments))
        print("Количество новых комментариев", len(comments))
        old_comments.extend(comments)
        print("Количество общих комментариев", len(old_comments))
        old_comments.sort(key=lambda x: x[1], reverse=True)

        comments_json_to_write = json.dumps(old_comments)
        with open(f"comments/{news_id}.txt", "w") as f:
            f.write(comments_json_to_write)
    navigation_html = data["navigation"]
    page = kwargs["page"]
    if navigation_html.find("b-navigation__next") == -1:
        next_page = None
        print("Нет больше комментариев")
    else:
        all_javascript_calls = re.findall("[0-9]*, [0-9]*, false, 0", navigation_html)
        next_page = int(all_javascript_calls[-1].split(",")[1][1:])
        print(next_page)
        if next_page <= page:
            print("Нет больше комментариев")
            return

    link = kwargs["link"]
    new_link = link.replace(
        re.findall("cstart=[0-9]+&", link)[0], "cstart=" + str(next_page) + "&"
    )
    headers = kwargs["headers"]
    if next_page:
        # time.sleep(1)
        response = requests.get(new_link, headers=headers)
        parse_comments_api(
            response, news_id=news_id, link=new_link, headers=headers, page=next_page
        )


def parse_comments(news_id, base_link):
    rezka_host = "http://kinopub.me/"
    page = 0
    # base_link = "http://kinopub.me/films/action/23576-dzhon-uik-2-2017.html"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": base_link,
        "sec-ch-ua": '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }

    link = f"{rezka_host}ajax/get_comments/?t={time.time()-100}&news_id={news_id}&cstart={page}&type=0&comment_id=0&skin=hdrezka"

    response = requests.get(link, headers=headers)
    parse_comments_api(response, news_id=news_id, link=link, headers=headers, page=1)


with open("rezka.csv", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    film_id_list = []
    for film in reader:
        film_id_list.append((film["film_id"], film["film_url"]))

all_files = listdir("comments")

files_without_extension = list(map(lambda x: x.split(".")[0], all_files))


couter = 1
film_list_len = len(film_id_list)
time_of_start = time.time()
counter_of_already_parsed = 0
for film_id, film_url in film_id_list:
    if film_id in files_without_extension:
        print(f"Фильм {film_id} уже парсили")
        counter_of_already_parsed += 1
        continue
    all_process_estimated_time = (time.time() - time_of_start) / (
        couter / (film_list_len - counter_of_already_parsed)
    )
    time_remaining = all_process_estimated_time - (time.time() - time_of_start)

    print(
        f"Осталось времени: {time_remaining} секунд или {time_remaining/60} минут или {time_remaining/3600} часов"
    )
    print(
        f"Ожидаемое затраченое время {all_process_estimated_time} или {all_process_estimated_time/60} минут или {all_process_estimated_time/3600} часов"
    )
    print("Parsing film", film_id, film_url)
    print(f"Фильм {couter + counter_of_already_parsed}/{film_list_len}")
    print("Осталось парсить", film_list_len - couter)
    print(
        "Процент выполнения",
        round(couter / (film_list_len - counter_of_already_parsed) * 100, 2),
        "%",
    )
    couter += 1
    parse_comments(film_id, film_url)
    print("----------------------------------------------------")
