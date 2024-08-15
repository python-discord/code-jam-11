#!/bin/bash


watchmedo auto-restart --directory=./app/ --pattern=*.py --recursive --debounce-interval=2 -- python -m app.main
