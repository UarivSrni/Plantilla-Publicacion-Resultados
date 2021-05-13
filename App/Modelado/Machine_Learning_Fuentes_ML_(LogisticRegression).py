#!/usr/bin/env python
# coding: utf-8

# In[37]:


get_ipython().run_line_magic('load_ext', 'watermark')
get_ipython().run_line_magic('watermark', '')


# In[38]:


# Librerias
import pandas as pd
import numpy as np

from unicodedata import normalize
import nltk
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model  import LinearRegression as LinReg
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.svm import LinearSVC
from spacy.lang.es.stop_words import STOP_WORDS
import matplotlib.pyplot as plt

import es_core_news_sm
nltk.download('stopwords')
nlp = es_core_news_sm.load()
#import nltk.data
#sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
from datetime import date
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from parsel import Selector

from io import StringIO
import os
import re
import scrapy
from datetime import datetime

from sklearn.metrics import f1_score
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.naive_bayes import GaussianNB, BernoulliNB, MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
import json

from requests.exceptions import ConnectionError
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import FunctionTransformer
from scipy.sparse import issparse

# Funciones adicionales
now = datetime.now()
dt_string = now.strftime("%d/%m/%Y")

def limpieza(fuentes):
    agregar_dato=[]
    for item in fuentes:
        agregar_dato.append(item.replace('\xa0', ''))
    return(agregar_dato)

def limpieza_descripcion(variable_corregir):
    valor_limpio = list(map(lambda d: d.replace('\r\n', ''), variable_corregir))
    valor_limpio = [i.strip('\n') for i in valor_limpio]
    valor_limpio = [i.strip('\r') for i in valor_limpio]
    valor_limpio = limpieza(valor_limpio)
    
    variable_almacenamiento = []
    for x in valor_limpio:
        x = remove_tags(x)
        variable_almacenamiento.append(x)
    return (variable_almacenamiento)

TAG_RE = re.compile(r'<[^>]+>')
def remove_tags(text):
    text = text.lower()
    text = re.sub('<.*?>', '', text)
    text = re.sub(':.*?:', '', text)
    text = re.sub(r"([^n\u0300-\u036f]|n(?!\u0303(?![\u0300-\u036f])))[\u0300-\u036f]+", r"\1", normalize( "NFD", text), 0, re.I)
    text = text.replace(',', '')
    text = text.replace(';', '')
    return TAG_RE.sub('', text)

# COMMAND ----------

def deletestopwords(text):
    word_tokens = nltk.word_tokenize(text)
    stop_words_sp = STOP_WORDS # WITH SPACY
    word_tokens_clean = [each for each in word_tokens if each.lower() not in stop_words_sp and len(each.lower()) > 2]
    return word_tokens_clean

def lemmatizer(text):  
    doc = nlp(text)
    return ' '.join([word.lemma_ for word in doc])

def formatingText(text):
    text = text.lower()
    text = re.sub('<.*?>', '', text)
    text = re.sub(':.*?:', '', text)
    text = re.sub(r"([^n\u0300-\u036f]|n(?!\u0303(?![\u0300-\u036f])))[\u0300-\u036f]+", r"\1", normalize( "NFD", text), 0, re.I)
    text = normalize( 'NFC', text)
    text = re.sub('[^a-z ]', '', text)
    return text

def lemant(text1):
    x=text1.lower()
    stopwords= deletestopwords(x)
    stopwords=str(stopwords)
    clean = formatingText(stopwords)
    final = lemmatizer(clean)
    return final


# ## Machine Learning

# In[39]:


with open ("C:/Users/harold.patino/Documents/Periodicos/DeVops/stopwords-es.json") as fname:
    stopwords_es = json.load(fname)
vectorizar_news = TfidfVectorizer(strip_accents='unicode', stop_words=stopwords_es)


# In[40]:


# Machine Learning
news = pd.read_csv("C:/Users/harold.patino/Documents/lectura_archivos/Data/NoticiasDataV01_PRUEBA_maestra.csv" , sep=';')
news = news[['REVIEW','TIP_EVEN','CAT_EVENTO']]

# http://rasbt.github.io/mlxtend/
class DenseTransformer(BaseEstimator):
    def __init__(self, return_copy=True):
        self.return_copy = return_copy
        self.is_fitted = False

    def transform(self, X, y=None):
        if issparse(X):
            return X.toarray()
        elif self.return_copy:
            return X.copy()
        else:
            return X

    def fit(self, X, y=None):
        self.is_fitted = True
        return self

    def fit_transform(self, X, y=None):
        return self.transform(X=X, y=y)

vectorizador =  TfidfVectorizer(strip_accents='unicode', stop_words=STOP_WORDS)
vectorizador.fit(news.REVIEW)

def model_type():
    
    pipeline_logistica = make_pipeline (
    vectorizador,
    DenseTransformer(),
    LogisticRegression(C=5, verbose=1, random_state=0, penalty='l2')
    )
    modelo = pipeline_logistica.fit(X=news.REVIEW, y= news.TIP_EVEN)
    return modelo


def model_cat():
   
    pipeline_logistica = make_pipeline (
    vectorizador,
    DenseTransformer(),
    LogisticRegression(C=5, verbose=1, random_state=0, penalty='l2')
    )
    modelo = pipeline_logistica.fit(X=news.REVIEW, y= news.CAT_EVENTO)
    return modelo

predCateg = model_cat()
predType = model_type()


# ## Periodicos

# In[41]:


# EL Nuevo Siglo (Bogotá)
r=requests.get("https://www.elnuevosiglo.com.co/rss.xml")
soup = BeautifulSoup(r.content, features ="xml")
items = soup.findAll('item')

news_items = []
for item in items:
    news_item = {}
    news_item['title'] = item.title.text
    news_item['description']= item.description.text
    news_item['description']= remove_tags(news_item['description']).replace('\n', '')
    news_item['description']= lemant(news_item['description'])
    news_item['pubDate'] = item.pubDate.text
    news_item['link'] = item.link.text
    news_item['category']="El Nuevo Siglo"
    news_item['medium']="El Nuevo Siglo"
    #--  Predict
    vect_text1 = news_item['description']
    news_item['predi_categ'] = predCateg.predict([vect_text1])[0]
    news_item['predi_type'] = predType.predict([vect_text1])[0]    
    news_items.append(news_item)
    
df_rss_elsiglo = pd.DataFrame(news_items, columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])


# In[42]:


# EL Nuevo Dia (Ibagué)
r=requests.get("http://www.elnuevodia.com.co/nuevodia/rss.xml")
soup = BeautifulSoup(r.content, features ="xml")
items = soup.findAll('item')


news_items = []
for item in items:
    news_item = {}
    news_item['title'] = item.title.text
    news_item['description']= item.description.text
    news_item['description']= remove_tags(news_item['description']).replace('\n', '')
    news_item['pubDate'] = item.pubDate.text
    news_item['link'] = item.link.text
    news_item['category']= "El Nuevo Dia"
    news_item['medium']="El Nuevo Dia" 
    #--  Predict
    vect_text1 = lemant(news_item['description'])
    news_item['predi_categ'] = predCateg.predict([vect_text1])[0]
    news_item['predi_type'] = predType.predict([vect_text1])[0]    
    news_items.append(news_item)
        
df_noticias_nuevodia = pd.DataFrame(news_items,columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])
        


# In[43]:


# EL Pais (Cali)
r=requests.get("https://www.elpais.com.co/rss/cali")
soup = BeautifulSoup(r.content, features ="xml")
items = soup.findAll('item')


news_items = []
for item in items:
        news_item = {}
        news_item['title'] = item.title.text
        news_item['description']= item.articleSlug.text
        news_item['description']= remove_tags(news_item['description']).replace('\n', '').replace('-',' ').replace('/', ' ')
        news_item['pubDate'] = item.pubDate.text 
        news_item['link'] = item.link.text
        news_item['category']= item.category.text
        news_item['medium']="El Pais"  
        #--  Predict
        vect_text1 = lemant(news_item['description'])
        news_item['predi_categ'] = predCateg.predict([vect_text1])[0]
        news_item['predi_type'] = predType.predict([vect_text1])[0] 
        news_items.append(news_item)
        
df_noticias_elpais = pd.DataFrame(news_items,columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])


# In[44]:


# Diario del Norte - La Guajira Hoy (La Guajira)
def fuentes_guajira_hoy(periodico_url):
    r=requests.get(periodico_url)
    soup = BeautifulSoup(r.content, features ="xml")
    items = soup.findAll('item')
    
   
    news_items = []
    for item in items:
        news_item = {}
        news_item['title'] = item.title.text
        news_item['description']= item.description.text
        news_item['description']= remove_tags(news_item['description']).lstrip('<p>')
        news_item['description'] = lemant(news_item['description'])
        news_item['pubDate'] = item.pubDate.text 
        news_item['link'] = item.link.text
        news_item['category']= item.category.text
        news_item['medium']="La Guajira Hoy"
        #--  Predict
        vect_text1 = news_item['description']
        news_item['predi_categ'] = predCateg.predict([vect_text1])[0]
        news_item['predi_type'] = predType.predict([vect_text1])[0] 
        news_items.append(news_item)
       
            
    rss_guajira_hoy = pd.DataFrame(news_items,columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])   
    return rss_guajira_hoy

guajirahoy_guajira = fuentes_guajira_hoy('https://laguajirahoy.com/seccion/la-guajira/feed')
guajirahoy_riohacha = fuentes_guajira_hoy('https://laguajirahoy.com/seccion/riohacha/feed')
guajirahoy_judicial = fuentes_guajira_hoy('https://laguajirahoy.com/seccion/judiciales/feed')

df_guajira_hoy = pd.concat([guajirahoy_guajira, guajirahoy_riohacha,guajirahoy_judicial])


# In[45]:


# La Nación(Huila)
def fuentes_lanacion_huila(periodico_url):
    r=requests.get(periodico_url)
    soup = BeautifulSoup(r.content, features ="xml")
    items = soup.findAll('item')
    
    news_items = []
    for item in items:
        news_item = {}
        news_item['title'] = item.title.text
        news_item['description']= item.description.text
        news_item['pubDate'] = item.pubDate.text 
        news_item['link'] = item.link.text
        news_item['category']= item.category.text
        news_item['medium']="La Nación" 
        #--  Predict
        vect_text1 = lemant(news_item['description'])
        news_item['predi_categ'] = predCateg.predict([vect_text1])[0]
        news_item['predi_type'] = predType.predict([vect_text1])[0] 
        news_items.append(news_item)    
            
    lanacion_huila = pd.DataFrame(news_items,columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])
    return lanacion_huila

nacion_huila = fuentes_lanacion_huila('https://www.lanacion.com.co/category/regional-huila/feed/')
nacion_judicial = fuentes_lanacion_huila('https://www.lanacion.com.co/category/judicial/feed/')

df_la_nacion = pd.concat([nacion_huila, nacion_judicial])


# In[46]:


def fuentes_pilon (periodico_url):
    try:
    
        r_noticias=requests.get(periodico_url)
        sel=Selector(r_noticias.text)  
        if r_noticias.status_code==200:

            descripcion = sel.css('div p::text').extract()
            descripcion_corregida = limpieza_descripcion(descripcion)
            catego = []
            tipo = []
            for x in descripcion_corregida:
                vect_text1 = lemant(x)
                predi_categ = predCateg.predict([vect_text1])[0]
                predi_type = predType.predict([vect_text1])[0] 
                catego.append(predi_categ)
                tipo.append(predi_type)

            noticias = {} 
            noticias['title'] = sel.css("h4>a::text").extract()
            noticias['description']= descripcion_corregida
            noticias['category']= sel.css('section h1::text').extract()
            noticias['category']= list(map(lambda d: d.replace('\n        ', ''), noticias['category']))[0]
            noticias['link'] = periodico_url
            noticias['pubDate'] = sel.css('li span ::text').extract()
            noticias['medium']="El Pilon"
            #--  Predict
            noticias['predi_type'] = tipo
            noticias['predi_categ'] = catego
            df_pilon = pd.DataFrame(noticias,columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])
            return df_pilon

        else:
            print(periodico_url) 
    except:
        pass
            
fuente_judicial = fuentes_pilon('https://elpilon.com.co/Noticias/judicial/')
fuente_valledupar = fuentes_pilon('https://elpilon.com.co/Noticias/valledupar/')
fuente_cesar = fuentes_pilon('https://elpilon.com.co/Noticias/cesar-y-la-guajira/cesar/')
fuente_guajira = fuentes_pilon('https://elpilon.com.co/Noticias/cesar-y-la-guajira/la-guajira/')
fuente_municipios = fuentes_pilon('https://elpilon.com.co/Noticias/cesar-y-la-guajira/municipios/')
fuente_sur = fuentes_pilon('https://elpilon.com.co/Noticias/cesar-y-la-guajira/sur/')

df_noticias_pilon = pd.concat([fuente_judicial, fuente_valledupar, fuente_cesar, fuente_guajira, fuente_municipios, fuente_sur])


# In[47]:


# Diario del Huila
def fuentes_huila (periodico_url):
    r_noticias=requests.get(periodico_url)
    sel=Selector(r_noticias.text) 
    
    titulo = sel.css("h2 a.et-accent-color::text, h3 a::text").extract()
    titulo = [i.strip('\n') for i in titulo]
    descripcion = sel.css("div.main-post p::text, h3 a::text").extract()
    descripcion_corregida = limpieza_descripcion(descripcion)
    catego = []
    tipo = []
    for x in descripcion_corregida:
        vect_text1 = lemant(x)
        predi_categ = predCateg.predict([vect_text1])[0]
        predi_type = predType.predict([vect_text1])[0] 
        catego.append(predi_categ)
        tipo.append(predi_type)
       
    noticias = {}
    noticias['title'] = titulo
    noticias['description'] = descripcion_corregida
    noticias['category']= sel.css('h1::text').extract_first()
    noticias['link'] = periodico_url
    noticias['pubDate'] = sel.css('span.updated::text').extract()
    noticias['medium']="Diario El Huila"
    #--  Predict
    noticias['predi_type'] = tipo
    noticias['predi_categ'] = catego

    df_huila = pd.DataFrame(noticias,columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])
    return df_huila


fuente_judicial = fuentes_huila("https://diariodelhuila.com/judicial/")
fuente_neiva = fuentes_huila("https://diariodelhuila.com/neiva/")
fuente_regional = fuentes_huila("https://diariodelhuila.com/regional/")

df_noticias_huila = pd.concat([fuente_judicial, fuente_neiva, fuente_regional])


# In[48]:


# Prensa Libre
def fuentes_prensalibre (periodico_url):
    r_noticias = requests.get(periodico_url)
    soup = BeautifulSoup(r_noticias.content, 'html.parser')

    titulo=soup.findAll('h2', class_='title')
    titulo=[i.get_text().strip('\n') for i in titulo]
    descripcion=soup.findAll('div', class_='clrfix')
    descripcion=[i.get_text().strip('\n') for i in descripcion][1:-2]
    descripcion = limpieza(descripcion)
    fecha =soup.findAll('div', class_='pr-post-info')
    fecha=[i.get_text().strip().split(',')[0] for i in fecha]
    categoria =soup.findAll('div', class_='pr-post-info')
    categoria =[i.get_text().lower().strip().split(' |')[-1].replace(' ','') for i in categoria]
    enlace =soup.findAll('div', class_='pr-post-info')
    enlace=[i.get_text().lower().strip().split(' |')[-1].split(' /')[-1].replace(' ','') for i in enlace][0]
    enlace = "https://prensalibrecasanare.com/" + enlace
    catego = []
    tipo = []
    for x in descripcion:
        vect_text1 = lemant(x)
        predi_categ = predCateg.predict([vect_text1])[0]
        predi_type = predType.predict([vect_text1])[0] 
        catego.append(predi_categ)
        tipo.append(predi_type)
           
    noticias ={}    
    noticias['title'] = titulo
    noticias['description']= descripcion
    noticias['category']= categoria
    noticias['link'] =  enlace
    noticias['pubDate'] = fecha
    noticias['medium']= 'Prensa Libre Casanare'
    #--  Predict
    noticias['predi_type'] = tipo
    noticias['predi_categ'] = catego
      
    df_libre = pd.DataFrame(noticias,columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])
    df_libre= df_libre.replace('', 'Noticia sin descripción')
    return df_libre


fuente_colombia = fuentes_prensalibre('https://prensalibrecasanare.com/colombia/')
fuente_judicial =fuentes_prensalibre('https://prensalibrecasanare.com/judicial/')
fuente_yopal =fuentes_prensalibre('https://prensalibrecasanare.com/yopal/')
fuente_casanare =fuentes_prensalibre('https://prensalibrecasanare.com/casanare/')

df_noticias_PrensaLibre = pd.concat([fuente_colombia, fuente_judicial, fuente_yopal, fuente_casanare])


# In[49]:


# Extra -Judicial
noticia = "https://caqueta.extra.com.co/noticias/judicial"
r_noticias=requests.get(noticia)
sel=Selector(r_noticias.text)

descripcion = sel.css("div.region.region-content div.even::text").extract()
descripcion = [i.strip() for i in descripcion]
catego = []
tipo = []
for x in descripcion:
    vect_text1 = lemant(x)
    predi_categ = predCateg.predict([vect_text1])[0]
    predi_type = predType.predict([vect_text1])[0] 
    catego.append(predi_categ)
    tipo.append(predi_type)

noticias = {}    
noticias['title'] = sel.css("div.region.region-content h2 a::text").extract()
noticias['description']= descripcion
noticias['category']= sel.css("h1.title::text").extract_first().lower()
noticias['link'] =  'https://caqueta.extra.com.co/noticias/' + noticias['category']
noticias['pubDate'] = sel.css("div.region.region-content div.field.field-datetime div.field-item::text").extract()
noticias['pubDate'] = [i.split(' -')[0] for i in noticias['pubDate']]
noticias['medium']= 'Extra Caqueta'
#--  Predict
noticias['predi_type'] = tipo
noticias['predi_categ'] = catego
    
df_extra_judicial = pd.DataFrame(noticias,columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])


# In[50]:


# La Tarde - url El Diario
def fuentes_eldiario (periodico_url):
    r_noticias = requests.get(periodico_url)
    soup = BeautifulSoup(r_noticias.content, 'html.parser')

    titulo=soup.findAll('h2', class_='entry-title')
    titulo=[i.get_text() for i in titulo]
    descripcion=soup.findAll('div', class_='entry-summary')
    descripcion=[i.get_text().strip()[0:-153] for i in descripcion]
    fecha=soup.findAll('time', class_='entry-date')
    fecha=[i.get_text() for i in fecha]
    categoria=soup.findAll('h1', class_='page-title')
    categoria=[i.get_text().strip().lower().lstrip('local') for i in categoria][0]
    enlace = periodico_url
    catego = []
    tipo = []
    for x in descripcion:
        vect_text1 = lemant(x)
        predi_categ = predCateg.predict([vect_text1])[0]
        predi_type = predType.predict([vect_text1])[0] 
        catego.append(predi_categ)
        tipo.append(predi_type)

    noticias = {}
    noticias['title'] = titulo
    noticias['description'] = descripcion
    noticias['category'] =categoria
    noticias['link'] = enlace
    noticias['pubDate'] = fecha
    noticias['medium'] ='El Diario'
    #--  Predict
    noticias['predi_type'] = tipo
    noticias['predi_categ'] = catego  
    
    df_eldiario=pd.DataFrame(noticias,columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])
    return df_eldiario

fuente_pereira =fuentes_eldiario('https://www.eldiario.com.co/categoria/noticias/pereira/')
fuente_risaralda =fuentes_eldiario('https://www.eldiario.com.co/categoria/noticias/risaralda/')
fuente_judicial =fuentes_eldiario('https://www.eldiario.com.co/categoria/judicial/')

df_diario_pereira = pd.concat([fuente_pereira, fuente_risaralda, fuente_judicial])


# In[51]:


# HSB-Noticias 
def fuentes_hsb(periodico_url):
    r_noticias=requests.get(periodico_url)
    sel=Selector(r_noticias.text)
    
    descripcion = sel.css("div.t-content div.field-item.even::text").extract()
    descripcion = [i.strip() for i in descripcion]
    catego = []
    tipo = []
    for x in descripcion:
        vect_text1 = lemant(x)
        predi_categ = predCateg.predict([vect_text1])[0]
        predi_type = predType.predict([vect_text1])[0] 
        catego.append(predi_categ)
        tipo.append(predi_type)
        
    noticias = {}
    noticias['title'] = sel.css("div.t-content h2>a::text").extract()
    noticias['description']= descripcion
    noticias['category']= sel.css("h1.title::text").extract_first()
    noticias['link'] = periodico_url
    noticias['pubDate'] = sel.css("div.t-content div.field.field-datetime div.field-items div.field-item::text").extract()
    noticias['pubDate'] = [i.split(' -')[0] for i in noticias['pubDate']]
    noticias['medium']="HSB - Noticia"
    #--  Predict
    noticias['predi_type'] = tipo
    noticias['predi_categ'] = catego
    hsb = pd.DataFrame(noticias, columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])
    return hsb

hsb_nacional = fuentes_hsb('https://hsbnoticias.com/noticias/nacional')
hsb_local = fuentes_hsb('https://hsbnoticias.com/noticias/local')
hsb_medellin = fuentes_hsb('https://hsbnoticias.com/Medellin')
hsb_cali = fuentes_hsb('https://hsbnoticias.com/Cali')
hsb_pasto = fuentes_hsb('https://hsbnoticias.com/Pasto')
hsb_manizales = fuentes_hsb('https://hsbnoticias.com/Manizales')
hsb_armenia = fuentes_hsb('https://hsbnoticias.com/Armenia')
hsb_barranquilla = fuentes_hsb('https://hsbnoticias.com/Barranquilla')
hsb_popayan = fuentes_hsb('https://hsbnoticias.com/Popayan')
hsb_judicial = fuentes_hsb('https://hsbnoticias.com/noticias/judicial')

df_hsb_noticias = pd.concat([hsb_nacional, hsb_local, hsb_medellin, hsb_cali, hsb_pasto, hsb_manizales, hsb_armenia, hsb_barranquilla, hsb_popayan, hsb_judicial])


# In[52]:


# Diario del Sur 
def fuentes_diario_sur(periodico_url):
    r_noticias=requests.get(periodico_url)
    sel=Selector(r_noticias.text)
    
    descripcion = sel.css("div.t-content div.field-item.even::text").extract()
    descripcion = [i.strip() for i in descripcion]
    catego = []
    tipo = []
    for x in descripcion:
        vect_text1 = lemant(x)
        predi_categ = predCateg.predict([vect_text1])[0]
        predi_type = predType.predict([vect_text1])[0] 
        catego.append(predi_categ)
        tipo.append(predi_type)
        
    noticias = {}
    noticias['title'] = sel.css("div.t-content h2>a::text").extract()
    noticias['description']= descripcion
    noticias['category']= sel.css("h1.title::text").extract_first()
    noticias['link'] = periodico_url
    noticias['pubDate'] = sel.css("div.t-content div.field.field-datetime div.field-items div.field-item::text").extract()
    noticias['pubDate'] = [i.split(' -')[0] for i in noticias['pubDate']]
    noticias['medium']="Diario del Sur"
    #--  Predict
    noticias['predi_type'] = tipo
    noticias['predi_categ'] = catego
    
    diariosur = pd.DataFrame(noticias, columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])
    diariosur= diariosur.replace('...', 'Noticia sin Descripcion')
    return diariosur

sur_judicial = fuentes_diario_sur('https://diariodelsur.com.co/noticias/judicial')
sur_local = fuentes_diario_sur('https://diariodelsur.com.co/noticias/local')
sur_tumaco = fuentes_diario_sur('https://diariodelsur.com.co/tumaco')
sur_ipiales = fuentes_diario_sur('https://diariodelsur.com.co/ipiales')
sur_guachucal = fuentes_diario_sur('https://diariodelsur.com.co/Guachucal')
sur_tuquerres = fuentes_diario_sur('https://diariodelsur.com.co/Tuquerres')
sur_piedemonte = fuentes_diario_sur('https://diariodelsur.com.co/PieDeMonte')
sur_putumayo = fuentes_diario_sur('https://diariodelsur.com.co/Putumayo')

df_diario_del_sur = pd.concat([sur_judicial, sur_local, sur_tumaco, sur_ipiales, sur_guachucal, sur_tuquerres, sur_piedemonte, sur_putumayo])


# In[53]:


# Mi Putumayo
noticia_putumayo = "http://miputumayo.com.co/author/MiPutumayo/"
r_noticias=requests.get(noticia_putumayo)
sel=Selector(r_noticias.text)

descripcion = sel.css("h2.entry-title a::text").extract()
catego = []
tipo = []
for x in descripcion:
    vect_text1 = lemant(x)
    predi_categ = predCateg.predict([vect_text1])[0]
    predi_type = predType.predict([vect_text1])[0] 
    catego.append(predi_categ)
    tipo.append(predi_type)
    
noticias = {}
noticias['title'] = sel.css("h2.entry-title a::text").extract()
noticias['description'] = descripcion
noticias['pubDate'] = sel.css("time.entry-date ::text").extract()
noticias['category']="Noticias Generales"
noticias['link'] = "http://miputumayo.com.co/author/MiPutumayo/"
noticias['medium']="Mi Putumayo"
 #--  Predict
noticias['predi_type'] = tipo
noticias['predi_categ'] = catego
    
df_putumayo = pd.DataFrame(noticias,columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])


# In[54]:


# La Cronica del Quindío 
def fuentes_cronica (periodico_url):
    r_noticias=requests.get(periodico_url)
    sel=Selector(r_noticias.text)
    
    descripcion = sel.css("h2 ::text").extract()
    catego = []
    tipo = []
    for x in descripcion:
        vect_text1 = lemant(x)
        predi_categ = predCateg.predict([vect_text1])[0]
        predi_type = predType.predict([vect_text1])[0] 
        catego.append(predi_categ)
        tipo.append(predi_type)
        
    noticias = {}
    noticias['title'] = sel.css("h2 ::text").extract()
    noticias['description'] = descripcion
    ###No cuenta con fecha noticias['pubDate'] = sel.css("time.entry-date ::text").extract()
    noticias['pubDate'] = dt_string
    noticias['category']= sel.css("h1 span ::text").extract()[0].lower()
    noticias['link'] = periodico_url
    noticias['medium']="La Cronica Del Quindío"
     #--  Predict
    noticias['predi_type'] = tipo
    noticias['predi_categ'] = catego
    
    df_cronica=pd.DataFrame(noticias,columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])
    return df_cronica

fuente_judicial = fuentes_cronica('https://www.cronicadelquindio.com/noticias/judicial')
fuente_region = fuentes_cronica('https://www.cronicadelquindio.com/noticias/region')

df_cronica_quindio = pd.concat([fuente_judicial, fuente_region])


# In[55]:


# Policia Nacional 
try:
    noticia = "https://www.policia.gov.co/noticias"
    r_noticias=requests.get(noticia, verify=False, timeout=10)
    sel=Selector(r_noticias.text)

    descripcion = sel.css("div.views-field.views-field-field-resumen span.field-content ::text").extract()
    descripcion_corregida = limpieza_descripcion(descripcion)
    catego = []
    tipo = []
    for x in descripcion_corregida:
        vect_text1 = lemant(x)
        predi_categ = predCateg.predict([vect_text1])[0]
        predi_type = predType.predict([vect_text1])[0] 
        catego.append(predi_categ)
        tipo.append(predi_type)

    noticias = {}
    noticias['title'] = sel.css("div.views-field.views-field-title a::text, span.views-field.views-field-title a::text").extract()
    noticias['description'] = descripcion_corregida
    noticias['category']= sel.css("span.views-field.views-field-field-noticia-ciudad span.field-content::text").extract()
    noticias['category'] = np.insert(noticias['category'], 0, np.array(('Sin categoria')), 0)
    noticias['category'] = noticias['category'].tolist()
    noticias['link'] = 'https://www.policia.gov.co/'
    noticias['pubDate'] = sel.css("div.views-field.views-field-created span.field-content ::text").extract()
    noticias['medium']="Policia Nacional"
    #--  Predict
    noticias['predi_type'] = tipo
    noticias['predi_categ'] = catego

except requests.exceptions.Timeout:
    print ('Timeout occurred')

df_policia = pd.DataFrame(noticias, columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])


# In[56]:


# Unidad de Victimas 
try:
    noticia = "https://www.unidadvictimas.gov.co/es/sala-de-prensa/noticias"
    r_noticias=requests.get(noticia, verify=False, timeout=20)
    sel=Selector(r_noticias.text)
    
    descripcion = sel.css("h5.tituloh5 a::text").extract()
    catego = []
    tipo = []
    for x in descripcion:
        vect_text1 = lemant(x)
        predi_categ = predCateg.predict([vect_text1])[0]
        predi_type = predType.predict([vect_text1])[0] 
        catego.append(predi_categ)
        tipo.append(predi_type)

    noticias = {}
    noticias['title'] = descripcion
    noticias['description'] = descripcion
    noticias['category'] = sel.css("h6.ciudadfecha::text").extract()
    noticias['category'] = [i.split(' |')[0] for i in noticias['category']]
    noticias['link'] = 'https://www.unidadvictimas.gov.co/es/sala-de-prensa/noticias'
    noticias['pubDate'] = sel.css("h6.ciudadfecha::text").extract()
    noticias['pubDate'] = [i.split('| ')[-1] for i in noticias['pubDate']]
    noticias['medium'] = 'Unidad de Victimas'
    #--  Predict
    noticias['predi_type'] = tipo
    noticias['predi_categ'] = catego
    

except requests.exceptions.Timeout:
    print ('Timeout occurred')
    
    
df_unidadvictimas = pd.DataFrame(noticias, columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])


# In[57]:


# Fuerza Aerea Colombiana 
try:
    noticia = "https://www.fac.mil.co/informacion-prensa"
    r_noticias=requests.get(noticia, timeout=20)
    sel=Selector(r_noticias.text)

    descripcion = sel.css("div.views-field.views-field-title span.field-content a::text").extract()
    #descripcion = sel.css("div.views-field.views-field-body p:last-child ::text").extract()
    catego = []
    tipo = []
    for x in descripcion:
        vect_text1 = lemant(x)
        predi_categ = predCateg.predict([vect_text1])[0]
        predi_type = predType.predict([vect_text1])[0] 
        catego.append(predi_categ)
        tipo.append(predi_type)

    noticias = {}
    noticias['title'] = descripcion
    noticias['description'] = descripcion
    noticias['category']= 'Información y prensa'
    noticias['link'] = 'https://www.fac.mil.co/informacion-prensa'
    noticias['medium'] = "Fuerza Aerea Colombiana"
    noticias['pubDate'] = sel.css("div.views-field.views-field-created span.field-content ::text").extract()
    noticias['pubDate'] = [i[3:-2] for i in noticias['pubDate']]
    #--  Predict
    noticias['predi_type'] = tipo
    noticias['predi_categ'] = catego 
    
except requests.exceptions.Timeout:
    print ('Timeout ocurred')

df_fuerza = pd.DataFrame(noticias, columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])


# In[58]:


# Fuentes que tiene fallas en sus paginas web. Pueden estar activas o no.
# Ejercito
def fuentes_ejercito (periodico_url):
    try:
        r_noticias=requests.get(periodico_url, verify=False, timeout=20)
        sel=Selector(r_noticias.text)
        
        descripcion = sel.css("h5>a::text").extract()
        catego = []
        tipo = []
        for x in descripcion:
            vect_text1 = lemant(x)
            predi_categ = predCateg.predict([vect_text1])[0]
            predi_type = predType.predict([vect_text1])[0] 
            catego.append(predi_categ)
            tipo.append(predi_type)
       
        noticias = {}
        noticias['title'] = descripcion
        noticias['description'] = descripcion
        #noticias['description']= sel.css("p.listaEntradilla ::text").extract()
        noticias['category']= sel.css("div.titulo-interna::text").extract()
        noticias['pubDate'] = sel.css("p.s_fecha::text").extract()
        noticias['link'] = periodico_url
        noticias['medium']="Ejercito Militar"
        #--  Predict
        noticias['predi_type'] = tipo
        noticias['predi_categ'] = catego 

        df_militar = pd.DataFrame(noticias,columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])
        return df_militar
        
    except requests.exceptions.Timeout:
        print ('Timeout ocurred')
        
df_ejercito_noticias = fuentes_ejercito("https://www.ejercito.mil.co/informes_noticias/noticias")
df_ejercito_actualidad = fuentes_ejercito("https://www.ejercito.mil.co/informes_noticias/actualidad")


# In[59]:


# Armada
def fuentes_armada (periodico_url):
    try:
        r_noticias=requests.get(periodico_url,  timeout=20)
        sel=Selector(r_noticias.text)

        descripcion = sel.css("span>a::text").extract()[:8]
        catego = []
        tipo = []
        for x in descripcion:
            vect_text1 = lemant(x)
            predi_categ = predCateg.predict([vect_text1])[0]
            predi_type = predType.predict([vect_text1])[0] 
            catego.append(predi_categ)
            tipo.append(predi_type)

        noticias = {}
        noticias['title'] = sel.css("span>a::text").extract()[:8]
        noticias['description']= descripcion
        noticias['category']= 'Armada'
        noticias['pubDate'] = dt_string
        noticias['link'] = "https://www.armada.mil.co/"
        noticias['medium']="Fuerzas Armadas de Colombia"
        #--  Predict
        noticias['predi_type'] = tipo
        noticias['predi_categ'] = catego 

        armada = pd.DataFrame(noticias,columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_categ','predi_type'])
        return armada

    except requests.exceptions.Timeout:
        print ('Timeout occurred')
    
df_armada = fuentes_armada("https://www.armada.mil.co/")


# In[60]:


# El Tiempo

def fuentes_tiempo(periodico_url):
    r_noticias = requests.get(periodico_url)
    sel=Selector(r_noticias.text)
    soup = BeautifulSoup(r_noticias.content, 'html.parser')

    descripcion = soup.findAll('div', class_='lead')
    descripcion = [i.get_text().strip('\n') for i in descripcion]
    l = len(descripcion)
    titulo =soup.findAll('h3', class_='titulo')
    titulo=[i.get_text().strip('\n') for i in titulo][:l] 
    categoria = soup.findAll('h1', class_='oculto')
    categoria = [i.get_text() for i in categoria][0]
    enlace = periodico_url
    medio = "El Tiempo"
    fecha = sel.css("div.apertura-seccion meta, div.seccion-fecha meta").extract()
    fecha = [i.split() for i in fecha]
    fecha = pd.DataFrame(fecha)
    fecha = fecha.drop(fecha[fecha[1]!='itemprop="datePublished"'].index)
    fecha = fecha[2]
    fecha = [i.split('=')[-1][1:-2] for i in fecha]
    #fecha = pd.to_datetime(fecha[0:], errors='coerce')
    #fecha = fecha.dropna()
 
    catego = []
    tipo = []
    for x in titulo:
        vect_text1 = lemant(x)
        predi_categ = predCateg.predict([vect_text1])[0]
        predi_type = predType.predict([vect_text1])[0]
        catego.append(predi_categ)
        tipo.append(predi_type)
            
    noticias = {}
    noticias['title'] = titulo
    noticias['description']= descripcion
    noticias['category']= categoria
    noticias['pubDate'] = fecha
    noticias['link'] = enlace
    noticias['medium']= medio
    #--  Predict
    noticias['predi_type'] = tipo
    noticias['predi_categ'] = catego
            
    df = pd.DataFrame(noticias,columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])
    df= df.replace('', 'Noticia sin descripción')
    return df

def fuentes_tiempo_2 (periodico_url):
    
    r_noticias=requests.get(periodico_url)
    sel=Selector(r_noticias.text)
    
    fecha = sel.css("div.modulo-mas-default meta, div.seccion-fecha meta, div.listing.view-grid meta").extract()
    fecha = [i.split() for i in fecha]
    fecha = pd.DataFrame(fecha)
    fecha = fecha.drop(fecha[fecha[1]!='itemprop="datePublished"'].index)
    fecha = fecha[2]
    fecha = [i.split('=')[-1][1:-2] for i in fecha]
    #fecha = pd.to_datetime(fecha[0:], errors='coerce')
    #fecha = fecha.dropna()
    descripcion = sel.css('h3>a::text, div.lead a::text').extract()
    descripcion_corregida = limpieza_descripcion(descripcion)
    catego = []
    tipo = []
    for x in descripcion_corregida:
        vect_text1 = lemant(x)
        predi_categ = predCateg.predict([vect_text1])[0]
        predi_type = predType.predict([vect_text1])[0] 
        catego.append(predi_categ)
        tipo.append(predi_type)
    
    noticias = {}
    noticias['title'] = sel.css('h3>a::text, h2>a::text').extract()
    noticias['title'] = list(map(lambda d: d.replace('\n', ' '), noticias['title']))
    noticias['title'] = [i.strip('\n')for i in noticias['title']]
    ## no cuenta con descripcion, se podria usar en descripcion la ruta de titulo
    ## de esta manera se puede evaluar si hay una noticia que requiera validación
    noticias['description']= descripcion_corregida       
    noticias['category']= sel.css("h1.titulo ::text").extract_first()
    noticias['link'] = periodico_url
    noticias['pubDate'] = fecha
    noticias['medium']="El Tiempo"
    #--  Predict
    noticias['predi_type'] = tipo
    noticias['predi_categ'] = catego

    df = pd.DataFrame(noticias,columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])
    return df

def fuente_bogota(periodico_url):
    r_noticias = requests.get(periodico_url)
    sel=Selector(r_noticias.text)
     
    titulo = sel.css("section.col0 h3.title-container a::text").extract()
    titulo = [i.strip('\n') for i in titulo]
    titulo = pd.DataFrame(titulo)
    titulo = titulo.replace('', 'NaN')
    titulo = titulo.drop(titulo[titulo[0]=='NaN'].index)
    titulo = titulo.values.tolist()
    titulo = [item for lista in titulo for item in lista]
    descripcion = titulo
    fecha = sel.css("section.col0 div meta").extract()
    fecha = [i.split() for i in fecha]
    fecha = pd.DataFrame(fecha)
    fecha = fecha.drop(fecha[fecha[1]!='itemprop="datePublished"'].index)
    fecha = fecha[2]
    fecha = [i.split('=')[-1][1:-2] for i in fecha]
    #fecha = pd.to_datetime(fecha[0:], errors='coerce')
    #fecha = fecha.dropna()
    categoria = 'Bogota'
    enlace = periodico_url
    medio = "El Tiempo"
   
    catego = []
    tipo = []
    for x in descripcion:
        vect_text1 = lemant(x)
        predi_categ = predCateg.predict([vect_text1])[0]
        predi_type = predType.predict([vect_text1])[0]
        catego.append(predi_categ)
        tipo.append(predi_type)
            
    noticias = {}
    noticias['title'] = titulo
    noticias['description']= titulo
    noticias['category']= categoria
    noticias['pubDate'] = fecha
    noticias['link'] = enlace
    noticias['medium']= medio
    #--  Predict
    noticias['predi_type'] = tipo
    noticias['predi_categ'] = catego
            
    df = pd.DataFrame(noticias,columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])
    return df

fuente_bogota = fuente_bogota('https://www.eltiempo.com/bogota')
fuente_medellin = fuentes_tiempo('https://www.eltiempo.com/colombia/medellin')
fuente_otras_ciudades = fuentes_tiempo('https://www.eltiempo.com/colombia/otras-ciudades')
fuente_santander = fuentes_tiempo('https://www.eltiempo.com/colombia/santander')
fuente_barranquilla = fuentes_tiempo('https://www.eltiempo.com/colombia/barranquilla')
fuente_cali = fuentes_tiempo('https://www.eltiempo.com/colombia/cali')
fuente_boyaca = fuentes_tiempo_2('https://www.eltiempo.com/noticias/boyaca')
fuente_meta = fuentes_tiempo_2('https://www.eltiempo.com/noticias/meta')

df_noticias_ElTiempo = pd.concat([fuente_bogota, fuente_medellin, fuente_otras_ciudades, fuente_santander, fuente_barranquilla, fuente_cali, fuente_boyaca, fuente_meta])


# In[61]:


# La voz del Cinaruco

noticia_lavoz = "https://lavozdelcinaruco.com/"
r_noticias=requests.get(noticia_lavoz)
sel=Selector(r_noticias.text)

descripcion = sel.css('article.col-xs-12.col-sm-4.col-md-4 p::text, div.well p::text').extract()
descripcion = limpieza(descripcion)
descripcion = pd.DataFrame(descripcion)
descripcion = descripcion.drop(descripcion[descripcion[0]==''].index)
descripcion = descripcion.values.tolist()
descripcion = [item for lista in descripcion for item in lista]
catego = []
tipo = []

for x in descripcion:
    vect_text1 = lemant(x)
    predi_categ = predCateg.predict([vect_text1])[0]
    predi_type = predType.predict([vect_text1])[0]
    catego.append(predi_categ)
    tipo.append(predi_type)

noticias = {}
noticias['title'] = sel.css("h2 a::text ,h3 a ::text").extract()
noticias['description'] = descripcion
noticias['pubDate'] = dt_string
noticias['link'] = "https://lavozdelcinaruco.com/"
noticias['category'] = "Noticias"
noticias['medium'] = "La Voz del Cinaruco"
#--  Predict  
noticias['predi_type'] = tipo
noticias['predi_categ'] = catego
        
df_lavoz = pd.DataFrame(noticias,columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])


# In[62]:


# La Patria 
def fuentes_la_patria (periodico_url):
    r_noticias=requests.get(periodico_url)
    sel=Selector(r_noticias.text)

    descripcion = sel.css("span.field-content a ::text").extract()  
    catego = []
    tipo = []

    for x in descripcion:
        vect_text1 = lemant(x)
        predi_categ = predCateg.predict([vect_text1])[0]
        predi_type = predType.predict([vect_text1])[0]
        catego.append(predi_categ)
        tipo.append(predi_type)
       
    noticias = {}
    noticias['title'] = descripcion
    noticias['description'] = descripcion
    noticias['pubDate'] = dt_string
    noticias['category'] = sel.css("h1 span ::text").extract()[0]
    noticias['link'] = periodico_url
    noticias['medium'] = "La Patria"
    #--  Predict  
    noticias['predi_type'] = tipo
    noticias['predi_categ'] = catego
    
    df_la_patria=pd.DataFrame(noticias,columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])
    return df_la_patria

fuente_manizales = fuentes_la_patria('https://www.lapatria.com/Manizales')
fuente_caldas = fuentes_la_patria('https://www.lapatria.com/caldas')
fuente_nacional = fuentes_la_patria('https://www.lapatria.com/nacional')


df_la_patria = pd.concat([fuente_manizales, fuente_caldas, fuente_nacional])


# In[63]:


# El Liberal - El diario del cauca
def fuentes_diario_cauca (periodico_url):
    r_noticias=requests.get(periodico_url)
    sel=Selector(r_noticias.text)
    
    descripcion = sel.css("div.region.region-content div.field-item.even::text").extract()
    descripcion = limpieza_descripcion(descripcion)
    catego = []
    tipo = []
    for x in descripcion:
        vect_text1 = lemant(x)
        predi_categ = predCateg.predict([vect_text1])[0]
        predi_type = predType.predict([vect_text1])[0]
        catego.append(predi_categ)
        tipo.append(predi_type)
    
    noticias = {}
    noticias['title'] = sel.css("div.region.region-content h2 a::text").extract()
    noticias['description'] = descripcion
    noticias['pubDate'] = sel.css("div.region.region-content div.content div.field.field-datetime div.field-items div.field-item::text").extract()
    noticias['pubDate'] = [i.split(' -')[0] for i in noticias['pubDate']]
    noticias['category'] = sel.css("h1.title ::text").extract()[0]
    noticias['medium'] = "Diario del Cauca"
    noticias['link'] = periodico_url
    #--  Predict  
    noticias['predi_type'] = tipo
    noticias['predi_categ'] = catego
    
    df_diario_cauca = pd.DataFrame(noticias,columns=['title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])
    return df_diario_cauca

cauca_judicial = fuentes_diario_cauca("https://diariodelcauca.com.co/noticias/judicial")
cauca_local = fuentes_diario_cauca("https://diariodelcauca.com.co/noticias/local")

df_diario_del_cauca = pd.concat([cauca_judicial, cauca_local ])


# In[64]:


# El Heraldo 
def fuentes_el_heraldo (periodico_url):
    r_noticias=requests.get(periodico_url)
    sel=Selector(r_noticias.text)
    
    descripcion = sel.css(" div.text h1 a ::text").extract()
    catego = []
    tipo = []
    for x in descripcion:
        vect_text1 = lemant(x)
        predi_categ = predCateg.predict([vect_text1])[0]
        predi_type = predType.predict([vect_text1])[0]
        catego.append(predi_categ)
        tipo.append(predi_type)
        
    noticias = {}
    noticias['title'] = descripcion
    noticias['description'] = descripcion
    noticias['pubDate'] = sel.css("div.datos time::text").extract()
    noticias['medium'] = "El Heraldo"
    noticias['link'] = periodico_url
    #--  Predict  
    noticias['predi_type'] = tipo
    noticias['predi_categ'] = catego
            
    df_elheraldo=pd.DataFrame(noticias,columns=['id_not','title', 'description', 'pubDate', 'link', 'category','medium','processDate','predi_type','predi_categ'])
    return df_elheraldo

fuente_bolivar = fuentes_el_heraldo('https://www.elheraldo.co/bolivar')
fuente_cesar = fuentes_el_heraldo('https://www.elheraldo.co/cesar')
fuente_cordoba = fuentes_el_heraldo('https://www.elheraldo.co/cordoba')
fuente_guajira = fuentes_el_heraldo('https://www.elheraldo.co/la-guajira')
fuente_magdalena = fuentes_el_heraldo('https://www.elheraldo.co/magdalena')
fuente_sucre = fuentes_el_heraldo('https://www.elheraldo.co/sucre')
fuente_san_andres = fuentes_el_heraldo('https://www.elheraldo.co/san-andres')
fuente_local = fuentes_el_heraldo('https://www.elheraldo.co/local')
fuente_judicial = fuentes_el_heraldo('https://www.elheraldo.co/judicial')


df_el_heraldo = pd.concat([fuente_bolivar, fuente_cesar, fuente_cordoba, fuente_guajira, fuente_magdalena, fuente_sucre, fuente_san_andres, fuente_local, fuente_judicial])


# ## Union de Periodicos - Un solo DataFrame

# In[65]:


periodicos_union = [df_noticias_PrensaLibre, df_hsb_noticias, df_diario_pereira, df_noticias_nuevodia, df_noticias_ElTiempo, 
                    df_noticias_elpais, df_guajira_hoy, df_la_nacion, df_noticias_pilon, df_noticias_huila, df_rss_elsiglo,
                    df_diario_del_sur, df_putumayo, df_cronica_quindio, df_extra_judicial, df_lavoz, df_la_patria, df_diario_del_cauca,
                    df_el_heraldo, df_policia, df_unidadvictimas, df_fuerza, df_ejercito_noticias, df_ejercito_actualidad, df_armada]
periodicos_union_df = pd.concat(periodicos_union)
periodicos_union_df = periodicos_union_df.assign(processDate=dt_string)
periodicos_union_df = periodicos_union_df.reset_index(drop=True)


# In[66]:


df_periodicos_limpios = periodicos_union_df.drop(periodicos_union_df[periodicos_union_df['predi_type']=='FUERA_RANGO'].index)
df_periodicos_limpios = df_periodicos_limpios.reset_index(drop=True)


# In[67]:


periodicos_union_df.predi_type.value_counts()


# In[68]:


df_periodicos_limpios.predi_type.value_counts()


# In[69]:


df_periodicos_limpios.to_csv('C:/Users/harold.patino/Documents/Periodicos/DeVops/Noticias.txt', sep='|', encoding='utf-8-sig')

