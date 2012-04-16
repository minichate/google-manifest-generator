# vim: ts=4 sw=4 et:

"""Library of some simple string and network related utilities. Initially
authored by Don Arscott."""

def StringAdd( instr, inc ):
    """ Will increment the right most chars of string instr by inc. Will rollover to left, and  stop incrementing when first non aplhanumeric char reached. Will not increase the length of the string, so rollover may occur.
    Example 
    "aaa" + 1 = "aab"
    "aaa" + 26 = "aba"  
    "aaa" + 27 = "abb"  
    "aa a" + "53" = "aa b"  - stoped incrementing at the space char
    """
    i = len(instr)-1

    inc = int(inc)

    # is string empty?
    if i < 0:
        return instr
    last = instr[i]

    str = instr[:-1]   # remove last char
    #print "begin instr=%s str=%s  last char=%s=%d" %( instr, str, last, ord(last))

    hi=0
    lo=0
    radix=0

    if last.isalnum():
        if last.isdigit():
            hi=ord('9')
            lo=ord('0')
            radix=10
        elif last.islower():
            hi=ord('z')
            lo=ord('a')
            radix=26
        elif last.isupper:
            hi=ord('Z')
            lo=ord('A')
            radix=26
        else:
            return  str + last   # return origional string unchanged
    else:
        return  str + last   # return origional string unchanged


    newlast = ord(last[0]) + inc
    while newlast > hi:
        #rollover
        str = StringAdd( str, '1')
        #print "x str=%s newlast=%d radix=%d" % (str, newlast, radix)
        newlast -= radix

    return str + chr(newlast)




def IpAddrAdd( ip, inc=1):
    """Function to increment an IP address.

    Examples:

    >>> IpAddrAdd('1.1.1.1',1)
    '1.1.1.2'
    >>> IpAddrAdd('1.1.1.255',1)
    '1.1.2.0'
    >>> IpAddrAdd('1.1.1.1',256)
    '1.1.2.1'
    >>> IpAddrAdd('1.1.1.1',512)
    '1.1.3.1'
    >>> IpAddrAdd('1.1.1.1',65536)
    '1.2.1.1'
    >>> 256*256*256
    16777216
    >>> IpAddrAdd('1.1.1.1',16777216)
    '2.1.1.1'
    """
    #print "Entering IpAddrAdd: ip=%s inc=%s" %( ip, inc)

    if (not ip) or (not inc):
        return ip

    inc = int(inc)

    octets = ip.split('.')  # list of octets
    if (len(octets) > 4) or (len(octets) == 0):
        return ip

    lso = len(octets) - 1   # index of right most octet
    last = octets[lso]      # least significant octet
    shortip = octets[:-1]   # remove last octet from list

    newlast = inc + int(last)

    shortip = ".".join(shortip)     # list to string

    while newlast > 255:
        # octet rollover
        # with right most octet removed, incremant remaing ip string by 1
        shortip = IpAddrAdd( shortip, 1)    # carry the 1
        #print "octet rollover last=%s newlast=%s shortip=%s" % (last,newlast,shortip)
        newlast -= 256

    if shortip:
        shortip  += '.' + str(newlast) 
    else:
        shortip = str(newlast)

    return shortip

def IPquadToAddr(icp_ip):
    """convert ip address to 32 bit integer"""
    octets = icp_ip.split('.')
    return (int(octets[0]) << 24) + (int(octets[1]) << 16) + (int(octets[2]) << 8) + int(octets[3])


def try_int(s):
    "Convert to integer if possible."
    try: return int(s)
    except: return s

def natsort_key(s):
    "Used internally to get a tuple by which s is sorted."
    import re
    return map(try_int, re.findall(r'(\d+|\D+)', s))

def natcmp(a, b):
    "Natural string comparison, case sensitive."
    return cmp(natsort_key(a), natsort_key(b))

def natcasecmp(a, b):
    "Natural string comparison, ignores case."
    return natcmp(a.lower(), b.lower())

def natsort(seq, cmp=natcmp):
    "In-place natural string sort."
    seq.sort(cmp)


# ---------------------------------------------------------
# Natural string sorting.   from http://code.activestate.com/recipes/285264/
# Sorts strings in a way that seems natural to humans. If the strings contain integers, then the integers are ordered numerically. 
# For example, sorts ['Team 11', 'Team 3', 'Team 1'] into the order ['Team 1', 'Team 3', 'Team 11'].
# ---------------------------------------------------------
def natsorted(seq, cmp=natcmp):
    "Returns a copy of seq, sorted by natural string sort."
    import copy
    temp = copy.copy(seq)
    natsort(temp, cmp)
    return temp

