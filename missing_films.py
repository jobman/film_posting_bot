import csv

with open("rezka.csv", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    film_urls = []
    for film in reader:
        if film["film_name"] != "NO P2P TRAFFIC IS PERMITTED ON THIS SERVER":
            continue
        else:
            film_urls.append(film["film_url"])
    # print(film_urls)

# save to file missing_films.txt film_urls
with open("missing_films.txt", "w", encoding="utf-8") as f:
    for url in film_urls:
        f.write(url + "\n")
