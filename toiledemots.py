#!/usr/bin/env python

from toiledemots import pipe
from toiledemots.toile import Toile

def main():
    lines = pipe.fetch_text_lines("data/train.fr")
    print lines[0], lines[-1]
    toile = Toile(min_count=0)
    toile.build(lines[:10000])
    
    closests = toile.get_closests(u"ciel")

    print closests[:20]

if __name__ == "__main__":
   main() 
