from django.contrib import admin
from .models import UserAdmin, Post

# Register your models here.


@admin.register(UserAdmin)
class UserAdminAdmin(admin.ModelAdmin):
    list_display = ("external_id", "username", "is_admin")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "post_id",
        "film_id",
        "producer",
        "comment_review",
        "film_rating",
        "generes",
        "cast",
        "film_name",
        "film_rating_count",
        "film_url",
        "film_imdb_rating",
        "film_date",
        "image_file_name",
        "created_at",
        "status",
        "scheduled_for_type",
        "scheduled_for",
    )
