import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import pandas as pd
import os
import json 
from loguru import logger
import faiss   

class Clusterer():

    def __init__(self, 
                 text: list,
                 text_embedding:np.array,
                 n_clusters: list|int):
        self.text = text
        self.text_embedding = text_embedding
        self.n_clusters = n_clusters


    # https://github.com/facebookresearch/faiss/issues/1875
    def _silhouette_score(self, cluster_index, samples) -> float:
        distance, _ = cluster_index.search(samples, 2)

        # a = distance[:, 0], b = distance[:, 1]
        # s = (b - a) / np.max(a, b)
        s = (distance[:, 1] - distance[:, 0]) / np.max(distance, 1)
        return s.mean()


    # def _find_best_nclusters(self):
    #     silhouette_scores = []
    #     cluster_range = range(self.cluster_range[0], self.cluster_range[1],5) 

    #     nparray = np.array(self.text_embedding)
    #     n, d = nparray.shape  # 获取数据点的数量和维度
    #     x = nparray.astype('float32')  # 转换数据类型为float32

    #     niter = 20 
    #     verbose = True

    #     for ncentroids in cluster_range:

    #         kmeans = faiss.Kmeans(d, ncentroids, niter=niter, verbose=verbose)
    #         kmeans.train(x)

    #         scores = self._silhouette_score(kmeans.index, x)
    #         silhouette_scores.append(scores)

    #     self.result = zip(cluster_range, silhouette_scores)
    #     best_n_clusters = cluster_range[silhouette_scores.index(max(silhouette_scores))]
    #     logger.info(f"Optimal number of clusters: {best_n_clusters}")
    #     if best_n_clusters < 10:
    #         logger.debug('Number of clusters is less than 10, please check the data, set to default 10')
    #         self.n_clusters = 10
    #     else:
    #         self.n_clusters = best_n_clusters   

    def kmeanscluster(self, n_clusters: int = None):
        '''
        input:

        - random_state: int, random state for kmeans

        output:

        - cluster labels saved to metadata
        '''
        if self.text_embedding is None:
            raise ValueError('No embeddings of repo found, please run generate_embeddings first')
        
        logger.info(f'Using n_clusters: {n_clusters}')

        nparray = np.array(self.text_embedding)
        n, d = nparray.shape  # 获取数据点的数量和维度
        x = nparray.astype('float32')  # 转换数据类型为float32

        ncentroids = n_clusters
        niter = 100  
        verbose = True

        kmeans = faiss.Kmeans(d, ncentroids, niter=niter, verbose=verbose)
        kmeans.train(x)

        index = faiss.IndexFlatL2(d)
        index.add(x)
        D, I = index.search(kmeans.centroids, 50)

        samples = {}
        for i in range(ncentroids):
            samples[i] ={
                'cluster': i,
                'samples': [self.text[j] for j in I[i]],
                'distance': D[i].tolist()
            }

        score = self._silhouette_score(kmeans.index, x)

        logger.info(f'kmeans with k = {n_clusters} complete. Silhouette score: {score}')
        result = (n_clusters, score)
        return result, samples
        


    def generate_cluster(self, workdir: str):
        '''
        generate cluster
        '''
        feature_dir = os.path.join(workdir, 'cluster_features')
        if not os.path.exists(feature_dir):
            os.makedirs(feature_dir)

        results = []    
        for n_clusters in self.n_clusters:
            sub_dir = os.path.join(feature_dir, f'cluster_features_{n_clusters}')

            if not os.path.exists(sub_dir):
                os.makedirs(sub_dir)

            result, samples = self.kmeanscluster(n_clusters)
            # save k and score result
            results.append(result)
            path = os.path.join(sub_dir, f'kresult.txt')
            with open(path, 'w') as f:
                f.write(str(result))    

            # save samples
            path = os.path.join(sub_dir, f'samples.json')
            with open(path, 'w') as f:
                json.dump(samples, f,ensure_ascii=False)

        # save all results
        path = os.path.join(feature_dir, 'all_results.txt')
        with open(path, 'w') as f:
            for k, score in results:
                f.write(f'k={k}, score={score}\n')
            
