#!/bin/bash

rsync -avz --compress-level=9 --progress unica1.parselab.ru:~/kinopoisk/cache .
rsync -avz --compress-level=9 --progress unica2.parselab.ru:~/kinopoisk/cache .
rsync -avz --compress-level=9 --progress unica3.parselab.ru:~/kinopoisk/cache .
rsync -avz --compress-level=9 --progress unica4.parselab.ru:~/kinopoisk/cache .
rsync -avz --compress-level=9 --progress unica5.parselab.ru:~/kinopoisk/cache .
rsync -avz --compress-level=9 --progress unica6.parselab.ru:~/kinopoisk/cache .
rsync -avz --compress-level=9 --progress unica7.parselab.ru:~/kinopoisk/cache .
rsync -avz --compress-level=9 --progress crm.smartsales.su:~/kinopoisk/cache .
rsync -avz --compress-level=9 --progress new.smartsales.su:~/kinopoisk/cache .
rsync -avz --compress-level=9 --progress store.parselab.ru:~/kinopoisk/cache .
rsync -avz --compress-level=9 --progress mutex@unicadb.parselab.ru:~/kinopoisk/cache .
rsync -avz --compress-level=9 --progress parser8.parselab.ru:~/kinopoisk/cache .
