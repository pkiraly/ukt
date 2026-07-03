#!/usr/bin/env bash

python fff2xml.py --filename ukt_v15.FFF --delete-records --debug --solr-index ukt
python fff2xml.py --filename Kezirattar.FFF --debug --solr-index ukt
python process-ql-links.py