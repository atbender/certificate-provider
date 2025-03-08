#!/bin/bash

mkdir -p /usr/local/share/fonts/

cp /app/assets/DancingScript-Regular.ttf /usr/local/share/fonts/ 2>/dev/null

fc-cache -f
