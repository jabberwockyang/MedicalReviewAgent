# yyj
import requests
import xml.etree.ElementTree as ET
import os 
from tqdm import tqdm
import json
import shutil
from loguru import logger
from lxml import etree
import sys
from scihub_cn.scihub import main

def scihub_download(doi_file_Path = None,doi = None,output_dir = None):
    args = ["scihub-cn"]  # This is the program name as expected in argv[0]
    if doi is not None:
        args.extend(["-d", doi])
    if doi_file_Path is not None:
        args.extend(["-i", doi_file_Path, "--doi"])
    if output_dir is not None:
        args.extend(["-o", output_dir])
    sys.argv = args  # Set sys.argv to our simulated command line arguments
    sys.exit(main())


class ArticleRetrieval:
    def __init__(self,
                    keywords: list = [],
                    pmids: list = [],
                    repo_dir = 'repodir',
                    retmax = 500):
        if keywords is [] and pmids is []:
            raise ValueError("Either keywords or pmids must be provided.")
        
        self.keywords = keywords
        self.pmids = pmids
        self.repo_dir = repo_dir
        self.retmax = retmax
        self.pmc_ids = []


    def esummary_pmc(self):
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?"
        params = {
            "db": "pubmed",
            "id": ','.join(self.pmids),
            # "retmax": self.retmax
        }
        response = requests.get(base_url, params=params)
        root = ET.fromstring(response.content)
        results = []
        for docsum in root.findall('DocSum'):
            pmcid = None
            doi = None
            id_value = docsum.find('Id').text
            for item in docsum.findall('.//Item[@Name="doi"]'):
                doi = item.text
                break
            for item in docsum.findall('.//Item[@Name="pmc"]'):
                pmcid = item.text
                break

            results.append((id_value, pmcid, doi))
        
        logger.info(f"total {len(results)} articles:")
        logger.info(f"found {len([r for r in results if r[1] is not None])} articles with PMC ID.")
        logger.info(f"found {len([r for r in results if r[2] is not None])} articles with DOI.")
        logger.info(f"found {len([r for r in results if r[1] is None and r[2] is None])} articles without PMC ID and DOI.")
                
        self.esummary = results
        self.pmc_ids = [r[1] for r in results if r[1] is not None]
        self.scihub_doi = [r[2] for r in results if r[1] is None and r[2] is not None]
        self.failed_pmids = [r[0] for r in results if r[1] is None and r[2] is None]
       
    ## 通过Pubmed数据库检索文章
    def esearch_pmc(self):

        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": '+'.join(self.keywords),
            "retmax": self.retmax
        }
        response = requests.get(base_url, params=params)
        root = ET.fromstring(response.content)
        idlist = root.find('.//IdList') 
        pmids = [id_element.text for id_element in idlist.findall('.//Id')]
        print(f"Found {len(pmids)} articles for keywords {self.keywords}.")
        self.pmids.extend(pmids)
        

    # 解析XML文件
    def _get_all_text(self, element):
        """递归获取XML元素及其所有子元素的文本内容。确保element不为None."""
        if element is None:
            return ""
        
        text = element.text or ""
        for child in element:
            text += self._get_all_text(child)
            if child is not None and child.tail:
                text += child.tail
        return text

    ## 清洗XML文件
    def _clean_xml(self,txt):
        parser = etree.XMLParser(recover=True)
        root = ET.fromstring(txt,parser=parser)
        txt = self._get_all_text(root)
        txt = txt.split('REFERENCES')[0]  # 截取参考文献之前的文本
        text = '\n\n'.join([t.strip() for t in txt.split('\n') if len(t.strip())>250])
        return text

    ## 通过PMC数据库获取全文
    def fetch_full_text(self):
        if not os.path.exists(self.repo_dir):
            os.makedirs(self.repo_dir)
        print(f"Saving articles to {self.repo_dir}.")
        self.success = 0
        for id in tqdm(self.pmc_ids, desc="Fetching full texts", unit="article"):
            base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            params = {
                "db": "pmc",
                "id": id,
                "rettype": "xml",
                "retmode": "text"
            }
            response = requests.get(base_url, params=params)
            full_text = self._clean_xml(response.text)
            if full_text.strip() == '':
                continue
            else:
                logger.info(full_text[:500])
                with open(os.path.join(self.repo_dir,f'{id}.txt'), 'w') as f:
                    f.write(full_text)
                self.success += 1
        for doi in tqdm(self.scihub_doi, desc="Fetching full texts", unit="article"):
            scihub_download(doi = doi,output_dir=self.repo_dir)
            self.success += 1

    def save_config(self):
        config = {
            'keywords': self.keywords,
            'repo_dir': self.repo_dir,
            'result': [
                {
                    'pmid': r[0],
                    'pmcid': r[1],
                    'doi': r[2]
                } for r in self.esummary
            ],
            'len': self.success,
            'retmax': self.retmax,
            'failed_pmids': self.failed_pmids
        }
        with open(os.path.join(self.repo_dir, 'info.json'), 'w') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    def initiallize(self):
        if self.keywords !=[]:
            print(self.keywords)
            self.esearch_pmc() # get pmids from pubmed database using keywords

        self.esummary_pmc() # get pmc ids from pubmed database using pmids
        self.fetch_full_text() # get full text from pmc database using pmc ids
        self.save_config() # save config file

if __name__ == '__main__':
    if os.path.exists('repodir'):
        shutil.rmtree('repodir')
    
    strings = """
36944324
38453907
38300432
38651453
38398096
38255885
38035547
38734498"""
    string = [k.strip() for k in strings.split('\n')]

    pmids = [k for k in string if k.isdigit()]
    print(pmids)
    keys = [k for k in string if not k.isdigit() and k != '']
    print(keys)
    articelfinder = ArticleRetrieval(keywords = keys,pmids = pmids,
                                     repo_dir = 'repodir',retmax = 5)
    articelfinder.initiallize()
