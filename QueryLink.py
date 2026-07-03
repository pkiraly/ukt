import json
import re
import os
from collections import Counter

class QueryLink:
    """A simple example class"""
    content_paths = None
    field_to_solr = None
    contents = Counter()
    file_name = 'ql.txt'

    query_links = {
        'c':   re.compile(r'^\[Contents ([^\]]+)\]$'),
        'cf':  re.compile(r'^\[Contents ([^\]]+)\]\[Field ([^\]]+)\]$'),
        'cl':  re.compile(r'^\[Contents ([^\]]+)\]\[Level ([^\]]+)\]$'),
        'clf': re.compile(r'^\[Contents ([^\]]+)\]\[Level ([^\]]+)\]\[Field ([^\]]+)\]$'),
        'clt': re.compile(r'^\[Contents ([^\]]+)\]\[Level ([^\]]+)\] ([^\]]+)$'),
        'l':   re.compile(r'^\[Level ([^\]]+)\]$'),
        'lt':  re.compile(r'^\[Level ([^\]]+)\] ([^\]]+)$'),
        'f':   re.compile(r'^\[Field ([^\]]+)\]$'),
        'pht': re.compile(r'^\[Partition ([^\]]+)\] \[Headings ([^\]]+)\] ([^\]]+)$')
    }
    cs = ['c', 'cf', 'cl', 'clf', 'clt']

    def __init__(self, field_to_solr, do_reset=False):
        self.field_to_solr = field_to_solr
        self.read_ql()
        if do_reset:
            self.reset_file()

    def read_ql(self):
        with open('ql.json') as f:
            json_str = f.read()
            self.content_paths = json.loads(json_str)

    def parse_query_link_field(self, field_query):
        try:
            field, value = field_query.split(':', maxsplit=1)
            field = self.field_to_solr[field] + '_tt'
            value = self.parse_query_link_text(value)
            return f'{field}:"{value}"'
        except ValueError:
            print(f'ValueError row {len(field_query.split(':', maxsplit=2))} - {field_query}')
            return None

    def parse_query_link_level(self, level_query):
        if ':' in level_query:
            level, value = level_query.split(':', maxsplit=1)
            value = self.parse_query_link_text(value)
            if value == '':
                return None
            return f'title_tt:{value}'
        else:
            print('level_query:', level_query)
            return None

    def parse_query_link_text(self, value):
        value = value.strip()
        if value.startswith('""'):
            value = value[1:]
        if value.endswith('""'):
            value = value[:-1]
        return value

    def parse_query_link(self, link):
        # global content_paths

        found = False
        content = False
        path = None
        level = None
        field = None
        text = None
        for key, link_pattern in self.query_links.items():
            m = link_pattern.match(link)
            if m is not None:
                if key in self.cs:
                    content = m.group(1).strip()
                    if content is not None:
                        self.contents.update([content])
                        if (self.content_paths is not None) and (content in self.content_paths):
                            path = self.content_paths[content]
                found = key
                if key == 'cf':
                    field = m.group(2)
                elif key == 'cl':
                    level = m.group(2)
                elif key == 'clf':
                    level = m.group(2)
                    field = m.group(3)
                elif key == 'clt':
                    level = m.group(2)
                    text = m.group(3)
                elif key == 'l':
                    level = m.group(1)
                elif key == 'lt':
                    level = m.group(1)
                    text = m.group(2)
                elif key == 'f':
                    field = m.group(1)
                elif key == 'pht':
                    partition = m.group(1)
                    headings = m.group(2)
                    text = m.group(3)
                elif key == 'c':
                    pass
                else:
                    print('unhandled key:', key)
                break
    
        if not found:
            print(link)
        else:
            
            query = []
            if path is not None:
                query.append(f'path_tt:"{path}/*"')
            if field is not None:
                field = self.parse_query_link_field(field)
                if field is not None:
                    query.append(field)
            if level is not None:
                level = self.parse_query_link_level(level)
                if level is not None:
                    query.append(level)
            if text is not None:
                text = self.parse_query_link_text(text)
                if (text is not None) and (text != ''):
                    query.append(text)

            query_string = ' AND '.join(query)

            return query_string
        return None

    def reset_file(self):
        print(f'reset_file')
        if os.path.exists(self.file_name):
            os.remove(self.file_name)

    def save_contents(self):
        print(f'save_contents {len(self.contents)}')
        with open(self.file_name, 'a', encoding='UTF-8') as ql_file:
            for key in self.contents.keys():
                if key:
                    ql_file.write(key + '\n')
