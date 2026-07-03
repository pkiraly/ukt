# process UKT FFF file
# Folio Reference (The Unofficial Folio Wiki): http://folio.wikidot.com/
import sys
import re
import pysolr
from argparse import ArgumentParser
import json
import os
from collections import Counter
import urllib.parse
from QueryLink import QueryLink


parser = ArgumentParser()
parser.add_argument("-f", "--filename", dest="filename", help="the file to process")
parser.add_argument("-t", "--target", dest="target", help="the target file")
parser.add_argument("-a", "--json-file", dest="json_file", help="the JSON file for debugging (default is <FILENAME>.json))")
parser.add_argument("-s", "--solr-index", default="ukt", dest="solr_index", help="the solr index")
parser.add_argument("-d", "--debug", dest="debug", help="debug content into a JSON file", action='store_true')
parser.add_argument("-x", "--delete-records", dest="delete_records", help="delete records before indexing", action='store_true')

args = parser.parse_args()
if args.debug:
    if args.json_file:
        json_file = args.json_file
    else:
        json_file = re.sub(r'FFF$', 'json', args.filename)

print(json_file)

solr = pysolr.Solr('http://localhost:8983/solr/' + args.solr_index, always_commit=False, timeout=10)

if args.delete_records:
    solr.delete(q='*:*')
    record_id = 0
else:
    res = solr.search('*:*', **{'fl': 'id_i', 'rows': 1, 'sort': 'id_i desc'})
    record_id = res.docs[0]['id_i']

print(record_id)

header = re.compile(r'^<RD:"H(\d)"(,CH)?>')
rd = re.compile(r'^<RD(:(Leiras|"S1"|"S2"|"S3"|"S4"))?(,CH)?>')
field_items = [
    '<FD:"(01Azonosito)">(.*?)</FD:"01Azonosito">',
    '<FD:"(01Azonosito_sorszam)">(.*?)</FD:"01Azonosito_sorszam">',
    '<FD:"(02Szerzo)">(.*?)</FD:"02Szerzo">',
    '<FD:"(03Cim)">(.*?)</FD:"03Cim">',
    '<FD:"(04Hely)">(.*?)</FD:"04Hely">',
    '<FD:"(05Ido)">(.*?)</FD:"05Ido">',
    '<FD:"(06Nyelv)">(.*?)</FD:"06Nyelv">',
    '<FD:"(07Jelleg)">(.*?)</FD:"07Jelleg">',
    '<FD:"(08Terjedelem)">(.*?)</FD:"08Terjedelem">',
    '<FD:"(09Meret)">(.*?)</FD:"09Meret">',
    '<FD:"(10Birtokos)">(.*?)</FD:"10Birtokos">',
    '<FD:"(11Allapot)">(.*?)</FD:"11Allapot">',
    '<FD:"(12Targyszo)">(.*?)</FD:"12Targyszo">',
    
    '<FD:"(13Tartalom)">(.*?)</FD:"13Tartalom">',
    '<FD:"(14Tartalom)">(.*?)</FD:"14Tartalom">',
    '<FD:"(14Facsimile)">(.*?)</FD:"14Facsimile">',
    '<FD:"(14Oldal)">(.*?)</FD:"14Oldal">',
    '<FD:"(15Oldal)">(.*?)</FD:"15Oldal">',
    '<FD:"(15Megjegyzes)">(.*?)</FD:"15Megjegyzes">',
    '<FD:"(20Scriptor)">(.*?)</FD:"20Scriptor">',
    '<FD:"(21Illum)">(.*?)</FD:"21Illum">',
    '<FD:"(22Cimer)">(.*?)</FD:"22Cimer">',
    '<FD:"(23Kotes)">(.*?)</FD:"23Kotes">',
    '<FD:"(24Bibliogr)">(.*?)</FD:"24Bibliogr">',
    '<FD:"(25Mikrofilm)">(.*?)</FD:"25Mikrofilm">',
    '<FD:"(27Adat)">(.*?)</FD:"27Adat">',
    '<FD:"(28Iras)">(.*?)</FD:"28Iras">',
    '<FD:"(29Bejegyzes)">(.*?)</FD:"29Bejegyzes">',
    '<FD:"(30Olim)">(.*?)</FD:"30Olim">',
    
    '<FD:"(T01xIncipit)">(.*?)</FD:"T01xIncipit">',
    '<FD:"(T01xExplicit)">(.*?)</FD:"T01xExplicit">',
    '<FD:"(T01xNev)">(.*?)</FD:"T01xNev">',
    '<FD:"(T02xrovidites)">(.*?)</FD:"T02xrovidites">',
    '<FD:(xErrata)>(.*?)</FD:xErrata>',

    '<<(kép)>(.*?)<</kép>',
    '<(BH)>(.*?)<EH>', 
]

tag_pattern = re.compile(r'<(/?FD:.+?)>')


field_to_solr = {
    '01Azonosito': 'identifier',
    '01Azonosito_sorszam': 'identifier2',
    '02Szerzo': 'author',
    '03Cim': 'title',
    '04Hely': 'place',
    '05Ido': 'date',
    '06Nyelv': 'language',
    '07Jelleg': 'feature',
    '08Terjedelem': 'extent',
    '09Meret': 'size',
    '10Birtokos': 'possessor',
    '11Allapot': 'state',
    '12Targyszo': 'keyword',
    '13Tartalom': 'toc',
    '14Tartalom': 'toc',
    '14Facsimile': 'facsimile',
    '14Oldal': 'pages',
    '15Oldal': 'pages',
    '15Megjegyzes': 'note',
    '20Scriptor': 'scriptor',
    '21Illum': 'illumination',
    '22Cimer': 'coatofarms',
    '23Kotes': 'binding',
    '24Bibliogr': 'bibliography',
    '25Mikrofilm': 'microfilm',
    '27Adat': 'data',
    '28Iras': 'script',
    '29Bejegyzes': 'annotation',
    '30Olim': 'olim',
    'T01xIncipit': 'incipit',
    'T01xExplicit': 'explicit',
    'T01xNev': 'person',
    'T02xrovidites': 'abbreviation',
    'xErrata': 'errata',
    'kép': 'caption',

    'BH': 'title',
}

removeable_items = [
    '<PT:6>', '<PT:7>', '<PT:8>', '<PT:9>', '<PT:10>', '<PT:11>', '<PT:12>', '<PT>', 
    r'<KN\+>', '<BP:9p>',
    '<PS:torzs>', '<PS:vers>', '<PS:Leiras>', '<PS:Normal>', '<PS:"sorkoz_elotte">',
        '<PS:"bal_margo">', '<PS:"sorkoz_elotte_utanna">', '<PS:"besch2a">', '<PS:"sorkoz_utanna">',
        '<PS:"normal_bekezdes">', '<PS:kozepre>', '<PS:init>', '<PS:"Szövegtörzs">', '<PS:"besch2">',
        '<PS:"besch1">', '<PS:"leiras_biblhung3">', '<PS:esztKategoriak>', '<PS:"Lábjegyzetszöveg">',
        r'<PS:(fejresz|Birtokos|Formatum|cimke)>', r'<PS:"(fuggo-dupla)">',
    r'<JD:"patak-\d+">', r'<JD:"raday-\d+">', r'<JD:"pannonhalma-\d+[abc]?">', r'<JD:"CL-?\d+">',
      r'<JD:"CL-\d+-\d+">', r'<JD:"CL-MNY\. \d+">', r'<JD:"DH\d+">', r'<JD:"DH\d+-\d+">', 
      r'<JD:"OH\d+">', r'<JD:"FH\d+">', r'<JD:"FH\d+-\d+">',
      r'<JD:"QH\d+">', r'<JD:"QH\d+-\d+\.?">',
    '<JU:RT>', '<JU:CN>', '<JU:FL>', '<JU:LF>',
    '<FC:DC>', '<FC>', '<BC:DC>', '<BC>', '<FC:128,0,0>',
    # r'<IT\+>', '<IT>', 
    '<IT->', r'<BD\+>', '<BD->', '<BD>',
    '<PB>',
    '<FD:fieldname>', '</FD:fieldname>',
    # '<HR>',
    '<BK:"[^"]+">',
    '<IN:FI:0>', '<IN:FI:9.95p>', '<IN:LF:11.2p,FI:0>', '<IN:FI:9p>', '<IN:[^>]+>',
    '<OB:FO:[^>]+>',
    # jump destination
    '<JD:"csapodi_budai_pic[1234]">', '<JD:"vizkelety_mittelalterliche_iii_pic26">',
    '<JD:"vizkelety_mittelalterliche_.*?">',
    # TODO: char replace
    '<FT:"Times New Roman CE",SR>', '<FT:"Times New Roman",SR>', '<FT:"Times New Roman,SR">',
      '<FT:"Times New Roman">', '<FT:Symbol,SR,SY>', '<FT:Arial,SN>', '<FT:Symbol>', '<FT>', 
    '<TS:[^>]+>', 
    # tables
    # '<TA:[^>]+>', '<RO>',
    # '<CE: BR:AL:0,0>', '<CE>', '<CE: VA:BO>', '<CE:[^>]+>', '</CE>', '</TA>'
]

table_items = {
    re.compile(r'<TA:[^>]+>'):           '<table>',
    re.compile('</TA>'):                 '</table>',
    re.compile(r'<CE[^>]*>'):            '<td>',
    re.compile('</CE>'):                r'</td>',
    re.compile(r'<RO>(.*)(</table>)$'): r'<tr>\1</td></tr>\2',
    re.compile(r'<RO>(.*)$'):           r'<tr>\1</tr>',
    re.compile(r'<IT\+>(.*?)<IT>'):     r'<em>\1</em>',
}

query_items = [
    r'<(QL):Query,"(.*?)">(.*?)<EL>',
    r'<(PL):Program,"aaview32 (.*?)">(.*?)<EL>',
    r'<(JL):Jump,"(.*?)">(.*?)<EL>',
    r'<(SP):([356]p)>(.*?)</SS>',
    r'<(SB):([23]p)>(.*?)</SS>',
]

single_query_items = [
    r'<CS:Felsoindex>(.*?)</CS>',
    r'<CS:Alsoindex>(.*?)</CS>',
    r'<CS:Lábjegyzet-hivatkozás>(.*?)</CS>',
    r'<CS:"Lábjegyzet-hivatkozás">(.*?)</CS>',
]

popup = re.compile(r'<PW:Popup[^>]+>(.*?)<LT>(.*?)<EL>')
repeated_fields = re.compile(r'<(f:[^<>]+)><\1>(.*?)</\1></\1>')


content_paths = None

tokenized_fields = list(field_to_solr.values())
tokenized_fields.append('path')

def compile_regexes(items):
    regexes = []
    for item in items:
        regexes.append(re.compile(item))

    return regexes

def handle_data(data, path, level=None):
    save_data(data, path)
    return create_data(level)

def get_path(path):
    return ('/').join(path)

def save_data(data, path):
    # pass
    # print(data)
    if len(data) > 0:
        data['path_ss'] = get_path(path)
        # tokenized_fields = ['path', 'title', 'identifier', 'identifier2']
        for tf in tokenized_fields:
            ss = tf + '_ss'
            tt = tf + '_tt'
            if ss in data:
                data[tt] = data[ss]

        if 'level' in data:
            if len(path) > 1:
                data['parent_ss'] = get_path(path[:-1])
            else:
                data['parent_ss'] = 'ukt'

        for key in data.keys():
            if isinstance(data[key], set):
                data[key] = list(data[key])

        if args.debug:
            with open(json_file, "a") as myfile:
                myfile.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

        solr.add(data)

def create_data(level = None):
    global record_id
    if record_id % 10000 == 0:
        print(record_id)
    record_id += 1
    data = {
        'id': record_id,
        'id_i': record_id,
        'lines': [],
    }
    if level is not None:
        data['level'] = level
    return data

def clean_value(value):
    value = re.sub('<[^>]+>', ' ', value)
    value = re.sub(r'\s+', ' ', value)
    value = value.strip()
    return value

def fix_tags(text, linenr):
    tags = tag_pattern.findall(text)
    c = {}
    for tag in tags:
        if tag[0:1] == '/':
            tag = tag[1:] 
            if tag in c:
                c[tag] -= 1
            else:
                print(f'{linenr}) error: unknown open {tag}')
        else:
            if tag in c:
                c[tag] += 1
            else:
                c[tag] = 1

    for tag, count in c.items():
        if count > 0:
            # print(f"{linenr}) {count} open '{tag}' tag")
            text += '</' + tag + '>'
        if count < 0:
            print(f"{linenr}) {abs(count)} unnecessary closed '{tag}' tag")

    return text

def main():
    if args.debug:
        if os.path.exists(json_file):
            os.remove(json_file)

    removeables = compile_regexes(removeable_items)
    fields = compile_regexes(field_items)
    queries = compile_regexes(query_items)
    single_queries = compile_regexes(single_query_items)
    error_count = 0
    ql = QueryLink(field_to_solr, args.delete_records)
    # content_paths = read_ql()
    # print(content_paths)

    # print(args)
    with open(args.filename, 'r', encoding='UTF-8') as file:
        old_level = None
        data = {}
        path = []
        linenr = 0
        while line := file.readline():
            linenr += 1
            line = line.rstrip()
            in_level = False
            m = header.match(line)
            # print(m)
            if m is not None:
                level = int(m.group(1))
                data = handle_data(data, path, level)
                # print(f'<head level={level}>')
                if (old_level is None) or (level == old_level + 1):
                    path.append(str(record_id))
                    # print(get_path(path))
                    # pass
                elif level == old_level:
                    path.pop()
                    path.append(str(record_id))
                    # print(get_path(path))
                    # pass
                elif level < old_level:
                    # print('unhandled:', level, '<', old_level)
                    # print('before', get_path(path))
                    i = level
                    while i < old_level:
                        path.pop()
                        i += 1
                    path.pop()
                    path.append(str(record_id))
                    # print('after', get_path(path))
                    pass
                else:
                    print(f'at line {linenr}) level: {level}, old_level: {old_level}')
                    # print(line)
                old_level = level
                line = re.sub(r"^<RD[^>]*>", "", line)
                atr = m.group(2)
            else:
                m = rd.match(line)
                if m is not None:
                    data = handle_data(data, path)
                    line = re.sub(r"^<RD[^>]*>", "", line)

            for regex in removeables:
                line = regex.sub("", line)

            for re_from, to in table_items.items():
                line = re_from.sub(to, line)

            line = fix_tags(line, linenr)

            for field in fields:
                # print('check', field)
                m = field.search(line)
                while m is not None:
                    dc_field = field_to_solr[m.group(1)]
                    solr_key = dc_field + '_ss'
                    if solr_key not in data:
                        data[solr_key] = set()
                    data[solr_key].add(clean_value(m.group(2)))
                    line = field.sub('<f:' + dc_field + '>' + r'\2' + '</f:' + dc_field + '>', line, 1)
                    m = field.search(line)
                    # print('#', line)

            line = re.sub(r'<LT>\*</CS><EL>', '</CS><LT>*<EL>', line)
            line = repeated_fields.sub(r'<\1>\2</\1>', line)

            for query in queries:
                m = query.search(line)
                if m is not None:
                    if m.group(1) == 'QL':
                        solr_query = ql.parse_query_link(m.group(2))
                        if solr_query:
                            solr_query = urllib.parse.quote_plus(solr_query)
                            line = query.sub(f'<a href="?tab=data&query={solr_query}">' + r'\3' + '</a>', line)
                line = query.sub(r'\3', line)

            for query in single_queries:
                m = query.search(line)
                while m is not None:
                    # print('query', query)
                    # print('match', m)
                    # print('group 1', m.group(1))
                    line = query.sub(r'\1', line)
                    m = query.search(line)

            line = popup.sub(r'<note ref="\2">\1</note>', line)

            line = re.sub('<TB>', '   ', line)
            line = re.sub('<(CR|HR)>', '<br>', line)
            line = re.sub(r'\s+', ' ', line)
            line = re.sub(r'<<([^<>]+)>', r'〈\1〉', line)


            if 'level' in data and 'title_ss' not in data:
                data['title_ss'] = [clean_value(line)]
            
            data['lines'].append(line)

            m = re.search(r'(<[A-Z][^>]+>)', line)
            if m:
                error_count += 1
                # pass
                if m.group(1) != '<FD:"13Tartalom">':
                    print(f'line nr {linenr}) {m.group(1)}')
                # print('>', line)

                # if atr is not None:
    print(f'{error_count} lines has code')
    handle_data(data, path)
    solr.commit()
    ql.save_contents()
    print('DONE')


if __name__ == '__main__':
    sys.exit(main())
