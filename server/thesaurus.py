from nltk.corpus import wordnet as wn
from scipy.sparse import lil_matrix, csc_matrix
from scipy.spatial.distance import cosine
from sklearn.utils.extmath import randomized_svd
#import gensim
import json
import nltk
import numpy as np

class WordNetVocabulary(object):
  def __init__(self, dictionary):
    self.definitions = sorted(list(dictionary.keys()))
    self.id_table = {}
    for defn, i in zip(self.definitions, range(len(self.definitions))):
      self.id_table[defn] = i
    self.n_definitions = float(len(self.definitions))
    self.term_table = {}
    self.freq_table = {}
    for _, v in dictionary.items():
      self._compute_freq_table(v, self.freq_table)
    for word, i in zip(sorted(list(self.freq_table.keys())), range(len(self.freq_table))):
      self.term_table[word] = i
    self.n_terms = len(self.freq_table)
    self._init_svd(dictionary, self.definitions)

  def _compute_freq_table(self, corpus, freq_table=None):
    if freq_table is None:
      freq_table = {}
    for word in nltk.word_tokenize(corpus):
      try:
        freq_table[word.lower()] += 1
      except:
        freq_table[word.lower()] = 1
    return freq_table

  def compute_freq_vec(self, text):
    vec = np.zeros(self.n_terms)
    freq_table = self._compute_freq_table(text)
    for term, freq in freq_table.items():
      vec[self.term_table[term]] = freq
    return vec

  def synonyms_by_word(self, word, topn=3):
    return self.synonyms_by_synset(wn.synsets(word)[0].name(), topn)

  def synonyms_by_synset(self, synset_name, topn=3):
    ssid = self.id_table[synset_name]
    doc = self.doc_matrix[ssid]
    found_indices = set([ssid])
    synonyms = []
    for _ in range(topn):
      min_index = 0
      min_val = 10
      for i in range(self.doc_matrix.shape[0]):
        cos_dist = cosine(self.doc_matrix[i], doc)
        if i not in found_indices and cos_dist < min_val:
          min_index = i
          min_val = cos_dist
      found_indices.add(min_index)
      synonyms.append((self.definitions[min_index], min_val))
    return synonyms

  def _init_svd(self, dictionary, definitions):
    self.td_matrix = lil_matrix((len(dictionary), self.n_terms))
    for defn, i in zip(definitions, range(len(definitions))):
      if i % 100 == 0:
        print("Building term-document matrix: {} / {}".format(i, len(dictionary)), end="\r")
      self.td_matrix[i, :] = self.compute_freq_vec(dictionary[defn])
    self.td_matrix = self.td_matrix.transpose().tocsr()
    print()
    for i in range(self.n_terms):
      n = float(self.td_matrix[i, :].getnnz())
      if i % 100 == 0:
        print("Applying td-idf: {} / {}".format(i, self.n_terms), end="\r")
      if n > 0:
        self.td_matrix[i, :] *= np.log(len(dictionary) / n)
    print()
    print("Performing rank reduction...")
    self.u, self.s, self.vt = randomized_svd(self.td_matrix, 50, transpose=False)
    self.doc_matrix = np.matmul(np.diag(self.s), self.vt).transpose()

  @staticmethod
  def generate(filename="dictionary.json"):
    dictionary = {}
    for synset in wn.all_synsets():
      dictionary[synset.name()] = synset.definition()
    with open(filename, "w") as f:
      f.write(json.dumps(dictionary))

  @staticmethod
  def load(filename="dictionary.json"):
    with open(filename) as f:
      dictionary = json.loads(f.read())
    return WordNetVocabulary(dictionary)

vocab = WordNetVocabulary.load()

