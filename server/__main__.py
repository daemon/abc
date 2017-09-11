import cherrypy
import cherrypy_cors
import codecs
import gensim
import inflect
import json
import math
import re
import requests
import spacy
from spacy.parts_of_speech import ADJ, VERB, NOUN, ADV

symbols = dict(ADV='adv', VERB='v', NOUN='n', ADJ='adj')
eq_table = dict(VBN='VERB')

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
  def __init__(self, top10k, top100k, nlp, model):
    self.top10k = top10k
    self.top100k = top100k
    self.nlp = nlp
    self.model = model
    self.cache = {}
    self.engine = inflect.engine()
    self.word_pattern = re.compile(r"^\w[\w\.\d]*$")
  
  def align_whitespace(self, word1, target):
    if word1[0] == " " and target[0] != " ":
      target = " " + target
    if word1[-1] == " " and target[-1] != " ":
      target = target + " "
    return target

  def align_capitalization(self, word1, target):
    if word1 == target:
      return word1
    cutoff = ""
    try:
      cutoff = target[1:]
    except:
      pass
    if word1[0].isupper():
      return "{}{}".format(target[0].upper(), cutoff.lower())
    return target.lower()

  def is_plural(self, token):
    return True if (token.tag_ == "VBZ" or token.pos == NOUN) and token.lemma != token.lower else False

  def pluralize(self, original, target):
    if self.is_plural(original) and not self.is_plural(target):
      try:
        return self.engine.plural(target.text)
      except:
        pass
    return target.text

  def compute_score(self, word, original, context):
    if not re.match(self.word_pattern, word):
      return -100
    score = 0.
    tok = self.nlp(word)[0]
    context = context.replace(original, word)
    if tok.lemma_.lower() not in self.top100k:
      score -= 20
    similarity = self.model.score([context.split()])[0]
    if similarity == 0.:
      score -= 100
    else:
      score += 100 * math.exp(0.01 * similarity)
    synonyms = [entry["word"].lower() for entry in self.find_synonyms(word)][:8]
    score += 100 * -self.top100k[tok.lemma_.lower()] / 100000
    if original.lower() in synonyms:
      score += 20
    print("{} {}".format(word, score))
    return score

  def find_synonyms(self, word):
    if word.lower() not in self.cache:
      self.cache[word.lower()] = json.loads(requests.get("https://api.datamuse.com/words?ml={}".format(word.lower())).content.decode())
    return self.cache[word.lower()]

  def find_easiest_synonym(self, token, context):
    word = token.text
    pos = token.pos_
    tag = token.tag_
    print(word, pos, tag)
    try:
      pos = eq_table[tag]
    except KeyError:
      pass
    try:
      symbol = symbols[pos]
    except:
      return word
    if token.lemma_.lower() in self.top10k or token.text.lower() in self.top10k:
      return word
    results = self.find_synonyms(word)
    try:
      top_score = -100 + self.compute_score(word.lower(), word.lower(), context)
    except:
      top_score = -100
    best_word = word
    index = 0
    for entry in results:
      try:
        if symbol not in entry["tags"]:
          continue
        if index >= 8 or (int(entry["score"]) < index * 10000 and index > 1):
          break
        index += 1
        if self.nlp(entry["word"])[0].tag_ != "VBG" and token.tag_ == "VBG":
          continue
        candidate = entry["word"].lower()
        score = self.compute_score(candidate, word.lower(), context)
        if score > top_score:
          best_word = candidate
          top_score = score
      except:
        continue
    best_word = self.nlp(best_word)[0]
    return self.align_capitalization(word, self.pluralize(token, best_word))

  exposed = True
  @cherrypy.tools.json_out()
  @json_in
  def POST(self, **kwargs):
    text = kwargs["text"]
    doc = self.nlp(text)
    doc_text = []
    for sent in doc.sents:
      context = sent.text
      words = []
      for word in sent:
        tok = word
        word = word.text
        if re.match(self.word_pattern, word):
          synonym = self.find_easiest_synonym(tok, context)
          context = context.replace(word, synonym)
          word = " " + synonym
        words.append(word)
      doc_text.append("".join(words).strip())
    return dict(text=self.align_whitespace(text, " ".join(doc_text)))

def read_wordlists():
  top_10k = {}
  top_100k = {}
  i = 0
  with codecs.open("top5k", "r", "utf8") as f:
    for line in f.readlines():
      i += 1
      if line.lower().strip() not in top_10k:
        top_10k[line.lower().strip()] = i
  with codecs.open("top5k", "r", "utf8") as f:
    for line in f.readlines():
      i += 1
      if line.lower().strip() not in top_100k:
        top_100k[line.lower().strip()] = i
  return (top_10k, top_100k)

def main():
  nlp = spacy.load("en_core_web_md")
  top10k, top100k = read_wordlists()
  model = gensim.models.Word2Vec.load(r"A:\reddit_rc.db.wv")
  run_server(top10k, top100k, nlp, model)

def run_server(top10k, top100k, nlp, model):
  cherrypy.config.update({
    "environment": "production",
    "log.screen": True
  })
  cherrypy.server.socket_port = 16384
  #cherrypy.server.socket_host = "0.0.0.0"
  rest_conf = {"/": {
    "request.dispatch": cherrypy.dispatch.MethodDispatcher(),
    'cors.expose.on': True
  }}
  cherrypy_cors.install()
  cherrypy.quickstart(SimplifyEndpoint(top10k, top100k, nlp, model), "/simplify", rest_conf)
  
if __name__ == '__main__':
  main()
