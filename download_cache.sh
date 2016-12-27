#!/bin/bash

rsync -avz --compress-level=9 --progress unica1:~/kinopoisk/cache .
rsync -avz --compress-level=9 --progress unica2:~/kinopoisk/cache .
rsync -avz --compress-level=9 --progress unica3:~/kinopoisk/cache .
rsync -avz --compress-level=9 --progress unica4:~/kinopoisk/cache .
rsync -avz --compress-level=9 --progress unica5:~/kinopoisk/cache .
rsync -avz --compress-level=9 --progress unica6:~/kinopoisk/cache .
rsync -avz --compress-level=9 --progress unica7:~/kinopoisk/cache .
rsync -avz --compress-level=9 --progress crm.smartsales.su:~/kinopoisk/cache .
rsync -avz --compress-level=9 --progress new.smartsales.su:~/kinopoisk/cache .
rsync -avz --compress-level=9 --progress store.parselab.ru:~/kinopoisk/cache .
rsync -avz --compress-level=9 --progress mutex@unicadb.parselab.ru:~/kinopoisk/cache .
