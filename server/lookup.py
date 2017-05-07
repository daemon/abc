import requests
import sys

print(requests.post("http://0.0.0.0:8888/simplify", json=dict(text=sys.argv[1])).content.decode())
