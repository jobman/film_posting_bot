comments_dir = "rezka_django/data/comments/"
comment_to_find = "ШЕДЕВР, на века!"

import os
import json

file_list = os.listdir(comments_dir)
counter = 1
maximum = len(file_list)
finded = False
for file in file_list:
    print(f"{counter}/{maximum} {file}")
    counter += 1
    comments_file = comments_dir + file
    with open(comments_file, "r") as f:
        comments_string = f.read()
        comments = json.loads(comments_string)
        for comment in comments:
            if comment_to_find in comment[0]:
                print(comment[0])
                print(comment[1])
                print("\n")
                print(file)
                finded = True
                break
    if finded:
        break
