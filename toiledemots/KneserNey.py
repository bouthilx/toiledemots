# -*- coding: utf-8 -*-

import time
import ngrams as ng
from timer import Timer, seconds_to_string
import sys

class LanguageModel(object):
    """
        a_z
            An N-gram where a is the first word, z is the last word, and "_" represents 0 or more words in between. 
        p(a_z)
            The estimated conditional probability of the nth word z given the first n-1 words (a_) of an N-gram. 
        a_
            The n-1 word prefix of the N-gram a_z. 
        _z
            The n-1 word suffix of the N-gram a_z. 
        c(a_z)
            The count of N-gram a_z in the training data. 
        n(*_z)
            The number of unique N-grams that match a given pattern. ``(*)'' represents a wildcard matching a single word. 
        n1,n[1]
            The number of unique N-grams with count = 1. 
    """

    def __init__(self,ngrams,alpha=3,modified=False,interpolate=True):
        self.ngrams = ngrams
        self.alpha = alpha
        self.interpolate = interpolate

    def __nc(self,n,c):
        """
            n1,n[1] The number of unique N-grams with count = 1. 
        """
        return len(self.ngrams.grams_with_count(n,c))

    def __c(self,ngram):
        """
            c(a_z) : The count of N-gram a_z in the training data. 
        """
        return self.ngrams[ngram]

    def __csum(self,ngram):
        """
            c(a_*) : The sum of count of N-gram a_* in the training data. 
        """
        return self.ngrams.csum(len(ngram),ngram,(0,-1)) #sum([self.ngrams[w] for w in self.ngrams.contains(ngram,(0,-1))])

    def __n(self,ngram,wildcards):
        """
            n(*_z) The number of unique N-grams that match a given pattern. ``(*)'' represents a wildcard matching a single word. 
            wildcards = (1,0) or (1,1) or (0,1)
        """
        return self.ngrams.lencontains(ngram,(wildcards[0],wildcards[1]*-1))#len(self.ngrams.contains(ngram,(wildcards[0],wildcards[1]*-1)))

    def __f(self,ngram):
        """
            f(a_z) = (c(a_z) - D0) / c(a_) ;; for highest order N-grams
        """
        try:
            return (self.__c(ngram)-self.__D(ngram))/(.0+self.__csum(ngram))
        except ZeroDivisionError as e:
            return 0.0



    def __fl(self,ngram):
        """
            f(_z)  = (n(*_z) - D1) / n(*_*) ;; for lower order N-grams
        """
        e_ngram = tuple([""]+list(ngram))
        try:
            return (self.__n(e_ngram,(1,0))-self.__D(ngram))/(.0+self.__n(e_ngram,(1,1)))
        except ZeroDivisionError as e:
            return 0.0

    def __g(self,ngram):
        """
            g(a_z) = max(0, c(a_z) - D) / c(a_*)
        """
        if self.__c(ngram[:-1])>0:
            try:
                return max(0,self.__c(ngram) - self.__D(ngram)) / (.0+ self.__csum(ngram))
            except ZeroDivisionError as e:
                return 0.0
        else:
            return 0.0

    def __gl(self,ngram):
        """
            gl(_z)  = max(0, n(*_z) - D) / n(*_*)
        """
        e_ngram = tuple([""]+list(ngram))
        if self.__n(e_ngram,(1,1))>0:
            try:
                return max(0,self.__n(e_ngram,(1,0))-self.__D(ngram)) / (.0+ self.__n(e_ngram,(1,1)))
            except ZeroDivisionError as e:
                return 0.0
        else:
            return 0.0

    def __bow(self,ngram):
        """
            bow(a_) = D n(a_*) / c(a_*)
        """
        e_ngram = tuple(list(ngram)+[""])
        if self.__c(ngram)>0:
            try:
                return self.__D(ngram)*self.__n(e_ngram,(0,1)) / (.0+ self.__csum(ngram))
            except ZeroDivisionError as e:
                return 0.0
        else:
            return 0.0

    def __bowl(self,ngram):
        """
            bow(_)  = D n(_*) / n(*_*)
        """
        if self.__n(tuple([""]+list(ngram)+[""]),(1,1))>0:
            try:
                return self.__D(ngram)*self.__n(tuple(list(ngram)+[""]),(0,1)) / (.0+ self.__n(tuple([""]+list(ngram)+[""]),(1,1)))
            except ZeroDivisionError as e:
                return 0.0
        else:
            return 0.0

    def __D(self,ngram):
        """
            D = n1 / (n1+2*n2)
        """
        n1 = self.__nc(len(ngram),1)
        try:
            return n1 / (0.+ (n1+2*self.__nc(len(ngram),2)))
        except ZeroDivisionError as e:
            return 0.0

    def __d_index(self,ngram):
        return len(self.ngrams)-len(ngram)-1

    def __mD(self,ngram):
        """ 
            Y  = n1 / (n1+2*n2)
            D1 = 1 - 2*Y(n2/n1)
            D2 = 2 - 3*Y(n3/n2)
            D3 = 3 - 4*Y(n4/n3)
            ...
        """
        return 0.0

    def p(self,ngram,higher=True):
        """
            p(a_z) = g(a_z) + bow(a_)p(_z) ; Eqn.4
        """
        if len(ngram)>self.ngrams.get_max_arity():
            return self.p(ngram[len(ngram)-self.ngrams.get_max_arity():])*self.p(ngram[:-1])

        if len(ngram)==2 and self.ngrams.get_max_arity()>2:
            gl = self.__gl(ngram)
            bowl = self.__bowl(ngram[:-1])
            p = self.p(ngram[1:],higher=False)
            return gl+bowl*p
        if len(ngram)==1:
            return self.ngrams.freq(ngram)

        nt = len(ngram)

        g = self.__g(ngram)

        if higher:
            mult = self.__bow(ngram[:-1])
        else:
            mult = self.__bowl(ngram[:-1])

        mult = mult * self.p(ngram[1:],higher=True)

        if self.interpolate and higher:
            p = g+mult
        elif self.interpolate:
            p = self.__gl(ngram)+mult
        elif ngram in self.ngrams and higher:
            p = self.__f(ngram)
        elif ngram in self.ngrams:
            p = self.__fl(ngram)
        else:
            p = mult

        return p
        
if __name__ == "__main__":
    ngram = ng.nGrams(3)
    ngram.build([u"C'est un test bien simple", u"Ça ne fait pas beaucoup de mots"])
    ngram.print_list()
    lm = LanguageModel(ngram,alpha=2)
    print "C'est un test bien simple"
    print "Ça ne fait pas beaucoup de mots"
    print "un : ",lm.p((u'un',))
    print "anticonstitutionnellement : ",lm.p((u'anticonstitutionnellement',))
    print "un anticonstitutionnellement : ",lm.p((u'un',u'anticonstitutionnellement',))
    print "un test : ",lm.p((u'un',u'test'))
    print "un test coucou : ",lm.p((u'un',u'test',u'coucou'))
    print "un coucou test : ",lm.p((u'un',u'coucou',u'test'))

    ngram = ng.nGrams(4)
    ngram.load('../data/french')
    lm = LanguageModel(ngram,alpha=2,interpolate=False)
    lmi = LanguageModel(ngram,alpha=2)
    start = time.time()
    print "est un quiqwe  : ",lmi.p((u'est',u'un',u'quiqwe'))
    print "It tooks ",time.time()-start,"s"
    start = time.time()
    print "est un quiqwe  : ",lmi.p((u'est',u'un',u'quiqwe'))
    print "It tooks ",time.time()-start,"s"
    start = time.time()
    print "est un zimbabwéen  : ",lmi.p((u'est',u'un',u'zimbabwéen'))
    print "It tooks ",time.time()-start,"s"
    start = time.time()
    print "est un président  : ",lmi.p((u'est',u'un',u'président'))
    print "It tooks ",time.time()-start,"s"
    start = time.time()
    print "ceci est un  : ",lmi.p((u'ceci',u'est',u'un'))
    print "It tooks ",time.time()-start,"s"
    start = time.time()
    print "Voici une phrase plutôt simple",lmi.p((u'Voici',u'une',u'phrase',u'plutôt',u'simple'))
    print "It tooks ",time.time()-start,"s"
    start = time.time()
    print "Phrase formé mal avec qwetrqq inconnu mot",lmi.p((u'Phrase',u'formé',u'mal',u'avec',u'qwetrqq',u'inconnu',u'mot'))
    print "It tooks ",time.time()-start,"s"

#    sys.exit(0)

    tmps = 0
    tmpss = 0
    t = Timer(ngram.len(2))
    t.start()
    # need 3-grams for this
    for i, ng in enumerate(ngram.getgrams(2)):
        tmps = 0
        for j, nng in enumerate(ngram.contains(tuple(list(ng)+[""]),(0,-1))):
            tmps += lmi.p(nng)

        tmpss += tmps
        update = t.update(1)
        if update:
            sys.stderr.write("time remaining : "+seconds_to_string(update)+"\n")
        print i,tmpss
        print "tmp %i : %f" % (i,tmpss/(0.+i+1))

    print "final : ",tmpss/(0.+ngram.len(2))
