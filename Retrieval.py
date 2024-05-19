import requests
import xml.etree.ElementTree as ET
import argparse
import os 
from tqdm import tqdm

## 通过PMC数据库检索文章
def search_pmc(keywords, retmax=10):

    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pmc",
        "term": ','.join(keywords),
        "retmax": retmax
    }
    response = requests.get(base_url, params=params)
    root = ET.fromstring(response.content)
    pmc_ids = [id_element.text for id_element in root.findall('.//Id')]
    return pmc_ids

# 解析XML文件
def get_all_text(element):
    """递归获取XML元素及其所有子元素的文本内容"""
    text = element.text or ""
    for child in element:
        text += get_all_text(child)
        if child.tail:
            text += child.tail
    return text

## 清洗XML文件
def clean_xml(txt):
    root = ET.fromstring(txt)
    txt = get_all_text(root)
    txt = txt.split('REFERENCES')[0]  # 截取参考文献之前的文本
    text = '\n\n'.join([t.strip() for t in txt.split('\n') if len(t.strip())>250])
    return text

## 通过PMC数据库获取全文
def fetch_full_text(pmc_ids,repo_dir):
    if not os.path.exists(repo_dir):
        os.makedirs(repo_dir)

    for id in tqdm(pmc_ids, desc="Fetching full texts", unit="article"):
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        params = {
            "db": "pmc",
            "id": id,
            "rettype": "xml",
            "retmode": "text"
        }
        response = requests.get(base_url, params=params)
        full_text = clean_xml(response.text)
        with open(os.path.join(repo_dir,f'{id}.txt'), 'w') as f:
            f.write(full_text)


## 解析命令行参数
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Feature store for processing directories.')
    parser.add_argument('--keywords',
                        type=str,
                        nargs='+',
                        help='Keywords for searching articles.')
    parser.add_argument('--retmax',
                        type=int,
                        default=500,
                        help='Maximum number of articles to retrieve.')
    parser.add_argument(
        '--repo_dir',
        type=str,
        default='repodir',
        help='Root directory where the repositories are located.')
    
    args = parser.parse_args()
    return args

    

if __name__ == '__main__':
    args = parse_args()
    keywords = args.keywords
    repo_dir = args.repo_dir
    retmax = args.retmax
    pmc_ids = search_pmc(keywords, retmax=retmax)

    print(f"Found {len(pmc_ids)} articles.")
    print(f"Saving articles to {repo_dir}.")

    fetch_full_text(pmc_ids,repo_dir)
