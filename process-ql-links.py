import pysolr
import json

def clean_title(title):
    title = title.lower()
    title = title.replace(',', '')
    title = title.replace('. ', ' ')
    return title

solr = pysolr.Solr('http://localhost:8983/solr/ukt', always_commit=False, timeout=10)
cache = {}
resolution = {}
with open('ql.txt', 'r', encoding='UTF-8') as file:
    while line := file.readline():
        line = line.rstrip()
        parts = line.split(',')
        path = ''
        for idx, part in enumerate(parts):
            part = part.strip()
            # print('\t', idx, part)
            if path == '':
                query = f'title_tt:"{part}"'
            else:
                query = f'title_tt:"{part}" AND path_tt:"{path}/*" AND level:{idx+1}'
            results = solr.search(query)
            hits = len(results)
            if hits == 0:
                print('line:', line)
                print(f'{idx}: "{part}" saw {hits} result(s) - query: {query}.')
            else:
                # if idx == 0:
                best_match = ''
                best_path = ''
                has_one_hit = True
                if hits > 1:
                    has_one_hit = False
                    # print(line)
                    # print(idx, part)
                    # print(f"{query} -> {hits} result(s).")
                found = False
                min = 1000
                type = ''
                if part == 'tit.xxvii familiae nobilium b':
                    debug = True
                else:
                    debug = False
                for doc_i, doc in enumerate(results):
                    if has_one_hit:
                        path = doc['path_ss'][0]
                        type = 'one hit'
                        if debug == True:
                            print(type)
                        found = True
                        break
                    else:
                        if found == False:
                            for title in doc['title_ss']:
                                title = clean_title(title)
                                if part == title:
                                    best_match = title
                                    best_path = doc['path_ss'][0]
                                    type = 'exact match'
                                    if debug == True:
                                        print(type)
                                    found = True
                                    break
                                else:
                                    d = abs(len(part) - len(title))
                                    if d < min:
                                        best_match = title
                                        best_path = doc['path_ss'][0]
                                        type = 'minimal match'
                                        if debug:
                                            print(type)
                                        min = d
                if found == True and best_path != '':
                    if type == 'exact match':
                        path = best_path
                    print(part, '~', best_match, '->', best_path, '--', type)
                
                    pass

                if not found:
                    print('min:', min, best_match)
        resolution[line] = path

with open('ql.json', 'w', encoding='UTF-8') as ql_file:
    ql_file.write(json.dumps(resolution, ensure_ascii=False))