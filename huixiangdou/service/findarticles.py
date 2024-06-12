# yyj
import requests
import xml.etree.ElementTree as ET
import os 
from tqdm import tqdm
import json
import shutil
from loguru import logger
from lxml import etree
import requests
from bs4 import BeautifulSoup
import os

def download_pdfs(path, doi_list): #fox dalao contribution https://github.com/BigWhiteFox
    # 确保下载目录存在
    if not os.path.exists(path):
        os.makedirs(path)
    if isinstance(doi_list, str):
        doi_list = [doi_list]
    href_list = []

    for doi in doi_list:
        url = f"https://sci-hub.se/{doi}"
        response = requests.get(url)

        # 检查请求是否成功
        if response.status_code == 200:
            print(f"成功请求：{url}")
        else:
            print(f"请求失败：{url}，状态码：{response.status_code}")
            continue  # 如果请求失败，跳过本次循环

        soup = BeautifulSoup(response.text, 'html.parser')
        buttons = soup.find_all('button', onclick=True)

        for button in buttons:
            onclick = button.get('onclick')
            if onclick:
                pdf_url = onclick.split("'")[1]
                href_list.append((pdf_url, doi))
                print("pdf_url:", pdf_url)
        print("href_list:", href_list)

    # 遍历href_list中的每个URL
    for href, doi in href_list:
        pdf_url = f"https:{href}"
        try:
            response = requests.get(pdf_url, stream=True)
            if response.status_code == 200:
                filename = doi.replace("/", "_") + ".pdf"
                file_path = os.path.join(path, filename)
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"File downloaded and saved as: {file_path}")
            else:
                print(f"Download failed, Status Code: {response.status_code}, URL: {pdf_url}")
        except requests.RequestException as e:
            print(f"Failed to download due to an exception: {e}")


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
        try:
            pmids = [id_element.text for id_element in idlist.findall('.//Id')]
        except:
            pmids = []

        print(f"Found {len(pmids)} articles for keywords {self.keywords}.")
        self.search_pmid = pmids
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
        self.pmc_success = 0
        self.scihub_success = 0
        self.failed_download = []
        downloaded = os.listdir(self.repo_dir)
        for id in tqdm(self.pmc_ids, desc="Fetching full texts", unit="article"):
            # check if file already downloaded
            if f"{id}.txt" in downloaded:
                print(f"File already downloaded: {id}")
                self.pmc_success += 1
                continue
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
                self.failed_download.append(id)
                continue
            else:
                logger.info(full_text[:200])
                with open(os.path.join(self.repo_dir,f'{id}.txt'), 'w') as f:
                    f.write(full_text)
                self.pmc_success += 1
        for doi in tqdm(self.scihub_doi, desc="Fetching full texts", unit="article"):
            # check if file already downloaded
            if f"{doi.replace('/','_')}.pdf" in downloaded: 
                print(f"File already downloaded: {doi}")
                self.scihub_success += 1
                continue

            if download_pdfs(path=self.repo_dir,doi_list = doi):
                self.scihub_success += 1
            else:
                self.failed_download.append(doi)

    def save_config(self):
        config = {
            'repo_dir': self.repo_dir,
            'keywords': self.keywords,
            'retmax': self.retmax,
            "search_pmids": self.search_pmid,
            'import_pmids': [id for id in self.pmids if id not in self.search_pmid],
            'failed_pmids': self.failed_pmids,
            'result': [
                {
                    'pmid': r[0],
                    'pmcid': r[1],
                    'doi': r[2]
                } for r in self.esummary
            ],
            "pmc_success_d": self.pmc_success,
            "scihub_success_d": self.scihub_success,
            "failed_download": self.failed_download,
            
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
34536239
7760895
36109602
24766875"""
    string = [k.strip() for k in strings.split('\n')]

    pmids = [k for k in string if k.isdigit()]
    print(pmids)
    keys = [k for k in string if not k.isdigit() and k != '']
    print(keys)
    articelfinder = ArticleRetrieval(keywords = keys,pmids = pmids,
                                     repo_dir = 'repodir',retmax = 5)
    articelfinder.initiallize()
