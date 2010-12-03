'''
Created on Dec 3, 2010

@author: leifj
'''

def hexify(s):
    r = ''
    for n in range(0, len(s)):
        r += '%02x' % ord(s[n])
    return r