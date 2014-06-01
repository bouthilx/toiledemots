#!/bin/python
# -*- coding: utf-8 -*-

import time
import os
import ctypes

__all__ = ['Cache']

class Cache(dict):
    """
        Cached dictionnary

        Arguments: 

            max: maximum size of the cache
            **d: dictionnary items

        Works like a dictionnary but with a maximum size.

        When there is more items than the maximum size, the ones accessed more lately are 
        deleted to make space for a new item

        Examples:

            cache = Cache(10,some="items",in="the",dict="ionnary")
            cache["new"] = "items"
            
            cache.get("get","if not in")
            cache["getitem"]
    """
    def __init__(self,max,**d):
        """
            Arguments:

                max: maximum size of the cache 
                **d: dictionnary items

            Examples:
            
                cache = Cache(5)

                cache = Cache(5,the="items",are="optional")
        """
        self.start = time.time()
        self.max = max

        for key,item in d.items():
            self[key] = item

    def __setitem__(self,key,value):
        """
            Arguments:

                key: key to access the value later on (most be hashable)
                value: the value to store

            A time value is stored together with the key and the value 
            to evaluate if the tuple (key,value) should be keep when 
            the cache is full.
 
            Examples:

                cache = Cache(10)
                cache["key"]="value"
       """
        dict.__setitem__(self,key,(time.time()-self.start,value))

        if len(self)>self.max:

            for key, item in sorted(self.items(),key=lambda a:a[1][0])[:len(self)-self.max]:
                del self[key]
            
    def __getitem__(self,key):
        """
            Arguments:

                key: key to access the value

            The time value is updated in order to keep the tuple (key,value) 
            in the dict if it is accessed frequently enough while the 
            cache is full.
 
            Examples:

                cache = Cache(10,key="value")
                cache["key"]
       """
        item = dict.__getitem__(self,key)
        self[key] = item[1]
        return item[1]

    def get(self,key,ifnot=None):
        """
            Arguments:

                key: key to access the value
                ifnot: value to return if the key is not in the cache
                    (None by default)

            No exception are raised if the key is not in the cache.
            The ifnot value is returned when the key is not in the cache.
            The time value updated if the key was in the cache.

            Examples:

                cache = Cache(10,key="value")
                cache.get("nokey")==None
                cache.get("nokey","value")=="value"
       """
        item = dict.get(self,key,ifnot)

        if item!=ifnot:
            self[key] = item[1]
            return item[1]

        return ifnot

if __name__=="__main__":
    c = Cache(20)
    print c.get("test")
    c["test"]="value"
    print c.get("test")

    for i in range(40000):
        c[i] = i
        print c.get(5,None)
        print c.items()[0]
        print sorted(c.items(),key=lambda a:a[1][0])
        time.sleep(1.0)
