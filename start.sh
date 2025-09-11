#!/bin/sh

ollama serve &

sleep 5

ollama pull llama-guard3:1b
# echo "TEST WE"

tail -f /dev/null