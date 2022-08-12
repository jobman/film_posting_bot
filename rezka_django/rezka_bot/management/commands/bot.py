import os
import csv
from os.path import exists
import re
import random
from datetime import timedelta
import json
from turtle import pos
from telegram import InputMediaPhoto, InputMediaVideo
from django.core.management.base import BaseCommand
from rezka_bot.models import UserAdmin, Post
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from django.conf import settings
from django.utils import timezone
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackQueryHandler,
)
from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
)
from telegram.ext import CallbackContext

SAVE_NEW_COMMENT, SAVE_VIDEO = range(2)


def update_or_create_user(f):
    def wrapper(update: Update, context: CallbackContext, **kwargs):
        p, created = UserAdmin.objects.get_or_create(
            external_id=update.message.chat_id,
            defaults={
                "username": update.message.from_user.username,
            },
        )
        return f(update, context, profile=p, created=created)

    return wrapper


@update_or_create_user
def do_start(update, context, profile, created):
    if profile.is_admin:
        update.message.reply_text(
            "Привет, я бот для управления каналом с хорошими фильмами!\n"
            + settings.CHANEL_NAME
        )
        choose_good_film_from_csv_file(admin=profile, update=update)


def construct_keyboard_for_comment(post, comment_id):
    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️", callback_data=f"commentBack_{post.film_id}_{comment_id}"
            ),
            InlineKeyboardButton(
                "➡️",
                callback_data=f"commentForward_{post.film_id}_{comment_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                "✅ Опубликовать",
                callback_data=f"commentPublish_{post.film_id}_{comment_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                "🤷‍♂️ Без комментария",
                callback_data=f"commentNo_{post.film_id}_{comment_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                "❌ Отмена",
                callback_data=f"filmCancel_{post.film_id}_{comment_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                "✏️ Редактировать",
                callback_data=f"commentEdit_{post.film_id}_{comment_id}",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def get_comments_by_post(post):
    if exists(f"data/comments/{post.film_id}.txt"):
        comments_file = "data/comments/" + f"{post.film_id}.txt"
    else:
        comments_file = None
        print(f"No comments for {post.film_name}")
    if comments_file:
        with open(comments_file, "r") as f:
            comments_string = f.read()
        comments = json.loads(comments_string)
        comments.sort(key=lambda x: x[1], reverse=True)
        print(comments)
        return comments
    else:
        return []


def edit_effective_message_of_comment_choosing(post, comment_id, update):
    message = get_message_text_of_comment_for_admin_to_choose(post, comment_id)
    update.effective_message.edit_text(
        message,
        reply_markup=construct_keyboard_for_comment(post, comment_id),
        parse_mode="HTML",
    )


def get_post_text_for_chanel_post(post, comment=False):
    year = re.findall(r"\d{4}", post.film_date)[0]
    url = f"https://www.google.com/search?q={post.film_name} {year} смотреть онлайн"
    post.film_url = url
    post.save()
    result = ""
    result += f"<b>{post.film_name}</b>\n"
    # result += f'<a href="{url}">ссылка на фильм</a>\n'
    result += f"Рейтинг от Джанго: <b>{round(10/(9.8-post.film_rating))}</b> 💥\n\n"
    result += f"{post.film_date}\n"
    result += f"{post.generes}\n\n"
    cast_4 = " ".join(post.cast.split(" ")[:4])
    result += f"В ролях: {cast_4}\n"
    result += f"Режиссер: {post.producer}\n"
    if comment:
        result += "___________________\n"
        result += post.comment_review
        result += f'\n\n<a href="{url}">ссылка на фильм</a>\n'
        result += f'<a href="https://t.me/django_watch">КАНАЛ ХОРОШЕГО КИНО</a>'
    else:
        result += f'\n<a href="{url}">ссылка на фильм</a>\n'
        result += f'<a href="https://t.me/django_watch">КАНАЛ ХОРОШЕГО КИНО</a>'
    return result


def publish_post_with_choosen_comment(post, comment_id, update, context):
    post_text = get_post_text_for_chanel_post(post)
    comment_tuple = get_comments_by_post(post)[comment_id]
    comment_text = comment_tuple[0]
    if len(post_text + "\n" + comment_text) <= 1024:
        post_text += f"\n{comment_text}"
        context.bot.send_message(
            chat_id=settings.CHANEL_NAME,
            text=post_text,
            parse_mode="HTML",
        )
        update.effective_message.edit_text(
            f"Фильм <b>{post.film_name}</b> опубликован в канале!",
        )
    update.effective_message.delete()


def schedule_post_with_choosen_comment(post, comment_id, update, context):
    post_text = get_post_text_for_chanel_post(post)
    if comment_id is not None:
        comment_tuple = get_comments_by_post(post)[int(comment_id)]
        comment_text = comment_tuple[0]
        post.comment_review = comment_text

    all_approved_posts = Post.objects.filter(status=Post.Status.APPROVED).order_by(
        "-scheduled_for"
    )
    last_post = all_approved_posts[0] if all_approved_posts else None
    if last_post:
        post.random_shift_for_posting = random.randint(-5, 5)
        signum_this_post = 1 if post.random_shift_for_posting > 0 else -1
        signum_last_post = 1 if last_post.random_shift_for_posting > 0 else -1
        if last_post.scheduled_for_type == Post.Scheduled_for_type.MORNING:
            post.scheduled_for_type = Post.Scheduled_for_type.AFTERNOON
            post.scheduled_for = (
                last_post.scheduled_for
                + timedelta(hours=4)
                + signum_this_post * timedelta(minutes=post.random_shift_for_posting)
                - signum_last_post
                * timedelta(minutes=abs(last_post.random_shift_for_posting))
            )
        elif last_post.scheduled_for_type == Post.Scheduled_for_type.AFTERNOON:
            post.scheduled_for_type = Post.Scheduled_for_type.EVENING
            post.scheduled_for = (
                last_post.scheduled_for
                + timedelta(hours=8)
                + signum_this_post * timedelta(minutes=post.random_shift_for_posting)
                - signum_last_post
                * timedelta(minutes=abs(last_post.random_shift_for_posting))
            )
        elif last_post.scheduled_for_type == Post.Scheduled_for_type.EVENING:
            post.scheduled_for_type = Post.Scheduled_for_type.MORNING
            post.scheduled_for = (
                last_post.scheduled_for
                + timedelta(hours=12)
                + signum_this_post * timedelta(minutes=post.random_shift_for_posting)
                - signum_last_post
                * timedelta(minutes=abs(last_post.random_shift_for_posting))
            )
    else:
        # tzinfo=pytz.timezone("Europe/Kiev")
        post.random_shift_for_posting = 0
        if timezone.now().hour < 8:
            post.scheduled_for_type = Post.Scheduled_for_type.MORNING
            post.scheduled_for = timezone.now().replace(
                hour=8,
                minute=30,
            )
        elif timezone.now().hour < 12:
            post.scheduled_for_type = Post.Scheduled_for_type.AFTERNOON
            post.scheduled_for = timezone.now().replace(
                hour=12,
                minute=30,
            )
        elif timezone.now().hour < 16:
            post.scheduled_for_type = Post.Scheduled_for_type.EVENING
            post.scheduled_for = timezone.now().replace(
                hour=20,
                minute=30,
            )
        else:
            post.scheduled_for_type = Post.Scheduled_for_type.MORNING
            post.scheduled_for = timezone.now().replace(
                hour=8,
                minute=30,
            ) + timedelta(days=1)
    post.status = Post.Status.APPROVED
    post.save()
    update.effective_message.edit_text(
        f"Фильм <b>{post.film_name}</b> запланирован на <i>{post.scheduled_for.strftime('%d.%m.%Y %H:%M')}</i>",
        parse_mode="HTML",
    )


def keyboard_handler(update, context):
    query = update.callback_query
    data = query.data
    chat_id = update.effective_message.chat_id
    profile = UserAdmin.objects.get(external_id=chat_id)

    button_type, film_id, comment_id = data.split("_")
    post = Post.objects.get(film_id=film_id)
    comments = get_comments_by_post(post)

    if profile.is_admin:
        if button_type == "commentBack":
            comment_id = int(comment_id) - 1
            if comment_id < 0:
                comment_id = len(comments) - 1
            edit_effective_message_of_comment_choosing(post, comment_id, update)
        elif button_type == "commentForward":
            comment_id = int(comment_id) + 1
            if comment_id >= len(comments):
                comment_id = 0
            edit_effective_message_of_comment_choosing(post, comment_id, update)
        elif button_type == "commentPublish":
            pass
        elif button_type == "commentNo":
            schedule_post_with_choosen_comment(post, None, update, context)
        elif button_type == "filmCancel":
            post.status = Post.Status.DECLINE
            post.save()
            update.effective_message.edit_text(
                f"Фильм <b>{post.film_name}</b> отклонен", parse_mode="HTML"
            )
            choose_good_film_from_csv_file(admin=profile, update=update)
        elif button_type == "commentEdit":
            pass


def get_message_text_of_comment_for_admin_to_choose(post, comment_id):
    comments = get_comments_by_post(post)
    comment = comments[comment_id]
    if len(comment[0]) < 4096:
        message = f"Комментарий к фильму <b>{post.film_name}</b>\n"
        message += f"{post.film_date}\n"
        message += f"Режиссер {post.producer}\n"
        message += f"id фильма {post.film_id}\n"
        message += (
            f"Коментарий <b>{comment_id + 1} из {len(comments)}</b>\n\n"
            + comment[0]
            + "\n\n Рейтинг: "
            + "<b>"
            + str(comment[1])
            + "</b>"
        )
        return message
    else:
        return f"Комментарий слишком длинный, его рейтинг <b>{comment[1]}</b>"


def choose_comment(post, admin, update):
    file_list = os.listdir("data/comments")
    for file in file_list:
        if file.startswith(str(post.film_id)):
            comments_file = "data/comments/" + file
            break
    else:
        comments_file = None
        print(f"No comments for {post.film_name}")
    if comments_file:
        with open(comments_file, "r") as f:
            comments_string = f.read()
        comments = json.loads(comments_string)
        comments.sort(key=lambda x: x[1], reverse=True)
        print(comments)
        update.message.reply_text(
            get_message_text_of_comment_for_admin_to_choose(post, 0),
            reply_markup=construct_keyboard_for_comment(post, 0),
            parse_mode="HTML",
        )


def create_post(post_dict, admin, update):
    post = Post()
    post.profile = admin
    post.film_id = post_dict["film_id"]
    post.film_name = post_dict["film_name"]
    post.film_rating = post_dict["film_rating"]
    post.film_rating_count = post_dict["film_rating_count"]
    post.generes = post_dict["genre"]
    post.film_imdb_rating = post_dict["imdb"]
    post.producer = post_dict["producer"]
    post.cast = post_dict["cast"]
    post.film_date = post_dict["date"]
    file_list = os.listdir("data/posters")
    for file in file_list:
        if file.startswith(post_dict["film_id"]+"."):
            post.image_file_name = "data/posters/" + file
            break

    post.save()
    print(f"Post created: {post.film_name}")
    choose_comment(post, admin, update)


def choose_good_film_from_csv_file(file_name="data/films.csv", admin=None, update=None):
    with open(file_name, encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        film_list = []
        for film in reader:
            film["film_rating"] = float(film["film_rating"])
            film["film_rating_count"] = int(film["film_rating_count"])
            if film["imdb"]:
                film["imdb"] = float(film["imdb"])
            film_list.append(film)
    best_films = []
    for film in film_list:
        if film["film_rating"] > 9.5 and film["film_rating_count"] > 100:
            best_films.append(film)
        elif film["film_rating"] > 9.4 and film["film_rating_count"] > 200:
            best_films.append(film)
        elif film["film_rating"] > 9.3 and film["film_rating_count"] > 300:
            best_films.append(film)
        elif film["film_rating"] > 9.2 and film["film_rating_count"] > 400:
            best_films.append(film)
        elif film["film_rating"] > 9.1 and film["film_rating_count"] > 500:
            best_films.append(film)
    chosen_film = random.choice(best_films)
    while True:
        not_posted_yet = chosen_film["film_id"] not in Post.objects.values_list(
            "film_id", flat=True
        )

        file_list = os.listdir("data/posters")
        for file in file_list:
            if file.startswith(chosen_film["film_id"]):
                poster_exists = True
                break
        else:
            poster_exists = False

        if not_posted_yet and poster_exists:
            break
        chosen_film = random.choice(best_films)
    create_post(chosen_film, admin, update)


last_alarm_time = None


def post_scheduled_film(context):
    all_approved_posts = Post.objects.filter(status=Post.Status.APPROVED).order_by(
        "scheduled_for"
    )
    global last_alarm_time
    if len(all_approved_posts) < 4 and (
        last_alarm_time is None
        or timezone.now() > last_alarm_time + timedelta(minutes=60)
    ):
        last_alarm_time = timezone.now()
        admin = UserAdmin.objects.first()
        context.bot.send_message(
            admin.external_id,
            "Фильмов осталось на одни сутки - добавь еще используя команду /start",
            parse_mode="HTML",
        )
    last_post = all_approved_posts[0] if all_approved_posts else None
    if last_post:
        if last_post.scheduled_for < timezone.now():
            text = get_post_text_for_chanel_post(last_post, comment=True)
            img = open(last_post.image_file_name, "rb")
            if len(text) <= 1024:
                if not last_post.video:
                    message = context.bot.send_photo(
                        settings.CHANEL_NAME,
                        photo=img,
                        caption=text,
                        parse_mode="HTML",
                    )
                    last_post.post_id = message.message_id
                    last_post.save()
                else:
                    media_to_send = []
                    media_to_send.append(
                        InputMediaPhoto(media=img, caption=text, parse_mode="HTML")
                    )
                    media_to_send.append(InputMediaVideo(media=last_post.video))
                    response = context.bot.send_media_group(
                        settings.CHANEL_NAME, media=media_to_send
                    )
                    last_post.post_id = response[0].message_id
                    last_post.save()
            else:
                text = get_post_text_for_chanel_post(last_post, comment=False)
                if not last_post.video:
                    message = context.bot.send_photo(
                        settings.CHANEL_NAME,
                        photo=img,
                        caption=text,
                        parse_mode="HTML",
                    )
                    context.bot.send_message(
                        settings.CHANEL_NAME,
                        text=last_post.comment_review,
                        parse_mode="HTML",
                        reply_to_message_id=message.message_id,
                    )
                    last_post.post_id = message.message_id
                    last_post.save()
                else:
                    media_to_send = []
                    media_to_send.append(
                        InputMediaPhoto(media=img, caption=text, parse_mode="HTML")
                    )
                    media_to_send.append(InputMediaVideo(media=last_post.video))
                    response = context.bot.send_media_group(
                        settings.CHANEL_NAME, media=media_to_send
                    )
                    context.bot.send_message(
                        settings.CHANEL_NAME,
                        text=last_post.comment_review,
                        parse_mode="HTML",
                        reply_to_message_id=response[0].message_id,
                    )
                    last_post.post_id = response[0].message_id
                    last_post.save()
            last_post.status = Post.Status.SEND
            last_post.save()


def request_of_new_comment(update, context):
    query = update.callback_query
    data = query.data
    button_type, film_id, comment_id = data.split("_")
    post = Post.objects.get(film_id=film_id)
    chat_id = update.effective_message.chat_id
    profile = UserAdmin.objects.get(external_id=chat_id)
    context.user_data["post"] = post
    context.user_data["data"] = data
    schedule_post_with_choosen_comment(post, None, update, context)
    context.bot.send_message(chat_id, "Пришлите новый комментарий")
    return SAVE_NEW_COMMENT


def request_video(update, context):
    query = update.callback_query
    data = query.data
    button_type, film_id, comment_id = data.split("_")
    post = Post.objects.get(film_id=film_id)
    chat_id = update.effective_message.chat_id
    profile = UserAdmin.objects.get(external_id=chat_id)
    schedule_post_with_choosen_comment(post, comment_id, update, context)
    context.user_data["post"] = post
    context.bot.send_message(
        chat_id,
        "Пришлите видео файл",
        reply_markup=ReplyKeyboardMarkup([["Без видео 🙅"]], one_time_keyboard=True),
    )
    return SAVE_VIDEO


def save_new_comment(update, context):
    post = context.user_data["post"]
    comment = update.message.text
    post.comment_review = comment
    post.save()
    context.bot.send_message(
        update.effective_message.chat_id,
        "Комментарий сохранен",
        reply_markup=ReplyKeyboardMarkup([["Без видео 🙅"]], one_time_keyboard=True),
    )
    data = context.user_data["data"]
    button_type, film_id, comment_id = data.split("_")

    return SAVE_VIDEO


def save_video(update, context):
    post = context.user_data["post"]
    post.video = update.message.video.file_id
    post.save()
    context.bot.send_message(
        update.effective_message.chat_id, "Пост будет опубликован с видео"
    )
    return ConversationHandler.END


def no_video(update, context):
    update.message.reply_text("Пост будет опубликован без видео")
    return ConversationHandler.END


def count_scheduled_posts(update, context):
    count = Post.objects.filter(status=Post.Status.APPROVED).count()
    update.message.reply_text(f"Всего запланированных постов: {count}")


class Command(BaseCommand):
    help = "Телеграм бот"

    def handle(self, *args, **options):
        updater = Updater(settings.TOKEN)
        print("Бот запущен")
        print(os.getcwd())
        start_handler = CommandHandler("start", do_start)
        updater.dispatcher.add_handler(start_handler)

        conversation_edit_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(request_of_new_comment, pattern="(commentEdit)")
            ],
            states={
                0: [MessageHandler(Filters.text, save_new_comment)],
                1: [
                    MessageHandler(Filters.regex("^(Без видео 🙅)$"), no_video),
                    MessageHandler(Filters.video, save_video),
                ],
            },
            fallbacks=[],
        )
        updater.dispatcher.add_handler(conversation_edit_handler)

        conversation_approve_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(request_video, pattern="(commentPublish)")
            ],
            states={
                SAVE_VIDEO: [
                    MessageHandler(Filters.regex("^(Без видео 🙅)$"), no_video),
                    MessageHandler(Filters.video, save_video),
                ],
            },
            fallbacks=[],
        )
        updater.dispatcher.add_handler(conversation_approve_handler)

        comment_buttons_handler = CallbackQueryHandler(keyboard_handler)
        updater.dispatcher.add_handler(comment_buttons_handler)

        count_scheduled_posts_handler = CommandHandler("count", count_scheduled_posts)
        updater.dispatcher.add_handler(count_scheduled_posts_handler)

        updater.job_queue.run_repeating(post_scheduled_film, interval=7 * 60, first=0)

        updater.start_polling()
        updater.idle()
