#!/bin/sh

ollama serve &

sleep 5

ollama pull llama-guard3:1b

python server.py