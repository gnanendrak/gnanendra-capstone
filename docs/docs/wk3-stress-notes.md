.Finding 1 — Malformed JSON. Response codes for each of the four bad inputs; 
curl -i -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{}'
HTTP/1.1 422 Unprocessable Entity
date: Wed, 09 Sep 2026 11:04:57 GMT
server: uvicorn
content-length: 91
content-type: application/json

{"detail":[{"type":"missing","loc":["body","question"],"msg":"Field required","input":{}}]}%                                                                                                                      gnanendra@Gnanendras-MacBook-Pro 

curl -i -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"q": "What is the leave policy?"}'
HTTP/1.1 422 Unprocessable Entity
date: Wed, 09 Sep 2026 11:05:34 GMT
server: uvicorn
content-length: 122
content-type: application/json

{"detail":[{"type":"missing","loc":["body","question"],"msg":"Field required","input":{"q":"What is the leave policy?"}}]}

curl -i -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question": 42}'
HTTP/1.1 422 Unprocessable Entity
date: Wed, 09 Sep 2026 11:06:16 GMT
server: uvicorn
content-length: 111
content-type: application/json

{"detail":[{"type":"string_type","loc":["body","question"],"msg":"Input should be a valid string","input":42}]}

curl -i -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question": "What is the leave policy?"'
HTTP/1.1 422 Unprocessable Entity
date: Wed, 09 Sep 2026 11:06:22 GMT
server: uvicorn
content-length: 133
content-type: application/json

{"detail":[{"type":"json_invalid","loc":["body",40],"msg":"JSON decode error","input":{},"ctx":{"error":"Expecting ',' delimiter"}}]}%  

• Finding 2 — 5000-character question. Total wall time observed; 
curl -N -X POST http://localhost:8000/ask -H "Content-Type: application/json"  0.02s user 0.05s system 0% cpu 42.228 total

• Finding 3 — Disconnect mid-stream. What the server logged on --max-time 1;
curl --max-time 1 -N -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question": "Please give me a long answer about something complicated"}'
(simulated answer for: Please give me a long answer about something complicated...) %   

• Finding 4 — 50 parallel requests. Successes out of 50; p50 / p95 latency; effective req/s;
python3 scripts/stress_test.py --requests 50 --concurrent 10
Stress test: 50 requests, up to 10 concurrent
────────────────────────────────────────────────────────────
Total wall time:   5.12s
Successes:         50 / 50
Effective req/s:   9.77

Latency (successful requests):
  min:   0.32s
  p50:   0.93s
  p95:   1.45s
  max:   1.46s
