import csv
from matplotlib import pyplot as plt

# csv headers
# cast,date,film_id,film_name,film_rating,film_rating_count,film_url,genre,image_url,imdb,producer


with open("rezka.csv", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    film_list = []
    for film in reader:
        film["film_rating"] = float(film["film_rating"])
        film["film_rating_count"] = int(film["film_rating_count"])
        if film["imdb"]:
            film["imdb"] = float(film["imdb"])
        film_list.append(film)

film_rating_data = (
    (film["film_rating_count"], 1 / (11 - film["film_rating"])) for film in film_list
)
