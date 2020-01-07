import sys
import json

def main(arg):
    with open(arg) as f:
        g = json.load(fp=f)
    for k in g:
        print(k)
        for r in g[k]:
            print('   ', str(r))

if __name__ == '__main__':
    main(sys.argv[1])
