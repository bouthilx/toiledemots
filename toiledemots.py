#!/usr/bin/env python

from toiledemots import pipe

def main():
    lines = pipe.fetch_text_lines("data/train.fr")
    print lines[0], lines[-1]

if __name__ == "__main__":
   main() 
