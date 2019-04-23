import unicodedata

def map_char(ch):
    try:
        name = unicodedata.name(ch)
    except:
        return ch
    if name.startswith("LATIN SMALL LETTER"):
        return name.split(" ")[3].lower()
    elif name.startswith("LATIN CAPITAL LETTER"):
        return name.split(" ")[3].upper()
    return ch
    
def latin2ascii(string):
    result = ""
    for ch in string:
        result += map_char(ch)
    return result
    
if __name__ == "__main__":
    print(latin2ascii("furtwangler"))
    print(latin2ascii("furtwängler"))
    print(latin2ascii("furtwængler"))
    print(latin2ascii("FURTWÄNGLER"))
    
    
    
    
    

