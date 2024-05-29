import requests
import xml.etree.ElementTree as ET
import os 
from tqdm import tqdm
import json
import shutil

class ArticleRetrieval:
    def __init__(self,
                    keywords: list,
                    repo_dir = 'repodir',
                    retmax = 500):
        self.keywords = keywords
        self.repo_dir = repo_dir
        self.retmax = retmax
        
    ## 通过PMC数据库检索文章
    def search_pmc(self):

        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "pmc",
            "term": '+'.join(self.keywords),
            "retmax": self.retmax
        }
        response = requests.get(base_url, params=params)
        root = ET.fromstring(response.content)
        pmc_ids = [id_element.text for id_element in root.findall('.//Id')]
        print(f"Found {len(pmc_ids)} articles.")
        self.pmc_ids = pmc_ids
        return pmc_ids

    # 解析XML文件
    def _get_all_text(self,element):
        """递归获取XML元素及其所有子元素的文本内容"""
        text = element.text or ""
        for child in element:
            text += self._get_all_text(child)
            if child.tail:
                text += child.tail
        return text

    ## 清洗XML文件
    def _clean_xml(self,txt):
        root = ET.fromstring(txt)
        txt = self._get_all_text(root)
        txt = txt.split('REFERENCES')[0]  # 截取参考文献之前的文本
        text = '\n\n'.join([t.strip() for t in txt.split('\n') if len(t.strip())>250])
        return text

    ## 通过PMC数据库获取全文
    def fetch_full_text(self):
        if not os.path.exists(self.repo_dir):
            os.makedirs(self.repo_dir)
        print(f"Saving articles to {self.repo_dir}.")
        
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
            with open(os.path.join(self.repo_dir,f'{id}.txt'), 'w') as f:
                f.write(full_text)

    def save_config(self):
        config = {
            'keywords': self.keywords,
            'repo_dir': self.repo_dir,
            'pmc_ids': self.pmc_ids,
            'len': len(self.pmc_ids),
            'retmax': self.retmax
        }
        with open(os.path.join(self.repo_dir, 'config.json'), 'w') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    def initiallize(self):
        self.search_pmc()
        self.fetch_full_text()
        self.save_config()

if __name__ == '__main__':
    if os.path.exists('repodir'):
        shutil.rmtree('repodir')
    articelfinder = ArticleRetrieval(keywords = ['covid-19'],repo_dir = 'repodir',retmax = 5)
    pmc_ids = articelfinder.search_pmc()
    articelfinder.fetch_full_text(pmc_ids)
