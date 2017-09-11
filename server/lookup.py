import requests
import sys

print(requests.post("http://127.0.0.1:16384/simplify", json=dict(text=" ".join(sys.argv[1:]))).content.decode())
