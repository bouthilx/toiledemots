# -*- coding: utf-8 -*-

import sys
import time
import datetime
import re
from collections import defaultdict
from timer import Timer, seconds_to_string
import codecs
from cache import Cache

import copy


# wildcard replaced by (i) (j is useless? => (0,3) is sorted as (0,2))

#ends_with -> search_range(item,sorted_reversed_words_list)
#sandwich -> search_range(item,
#               sorted_reversed_words(search_range(item,sorted_list)))

def search_ngram_range(ngram,l,wildcard=(0,0)):
    """
        search ngrams fitting *ngram*

        Arguments:
            
            ngram: the ngram to fit
            l: the list of ngrams
            wildcard: the wildcard to apply on ngram

        Examples:

            l = list of 3-grams
            ngram = (u"one",u"two",u"three")
            search_ngram_range(ngram,l,wildcard=(1,0))
            # it returns all the elements in l
            # that has the word two and three at 
            # index 1 and 2
    """

    i_min = 0
    i,j = 0,len(l)-1

    if wildcard[1] <= 0:
        wildcard = (wildcard[0], wildcard[1]+len(ngram))

    e = len(ngram)
    ngram = ngram[wildcard[0]:wildcard[1]]

    while j >= i:
        m = (j+i)/2

        if l[m][wildcard[0]:wildcard[1]] < ngram:
            i = m+1
            i_min=i
        else:
            j = m-1

    i -= 1
    j = len(l)-1
    i_max = len(l)

    while j >= i:
        m = (j+i)/2

        if l[m][wildcard[0]:wildcard[1]] <= ngram:
            i = m+1
        else:
            j = m-1
            i_max=m

    return (i_min,i_max)


def search_range(item,l):
    """
        search ngrams begginning with item

        Arguments:
            
            item: the word to fit
            l: the list of ngrams

        Examples:

            l = list of 3-grams
            item = (u"one",u"two")
            search_range(ngram,l)
            # it returns all the elements in l
            # that begins with u"onetwo"
    """
    i_min = 0
    i,j = 0,len(l)-1

    item = "".join(item)

    e = len(item)

    while j >= i:
        m = (j+i)/2

        if "".join(l[m]) < item:
            i = m+1
            i_min=i
        else:
            j = m-1

    i -= 1
    j = len(l)-1
    i_max = len(l)

    while j >= i:
        m = (j+i)/2

        if "".join(l[m])[:e] <= item:
            i = m+1
        else:
            j = m-1
            i_max=m

    return (i_min,i_max)

class nGrams(object):
    """
        n-gram

        Arguments:
            
            max_arity: the maximal arity of the n-gram. It will contain 1-gram,2-gram, ... up to n-gram

        An n-gram dictionnary that stores the n-gram and their counts. It is optimized
        to respond countly to successiv request (the first answer might be slow). 
        The drawback is that it may take a lot of memory space.

        Example:

            ngrams = nGrams(3)

            ngrams.build([u"C'est un test bien simple",u"Ça ne fait pas beaucoup de mots","est ce bien?"])
            ngram.print_list()
            ngram[(u"test",)]
            ngram.freq((u"test",))
            ngram.begins_with((u"te",))
            ngram.save("test_save")
            ...
    """

    def __init__(self,max_arity,min_count=0):
        """
            n-gram

            Arguments:
                
                max_arity: the maximal arity of the n-gram. It will contain 1-gram,2-gram, ... up to n-gram

            An n-gram dictionnary that stores the n-gram and their counts. It is optimized
            to respond countly to successiv request (the first answer might be slow). 
            The drawback is that it may take a lot of memory space.

            Example:

                ngrams = nGrams(3)
        """

        self.__max_arity = max_arity
        self.__ngrams = [defaultdict(int) for i in range(self.__max_arity)]
        self.__sorted_grams = [{} for i in range(self.__max_arity)]
        self.__len = 0
        self.__nlen = [0 for i in range(self.__max_arity)]
        self.__sum = Cache(4000)
        self.__nc = Cache(4000)
        self.__contains = Cache(4000)
        self.__lencontains = Cache(4000)
        self.__gwc = Cache(4000)
        self.__n = Cache(4000)

        self.__min_count = min_count

    def get_max_arity(self):
        """
        """

        return len(self.__ngrams)#self.__max_arity

    def set_minimal_count(self,minimal_count):
        self.__min_count = minimal_count

    def get_minimal_count(self):
        return self.__min_count

    def subgrams(self,max_arity):
        """
            Returns an ngram of a sub-max-arity
            the list pointed by this subngrams are the same as the ngram 
            (any new build in the ngram will have impacts on the subngram)
            This is valuable for better memory use. (less redondancy)
        """
        # they point to the very same lists
        ngrams = copy.copy(self)# nGrams(max_arity)
        
        # we gap the max_arity
        ngrams.__max_arity = max_arity
        ngrams.__ngrams = ngrams.__ngrams[:max_arity]
        ngrams.__sorted_grams = ngrams.__sorted_grams[:max_arity]
        ngrams.__nlen = ngrams.__nlen[:max_arity]

        return ngrams

#    def set_max_arity(self,max_arity):
#        if self.__max_arity > max_arity:
#            for i in xrange(max_arity,self.__max_arity):
#                del self.__ngrams[i]
#            self.__max_arity = max_arity
#        elif self.__max_arity < max_arity:
#            raise ValueError("max_arity can only be smaller than current one, otherwise build again a new n-gram")

    def __init_buffer(self):
        return ["" for i in range(self.__max_arity)]

    def __update_buffer(self,n_buffer,word):
        n_buffer = n_buffer[1:] + [word]

        for i in range(self.__max_arity):
            self.__ngrams[i][tuple([w for w in n_buffer[self.__max_arity-i-1:]])] += 1

        return n_buffer

    def __empty_buffer(self,n_buffer):

        while n_buffer[0]!="":
            n_buffer = n_buffer[1:] + [""]
            for i in range(self.__max_arity):
                self.__ngrams[i][tuple([w for w in n_buffer[self.__max_arity-i-1:]])] += 1

        return n_buffer

    def build(self,lines,clean_str=u'[!"%&\'\(\)\+,‚‘’\.\/:;=?\[\]«»¡£§²´µ·¸º°…“”•„−–—]',del_lines=False):
        """
            Arguments:
                
                lines: the lines to build the n-grams
                clean_str: a regular expression to clean the strings (default removes every special characters)

            Example:

                ngrams = nGrams(3)
                ngrams.build([u"C'est un test bien simple",u"Ça ne fait pas beaucoup de mots","est ce bien?"])
        """

        self.__len = 0
        self.__nlen = [0 for i in range(self.__max_arity)]

        sys.stderr.write("Building the %i-grams...\n" % self.__max_arity)
        n_lines = len(lines)
        n_buffer = self.__init_buffer() 

        t = Timer(n_lines,out=sys.stderr)
        t.start()
        for line in lines:

            line = line.lower().strip(u'\n')

            if clean_str:
                line = re.sub(clean_str, ' ', line)

            n_buffer = self.__init_buffer()

            for word in line.split(" "):
                word = word.strip(" ")#word.strip("-").strip(" ")

                if word:
                    n_buffer = self.__update_buffer(n_buffer,word)

            self.__empty_buffer(n_buffer)
                        
            t.print_update(1)
            
            del lines[0]

        sys.stderr.write("Sorting the %i-grams...\n" % self.__max_arity)

        len(self)
 
        for ng in range(self.__max_arity):
            self.__sort_keys(ng,(0,ng+1))

    def __sort_keys(self,ng,wildcard):
        """
            ng = i in i-gram
            wildcard = subset of i-grams 
                ex : (0,1) in 3-gram (a,b,c) => (a,b)
        """

        sys.stderr.write("Sorting the %i-grams with wildcard (%i,%i)...\n" % (ng+1,wildcard[0],wildcard[1]))

        self.__sorted_grams[ng][wildcard[0]] = sorted(self.__ngrams[ng].keys(),key=lambda a:a[wildcard[0]:])#wildcard[1]])
        sys.stderr.write("done.\n")

    def __get_sorted_grams(self,ng,wildcard):
        sorted_grams = self.__sorted_grams[ng].get(wildcard[0],None)
        if not sorted_grams:
            self.__sort_keys(ng,wildcard)
            return self.__sorted_grams[ng].get(wildcard[0],None)

        return sorted_grams

    def __wildcard(self,nt,wildcard):
        if wildcard[1] <= 0:
            wildcard = (wildcard[0],wildcard[1]+nt)

        return wildcard

    def begins_with(self,ngram):
        """
            Arguments:
                
                ngram: the ngram to test

            Returns:
                
                a list of every ngrams of length==len(ngram) that begins with ngram
        """

        i,j = search_range(ngram,self.__get_sorted_grams(len(ngram)-1,(0,len(ngram))))
        return self.__get_sorted_grams(len(ngram)-1,(0,len(ngram)))[i:j]

    def lencontains(self,ngram,wildcard=(0,0)):
        """
            Arguments:
                
                ngram: the ngram to test
                wildcard: the wildcard to apply on ngram

            Returns:

                the number of ngrams that contains the given ngram with the wildcard

            Examples:
                
                ngrams.lencontains((u"test",u"un"),(0,-1))
                # number of 2-grams with first word equal to test
        """

        wildcard = self.__wildcard(len(ngram),wildcard)
        
        if (ngram,wildcard) not in self.__lencontains:
            self.__lencontains[(ngram,wildcard)] = len(self.contains(ngram,wildcard))

        return self.__lencontains[(ngram,wildcard)]

    def contains(self,ngram,wildcard=(0,0)):
        """
            Arguments:
                
                ngram: the ngram to test
                wildcard: the wildcard to apply on ngram

            Returns:

                A list of ngrams that contains the given ngram with the wildcard

            Examples:
                
                ngrams.contains((u"test",u"un"),(0,-1))
                # list of 2-grams with first word equal to test
        """

        ng = len(ngram)-1

        wildcard = self.__wildcard(ng+1,wildcard)

        if (ngram,wildcard) not in self.__contains:
            self.__contains[(ngram,wildcard)] = search_ngram_range(ngram,self.__get_sorted_grams(ng,wildcard),wildcard=wildcard)

        i,j = self.__contains[(ngram,wildcard)]
        return self.__get_sorted_grams(ng,wildcard)[i:j]

    def __contains__(self,item):
        return self[item]>0

    def __iter__(self):
        return iter(self.getgrams(self.__max_arity))

    def getgrams(self,nt,wildcard=(0,0)):
        """
            Arguments:
                
                nt: order of gram, nt-gram
                wildcard: the wildcard to apply on ngrams to sort them (default (0,0))

            Returns:

                A sorted list of nt-grams sorted based on the wildcard

            Examples:
                
                ngrams.getgrams(2,(1,0))
                # list of 2-grams sorted by the second word
        """

        wildcard = self.__wildcard(nt,wildcard)

        return self.__get_sorted_grams(nt-1,wildcard)

    def grams_with_count(self,n,c):
        """
            Arguments:
                
                n: order of gram, n-gram
                c: the count wanted

            Returns:

                A list of n-grams with count c

            Examples:
                
                ngrams.grams_with_count(2,1)
                # list of 2-grams with count 1
        """
 
        if (n,c) not in self.__gwc:
            self.__gwc[(n,c)] = filter(lambda a:self[a]==c,self.__get_sorted_grams(n-1,(0,n)))

        return self.__gwc[(n,c)]

    def n(self,order,c,plus=False):
        """
            Arguments:
                
                order: order of gram, n-gram
                c: the count wanted
                plus: c and + or only exact count (default False)

            Returns:

                The number of n-grams of count c (or c>)

            Examples:
                
                ngrams.n(2,1)
                # number of 2-grams with count 1

                ngrams.n(2,3,True)
                # number of 2-grams with count 3 or more
        """
 
        if c <= 0:
            return 0

        if (order,c,plus) not in self.__n:
            if plus:
                self.__n[(order,c,plus)] = self.__nlen[order-1] - self.n(order,c-1,True)
            else:
                self.__n[(order,c,plus)] = len(self.grams_with_count(order,c))

        return self.__n[(order,c,plus)] 

    def freq(self,ngram):
        """
            Arguments:
                
                ngram: 

            Returns:

                The frequency of the n-gram (c/csum(n))

            Examples:
                
                ngrams.freq((u"frequency",))
                # The frequency of the 1-gram "frequency"
        """
 
        order = len(ngram)
        return self[ngram]/float(self.csum(order))

    def csum(self,order,ngram=None,wildcard=(0,0)):
        """
            Arguments:
                
                order: the order of the n-grams (n)
                ngram: ngram that should be contained in the ngrams (default None)
                wildcard: the wildcard to apply on ngram if ngram!=None

            Returns:

                The sum over all counts of the n-grams of the given order (and 
                containing ngram if ngram!=None)

            Examples:
                
                ngrams.csum(1)
                # The sum over all counts of every 1-grams

                ngrams.csum(2,(u"me",u"too"),(1,0))
                # The sum over all counts of every 2-grams that has u"too" 
                # at position 1
        """

        if ngram:
            if wildcard[1] <= 0:
                wildcard = (wildcard[0],wildcard[1]+len(ngram))

            if (order,ngram,wildcard) not in self.__sum:
                self.__sum[(order,ngram,wildcard)] = sum([self[w] for w in self.contains(ngram,(0,-1))])

            return self.__sum[(order,ngram,wildcard)]

        if order not in self.__sum:
            self.__sum[order] = sum(self.counts(order))

        return self.__sum[order]

    def counts(self,ng):
        """
            Arguments:
                
                ng: the order of n-grams

            Returns:

                A list of the counts of the n-grams of order ng (ng-grams)

            Examples:
                
                ngrams.counts(1)
                # The counts of every 1-grams
        """

        return self.__ngrams[ng].values()

    def __delitem__(self, ngram):
        del self.__ngrams[len(ngram)-1][ngram]

    def __getitem__(self,ngram):
        if len(ngram)-1 > self.__max_arity:
            raise IndexError("gramm must have an arity equal or lower than %i : %i given" % (self.__max_arity,len(ngram)))

        if self.__ngrams[len(ngram)-1].get(ngram,0) >= self.__min_count:
            return self.__ngrams[len(ngram)-1].get(ngram,0)
        else:
            return 0

    def __test_file(self,file,mode):
        if isinstance(file,type("")):
            file = codecs.open(file,mode,"utf-8")
        
        return file

    def save(self,file):
        """
            Arguments:
                
                file: where to save (utf-8 encoding)

            Examples:
                
                ngrams.save("myfile")
        """

        file = self.__test_file(file,'w')
        n_word = len(self)

        buffer = ""

        sys.stderr.write("Saving the %i-grams...\n" % self.__max_arity)

        t = Timer(n_word,out=sys.stderr)
        t.start()
        for i in range(self.__max_arity):
            for word in self.__get_sorted_grams(i,(0,i+1)):
                buffer += "#".join(word)+"%"+str(self.__ngrams[i][word])+"\n"

                if len(buffer) > 1000:
                    file.write(buffer)
                    buffer = ""

                t.print_update(1)

        file.write(buffer)
        file.close()

    def load(self,file):
        """
            Arguments:
                
                file: file to build the n-grams

            Examples:
                
                ngrams.load("myfile")
        """

        file = self.__test_file(file,'r')
        self.__ngrams = []
        self.__sorted_grams = []
        lines = file.readlines()
        file.close()
        n_lines = len(lines)

        self.__len = 0
        self.__nlen = [0 for i in range(self.__max_arity)]

        sys.stderr.write("Loading the %i-grams...\n" % self.__max_arity)

        t = Timer(n_lines,out=sys.stderr)
        t.start()
        for line in lines:
            word, count = line.split("%")
            word = word.split("#")
            n_grams = len(word)-1

            if n_grams > self.__max_arity-1:
                break
        
            while len(self.__ngrams) <= n_grams:
                self.__ngrams.append({})
                self.__sorted_grams.append({(0,n_grams+1):[]})
                
            self.__ngrams[n_grams][tuple(word)] = int(count)
            self.__get_sorted_grams(n_grams,(0,n_grams+1)).append(tuple(word))
            
            t.print_update(1)

        self.__max_arity = len(self.__ngrams)

        # to calculate and store __len and __nlen
        len(self)

    def print_list(self):
        for i in range(self.__max_arity):
            for word in self.__get_sorted_grams(i,(0,i+1)):
                print "".join(word), self.__ngrams[i][word]

    def len(self,nt=1):
        """
            Arguments:
                
                nt: the order of n-grams (nt-grams)

            Returns:

                The number of nt-grams

            Examples:
                
                ngrams.len(2)
                # The number of 2-grams
        """

        return self.__nlen[nt-1]

    def __len__(self):
        if self.__len:
            return self.__len

        self.__nlen = [len(ngram.keys()) for ngram in self.__ngrams]
        self.__len = sum([len(ngram.keys()) for ngram in self.__ngrams])
        return self.__len

    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        str = ""
        for i, nlen in enumerate(self.__nlen):
            str += "%i-gramm : %i grams\n" % (i+1,nlen)
            str += "%i-gramm : %i grams\n" % (i+1,len(self.__get_sorted_grams(i,(0,i+1))))
        return str

if __name__=="__main__":
    ngram = nGrams(3)
    ngram.build([u"C'est un test bien simple",u"Ça ne fait pas beaucoup de mots","est ce bien?"])
    print ngram
    ngram.print_list()
    print "\n\n\n Save ngram"
    ngram.save("test_save")
    test = nGrams(3)
    test.load("test_save")
    print test
    test.print_list()

    a = sorted(["a","b","bcd","c","d","ab","ac","ad","abc","abd","adc","adcb","acd","abcd","abdc"])
    a = [tuple([i]) for i in a]
    i = search_range('ab',a)
    print i
    print a
    print a[i[0]:i[1]]

    print "\n\n"
    i = search_range('b',a)
    print a[i[0]:i[1]]
    print ngram.begins_with(('e',))

    print ngram.contains(("un","test","bien"),(2,3))
    print ngram.contains(("est","un","test"),(0,1))
    print ngram.contains(("C","est","un"),(1,2))
    print ngram.contains(("C","est","ce"),(1,3))
    print ngram.contains(("est","ce"),(0,-1))
    print "Should not resort 2: (0,1)"
    print ngram.contains(("est","ce"),(0,1))
    print ngram.grams_with_count(1,2)
