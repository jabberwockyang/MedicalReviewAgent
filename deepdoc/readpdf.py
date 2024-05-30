from deepdoc.parser import RAGFlowPdfParser, PlainParser
import os
from PIL import Image
import json
class PDFprocess():
    def __init__(self, repodir, workdir):
        self.repodir = repodir
        self.preprocessdir = os.path.join(workdir,'preprocess')
        self.pdf_parser = RAGFlowPdfParser()
        # self.plain_parser = PlainParser()
            
    def _save_image(self,image, path, name):
        """ 保存图片到指定路径 """
        if not os.path.exists(path):
            os.makedirs(path)
        image_path = os.path.join(path, name)
        image.save(image_path)
        return image_path

    def save_all_image(self,preprocessdir,tables):
        image_folder = os.path.join(preprocessdir,'saved_images')
        # 假设 res 中包含了图片对象和其他数据
        for index, data in enumerate(tables):
            image, text = data  # 假设 data 结构是这样的
            image_path = self._save_image(image, image_folder, f'image_{index}.png')
            # relative_path = os.path.relpath(image_path, preprocessdir)
            tables[index] = (image_path, text)  # 更新 res 中的图片对象为图片路径
        return tables

    def create_html_file(self,tables, html_file_path):
        html_content = '<html><body>\n'
        for index, data in enumerate(tables):
            image_path, text = data
            # 创建图片链接和文本
            html_content += f'<img src="{image_path}" alt="Image">\n{text}\n'
        html_content += '</body></html>'
        
        # 写入 HTML 文件
        with open(html_file_path, 'w') as file:
            file.write(html_content)
    def process(self, pdffilename):
        pdf_file_path = os.path.join(self.repodir,pdffilename)
        text_content, tables = self.pdf_parser(pdf_file_path, need_image=False, zoomin=3, return_html=True)

        text_file_path = os.path.join(self.preprocessdir,pdffilename.replace('.pdf','.txt'))
        with open(text_file_path, 'w') as f:
            f.write(text_content)

        image_folder = os.path.join(self.preprocessdir,f'{pdffilename}_images')
        tables = self.save_all_image(image_folder,tables)

        html_file_path = os.path.join(self.preprocessdir,pdffilename.replace('.pdf','.html'))
        self.create_html_file(tables, html_file_path)

        json_file_path = os.path.join(self.preprocessdir,pdffilename.replace('.pdf','.json'))
        with open(json_file_path, 'w') as f:
            json.dump(tables, f, indent=4, ensure_ascii=False)
if __name__ == '__main__':
    repodir = '/Users/chen/Downloads/ReviewAgent2'
    preprocessdir = '/Users/chen/Downloads/ReviewAgent2/preprocess'
    pdfprocess = PDFprocess(repodir, preprocessdir)
    pdfprocess.process('test.pdf')
