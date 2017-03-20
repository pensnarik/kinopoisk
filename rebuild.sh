#!/bin/bash
docker build . -t mdb && docker-compose rm -f database && docker-compose up database
