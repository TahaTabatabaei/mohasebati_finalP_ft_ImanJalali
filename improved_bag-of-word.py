# -*- coding: utf-8 -*-
"""Untitled1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Iuc3R_1uAR8ZOU5MGaeNpfbPYUPDQt_V

import library
"""

import os
import random
import re
import string
import  math
import nltk
import numpy as np
import pandas as pd

from gensim.models import Word2Vec

from nltk import word_tokenize
from nltk.corpus import stopwords

from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_samples, silhouette_score

nltk.download("stopwords")
import nltk
nltk.download('punkt')

SEED = 42
random.seed(SEED)
os.environ["PYTHONHASHSEED"] = str(SEED)
np.random.seed(SEED)

"""read data"""

from google.colab import drive

drive.mount('/content/gdrive')

import pandas as pd
train_path = '/content/gdrive/MyDrive/nlp/train.csv'
test_path = '/content/gdrive/MyDrive/nlp/test.csv'

df = pd.read_csv(train_path)


df_test = pd.read_csv(test_path)

comments = df.values[:10,1]
comments_test = df_test.values[:10,1]

"""bagofword and clean text function"""

def clean_text(comments, tokenizer, stopwords):
    """Pre-process comments and generate Kword

    Args:
        comments: comments to tokenize.

    Returns:
        Tokenized comments.
    """
    comments = str(comments).lower()  # Lowercase words
    comments = re.sub(r"\[(.*?)\]", "", comments)  # Remove [+XYZ chars] in content
    comments = re.sub(r"\s+", " ", comments)  # Remove multiple spaces in content
    comments = re.sub(r"\w+…|…", "", comments)  # Remove ellipsis (and last word)
    comments = re.sub(r"(?<=\w)-(?=\w)", " ", comments)  # Replace dash between words
    comments = re.sub(
        f"[{re.escape(string.punctuation)}]", "", comments
    )  # Remove punctuation

    Kword = tokenizer(comments)  # Get Kword from comments
    Kword = [t for t in Kword if not t in stopwords]  # Remove stopwords
    Kword = ["" if t.isdigit() else t for t in Kword]  # Remove digits
    Kword = [t for t in Kword if len(t) > 1]  # Remove short Kword
    return Kword

custom_stopwords = set(stopwords.words("english") + ["news", "new", "top"])
text_columns = ["Id", "Comment", "Topic"]

df = df[:10].copy()
df_test = df_test[:10].copy()

df["Topic"] = df["Topic"].fillna("")
df_test["Topic"] = df_test["Topic"].fillna("")

for col in text_columns:
    df[col] = df[col].astype(str)
    df_test[col] = df_test[col].astype(str)

# Create text column based on title, description, and Topic
df["text"] = df[text_columns].apply(lambda x: " | ".join(x), axis=1)
df["tokens"] = df["text"].map(lambda x: clean_text(x, word_tokenize, custom_stopwords))


#for test
df_test["text"] = df_test[text_columns].apply(lambda x: " | ".join(x), axis=1)
df_test["tokens"] = df_test["text"].map(lambda x: clean_text(x, word_tokenize, custom_stopwords))


tok = [df["tokens"].values[i][j]for i in range(len(df["tokens"])) for j in range(1,len(df["tokens"].values[i]))]
tok_test = [df_test["tokens"].values[i][j]for i in range(len(df_test["tokens"])) for j in range(1,len(df_test["tokens"].values[i]))]

tok1 = list(set(tok))
tok1_test = list(set(tok_test))
#print(tok1)

tok2 = []
for i in range(len(df["tokens"])):
  a = list(df["tokens"].values[i][1:len(df["tokens"].values[i])-1])
  tok2.append(a)


tok2_test = []
for i in range(len(df_test["tokens"])):
  a = list(df_test["tokens"].values[i][1:len(df_test["tokens"].values[i])-1])
  tok2_test.append(a)


# Remove duplicated after preprocessing
_, idx = np.unique(df["tokens"], return_index=True)
df = df.iloc[idx, :]
#for test
_, idx = np.unique(df_test["tokens"], return_index=True)
df_test = df_test.iloc[idx, :]

# Remove empty values and keep relevant columns
df = df.loc[df.tokens.map(lambda x: len(x) > 0), ["text", "tokens"]]
df_test = df_test.loc[df.tokens.map(lambda x: len(x) > 0), ["text", "tokens"]]

docs = df["text"].values
tokenized_docs = df["tokens"].values

#for test
docs = df_test["text"].values
tokenized_docs = df_test["tokens"].values

"""TF,IDF function"""

def tf(comment,tok,AW):
    
    corpus = comment
    words_set = tok



    n_docs = len(corpus)         #·Number of documents in the corpus
    n_words_set = len(words_set) #·Number of unique words in the 
    df_tf = pd.DataFrame(np.zeros((n_docs, n_words_set)), columns=words_set)
    # df_tf
    # words_set


    # Compute Term Frequency (TF)
    for i in range(n_docs):
        words = AW[i]
        #words = corpus[i].split(' ') # Words in the document
        for w in words:
            df_tf[w][i] = df_tf[w][i] + (1 / len(words))

    #print(df_tf)

    #print("IDF of: ")

    # Compute Inverse Document Frequency (IDF)
    idf = {}

    for w in words_set:
        k = 1    # number of documents in the corpus that contain this word
    
        for i in range(n_docs):
            if w in AW[i]:
                k += 1
        
        idf[w] =  np.log10(n_docs / k)
    
        #print(f'{w:>15}: {idf[w]:>10}' )
        
    df_tf_idf = df_tf.copy()

    for w in words_set:
        for i in range(n_docs):
            df_tf_idf[w][i] = df_tf[w][i] * idf[w]

    return df_tf_idf

tok_ALL = list(set(tok1 + tok1_test))
X_train = tf(comments,tok_ALL,tok2)
X_test = tf(comments_test,tok_ALL,tok2_test)
print(X_test)

"""create model and load vocabulary"""

model = Word2Vec(sentences=tokenized_docs, size=100, workers=1, seed=SEED)

import gensim
import gensim.downloader as api

wv = api.load('word2vec-google-news-300')

"""vectorize"""

def vectorize(list_of_docs, model):
    """Generate vectors for list of documents using a Word Embedding

    Args:
        list_of_docs: List of documents
        model: Gensim's Word Embedding

    Returns:
        List of document vectors
    """
    features = []

    for tokens in list_of_docs:
        zero_vector = np.zeros(model.vector_size)
        vectors = []
        for token in tokens:
            if token in model.wv:
                try:
                    vectors.append(model.wv[token])
                except KeyError:
                    continue
        if vectors:
            vectors = np.asarray(vectors)
            avg_vec = vectors.mean(axis=0)
            features.append(avg_vec)
        else:
            features.append(zero_vector)
    return features
    
vectorized_docs = vectorize(tokenized_docs, model=model)
vectorized_docs[0]
len(vectorized_docs), len(vectorized_docs[0])

"""clustering"""

import numpy as np
import math
import numba


def Key_Identification(vectors , k_nighboors , Data_Dimension, C_Target , g):
    vecrotsCount = len(vectors)

    data = np.empty((vecrotsCount  , Data_Dimension))
    # sakht label ha
    L_set = np.arange(vecrotsCount)
    C_Current = math.floor(vecrotsCount / g)

    for i in range(0 , vecrotsCount) :
            data[i] = vectors[i]

    if (C_Target >= C_Current):
        return L_set
    
    # mohasebe D_Original
    D_Original = np.zeros((vecrotsCount, vecrotsCount) )

    for i in range(0 , vecrotsCount ):
            for j in range(0 , vecrotsCount) :
                D_Original[i , j] = dist(i , j , data, Data_Dimension)
    

    # mohasebe R har element
    R_set = np.empty((vecrotsCount, k_nighboors + 1))
    for i in range( 0 , vecrotsCount):
        sorted = np.argsort(D_Original[i])
        for j in range(0 , k_nighboors + 1):
            R_set[i][j] = sorted[j]

    R_set = R_set.astype(int)

    # mohasebe D-Current
    D_Current = np.zeros((vecrotsCount ,vecrotsCount))

    for i in range(0 , vecrotsCount):
        for j in range(0 , i):
            # if (i == j):
            #     D_Current[i][j] = 0
            # else:
                avg_dist = 0
                for k in range(0 , k_nighboors+1):
                    for l in range(0 , k_nighboors+1):
                        # R_set[i][k] = int(R_set[i][k])

                        avg_dist += D_Original[R_set[i][k]][R_set[j][l]]

                avg_dist = avg_dist / ((k_nighboors+1)*(k_nighboors+1))
                D_Current[i][j] = avg_dist
                D_Current[j][i] = avg_dist

    while(C_Current > C_Target):
        keyPoints = findKeyPoints(n_keys=C_Current ,D_Current_set=D_Current)

    # edgham 2 cluster, ba peyda kardan cluster ba fasele minimum az cluster i
        m = len(D_Current)
        for i in range(0, m):
            min = math.inf
            min_cluster_index =0

            for j in range(0 , len(keyPoints)):
                if (D_Current[i][keyPoints[j]] < min):
                    min = D_Current[i][j]
                    min_cluster_index = j
            
            for k in range(0, len(L_set)):
                if (L_set[k] == i):
                    L_set[k] = min_cluster_index


    #  update faseleha
        p_set = [[]*vecrotsCount]

        for i in range(0, len(keyPoints)):
            for j in range(0,vecrotsCount):
                if (L_set[j] == keyPoints[i]):
                    p_set[keyPoints[i]].append(j)
                    p_set[keyPoints[i]] = list(set().union(p_set[keyPoints[i]] , R_set[j]))

        m = len(keyPoints)
        D_Current = np.zeros((m , m))

        for i in range(0, m):
             for j in range(0, i):
            #     if (i == j):
            #         D_Current[i][j] = 0
            #     else:
                    value = matrix_new_dist(p_set[i] , p_set[j] , D_Original)
                    D_Current[i][j] = value
                    D_Current[j][i] = value

        C_Current =  math.floor(C_Current/g)

    return L_set

@numba.jit(nopython = True,)
def dist(i , j, data, dimension):

        distance = 0
        distance = np.linalg.norm(float(data[i]),float(data[j]))
        # for k in range(0 , dimension):
        #     distance += math.pow(data[i, k] - data[j, k], 2)
             
        # return math.sqrt(distance)
        return distance

def findKeyPoints(n_keys, D_Current_set):
        m = len(D_Current_set)
        min = math.inf
        s_keys = []
        key = 0

        for i in range(0, m):
            distance = 0
            for j in range(0, m):
                 distance += D_Current_set[i][j]
            avg_distance = distance/m

            if (avg_distance < min):
                min = avg_distance
                key = i
        s_keys.append(key)

        for i in range(0 , n_keys-1):
            max = -math.inf
            key = 0

            for j in range(0 , m):
                min = math.inf

                for k in range(0 , len(s_keys)):
                    if (D_Current_set[j][s_keys[k]] < min):
                        min = D_Current_set[j][s_keys[k]]

                if min > max :
                 max = min
                 key = j

            s_keys.append(key)

        return s_keys


def matrix_new_dist(p_set1 ,p_set2, Dist_Original):
    sum = 0
    for a in range( 0 , len(p_set1)) :
        for b in range( 0 , len(p_set2)):
            sum += Dist_Original[p_set1[a]][p_set2[b]]

    return  (sum / (len(p_set1) * len(p_set2)))

Key_Identification(vectors = vectorized_docs , k_nighboors = 4 , Data_Dimension = 100, C_Target = 900 , g = 10)

"""DecisionTree"""

from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score

# Y = label haye comments

label = df.drop(['Id','Comment'], axis=1)
label_test = df_test.drop(['Id','Comment'], axis=1)

Y = [label.values[i][0] for i in range(len(label))]
Y_test = [label_test.values[i][0] for i in range(len(label_test))] 

Y = Y[:10]
Y_test = Y_test[:10]

model = DecisionTreeClassifier()
clf = model.fit(X_train, Y)


labels = clf.predict(X_test)
labels1 = clf.score(X_test,Y_test)
#label1 = accuracy_score(Y_test,labels)
labels1

