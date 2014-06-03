from collections import defaultdict
from ngrams import nGrams
import Levenshtein
import gc

voyelles = ["a", "e", "i", "o", "u", "y"]

def distance(string1, string2):
    points = 0

    if len(string1) < len(string2):
        return max(distance(" "+string1, string2), distance(string1+" ", string2))
    elif len(string1) > len(string2):
        return max(distance(string1, " "+string2), distance(string1, string2+" "))

    for i in range(len(string1)+1):
        for j in xrange(i+1, len(string1)+1):
#            print string1[i:j], string2[i:j]
            if string1[i:j] == string2[i:j]:
                if all(letter in voyelles for letter in string1[i:j]):
                    points += 2
                else:
                    points += 1

    return points

class Toile(set):
    """
    .. todo:: 

        WRITEME
    """
    
    def __init__(self, min_count=10):
        self.__toile = defaultdict(set)
        self.min_count = min_count

    def build(self, lines):

        ngrams = nGrams(1)
        ngrams.build(lines, del_lines=True)

        lines = None
        gc.collect()

        for ngram in ngrams.getgrams(1):
            if ngrams[ngram] > self.min_count:
                self.add(ngram[0])

            del ngrams[ngram]

        ngrams = None
        gc.collect()

    def __getitem__(self, key):
        return self.__toile[key]

    def add(self, word):
        if word not in self.__toile[len(word)]:
            self.__toile[len(word)].add(word)

    def get_closests(self, word, max_dist=4):
        candidats = []

        for length in xrange(len(word)-2, len(word)+3):
            for candidat in self[length]:
                    
#                dist = Levenshtein.distance(word, candidat)
                dist = distance(word, candidat)

        #            if dist <= max_dist:
                candidats.append((dist, candidat))

        return sorted(candidats, reverse=True)









if __name__ == "__main__":
    distance("bonjour", "honneur")
