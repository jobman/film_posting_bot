comments_dir = "rezka_django/data/comments/"
file_number = 10224
import os
import json

file = str(file_number) + ".txt"
comments_file = comments_dir + file
with open(comments_file, "r") as f:
    comments_string = f.read()
    comments = json.loads(comments_string)
    for comment in comments:
        print(comment[0])
