from deepdoc.parser import RAGFlowPdfParser, PlainParser

import json
import os
pdf_parser = RAGFlowPdfParser()
repodir = '/root/ReviewAgent2/repodir/'
preprocessdir = '/root/ReviewAgent2/workdir/preprocess'
pdffilename = 'Furuhashi-2017-Priming with high and low respi.pdf'
pdf_file_path = os.path.join(repodir,pdffilename)
text_content, tables = pdf_parser(pdf_file_path, need_image=True, zoomin=3, return_html=False)
text_file_path = os.path.join(preprocessdir,pdffilename.replace('.pdf','.txt'))
table_file_path = os.path.join(preprocessdir,pdffilename.replace('.pdf','.json'))
with open(text_file_path, 'w') as f:
    f.write(text_content)
with open(table_file_path, 'w') as f:
    json.dump(tables, f, indent=4, ensure_ascii=False)
