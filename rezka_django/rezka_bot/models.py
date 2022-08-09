from django.db import models

# Create your models here.
class UserAdmin(models.Model):
    external_id = models.PositiveIntegerField(
        verbose_name="ID пользователя в Telegram",
        unique=True,
    )
    username = models.TextField(verbose_name="Ник в Telegram")

    is_admin = models.BooleanField(
        verbose_name="Администратор",
        default=False,
    )

    def __str__(self):
        return f"@{self.username} #{self.external_id}"

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"


class Post(models.Model):
    profile = models.ForeignKey(
        to="rezka_bot.UserAdmin",
        verbose_name="Профиль",
        on_delete=models.PROTECT,
    )
    post_id = models.PositiveIntegerField(
        verbose_name="ID сообщения в Telegram",
        default=0,
    )
    film_id = models.PositiveIntegerField(
        verbose_name="ID в в базе фильмов",
        unique=True,
    )

    producer = models.TextField(
        verbose_name="Режиссер",
        null=True,
    )

    comment_review = models.TextField(
        verbose_name="Комментарий",
        default="",
    )

    film_rating = models.FloatField(
        verbose_name="Рейтинг",
    )

    generes = models.TextField(
        verbose_name="Жанры",
    )

    cast = models.TextField(
        verbose_name="Актеры",
    )

    film_name = models.TextField(
        verbose_name="Название фильма",
    )

    film_rating_count = models.PositiveIntegerField(
        verbose_name="Количество оценок",
    )

    film_url = models.TextField(
        verbose_name="Ссылка на фильм",
    )

    film_imdb_rating = models.FloatField(
        verbose_name="Рейтинг IMDB",
        null=True,
    )

    film_date = models.TextField(
        verbose_name="Дата выхода",
        null=True,
    )

    image_file_name = models.TextField(
        verbose_name="Имя файла изображения",
    )

    created_at = models.DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True,
    )

    scheduled_for = models.DateTimeField(
        verbose_name="Время публикации",
        null=True,
    )

    class Status(models.TextChoices):
        ON_REVIEW = (1, "На рассмотрении")
        APPROVED = (2, "Подтверждено")
        DECLINE = (3, "Отклонено")
        SEND = (4, "Отправлено")

    status = models.CharField(
        verbose_name="Статус",
        max_length=20,
        choices=Status.choices,
        default=Status.ON_REVIEW,
    )

    random_shift_for_posting = models.IntegerField(
        verbose_name="Сдвиг времени публикации",
        null=True,
    )

    video = models.TextField(
        verbose_name="ID видео файла",
        null=True,
    )

    class Scheduled_for_type(models.TextChoices):
        MORNING = (1, "Утром")
        AFTERNOON = (2, "Днем")
        EVENING = (3, "Вечером")

    scheduled_for_type = models.CharField(
        verbose_name="Время публикации",
        max_length=20,
        choices=Scheduled_for_type.choices,
        null=True,
    )

    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Посты"
