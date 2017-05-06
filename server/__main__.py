import cherrypy
import spacy

def json_in(f):
  def merge_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z
  def wrapper(*args, **kwargs):
    cl = cherrypy.request.headers["Content-Length"]
    data = json.loads(cherrypy.request.body.read(int(cl)).decode("utf-8"))
    kwargs = merge_dicts(kwargs, data)
    return f(*args, **kwargs)
  return wrapper

class SimplifyEndpoint:
  exposed = True
  @cherrypy.tools.json_out()
  @json_in
  def POST(**kwargs):
    text = kwargs["text"]
    
    return dict(text=text)

def read_wordlists():
  top_10k = {}
  top_100k = {}
  i = 0
  with open("top10k") as f:
    for line in f.readlines():
      i += 1
      top_10k[line.lower().strip()] = i
  with open("top100k") as f:
    for line in f.readlines():
      i += 1
      top_100k[line.lower().strip()] = i
  return (top_10k, top_100k)

def main():
  nlp = spacy.load("en")
  results = nlp("The cat liked the hat, and it enjoyed company.")
  print(results)
  print("OK")
  (top10k, top100k) = read_wordlists()
  run_server(top10k, top100k)

def run_server(top10k, top100k):
  cherrypy.config.update({
    "environment": "production",
    "log.screen": True
  })
  cherrypy.server.socket_port = 8888
  cherrypy.server.socket_host = "0.0.0.0"
  rest_conf = {"/": {"request.dispatch": cherrypy.dispatch.MethodDispatcher()}}
  cherrypy.tree.mount(SimplifyEndpoint(), "/simplify", rest_conf)
  cherrypy.engine.start()
  cherrypy.engine.block()
  
if __name__ == '__main__':
  main()
