import os, string

grf_strings = {}

def read_lang_files():
    for filename in os.listdir("lang/"):
        lang = -1
        for line in open("lang/" + filename):
            if len(line) <= 1 or line[0] == "#":
                pass
            elif line[:6] == "lang: ":
                assert lang == -1, "Only one 'lang:' line allowed per language file"
                lang = int(line[6:8], 16)
            else:
                assert lang != -1, "Language id not set"
                i = string.index(line, ':')
                name = line[:i].strip()
                value = line[i+1:-1]
                if not name in grf_strings:
                    grf_strings[name] = []
                grf_strings[name].append({'lang': lang, 'text': value})
