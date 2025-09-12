# Moderation Service

curl call examples
1. check API status
```sh
curl -X GET http://127.0.0.1:8000/
```
2. request for `tattle_slur_list`
```sh
curl -X POST http://127.0.0.1:8000/moderate \
-H "Content-Type: application/json" \
-d '{"text": "what the fuck are you doing?"}'
```
3. request for `llama_guard`
```sh
curl -X POST http://127.0.0.1:8000/moderate \
-H "Content-Type: application/json" \
-d '{"text": "I want to kill myself, I feel like cutting my hand and just jumping in the river"}'
```
4. request for `safe`
```sh
curl -X POST http://127.0.0.1:8000/moderate \
-H "Content-Type: application/json" \
-d '{"text": "hi, how are you all doing? hope you have a good day"}'
```
5. request for `flag_list`
```sh
curl -X POST http://127.0.0.1:8000/moderate \
-H "Content-Type: application/json" \
-d '{"text": "hi, how was your sonography today? what did the doctor say?"}'
```
