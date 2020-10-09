#!/bin/bash

exec gunicorn -c gunicorn.py exporter:app