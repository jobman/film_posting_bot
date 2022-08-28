import csv

with open("rezka.csv", encoding="utf-8") as csvfile:
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

print(len(best_films))
