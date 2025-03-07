#!/bin/bash

mkdir -p /usr/local/share/fonts/

cp /app/assets/DancingScript-Regular.ttf /usr/local/share/fonts/ 2>/dev/null

fc-cache -f

echo "Font installation completed"
ls -la /usr/local/share/fonts/DancingScript-Regular.ttf 2>/dev/null || echo "Font not found"