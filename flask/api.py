import pickle
import pandas as pd

class BookSimilarity(object):
	def __init__(self):
		self.__load_data()

	def __load_data(self):
		self.__book_data = pickle.load(open('./data/book_data.pickle', 'rb'))
		print('Loaded book data.')

	def search(self, query):
		return self.__book_data.loc[self.__book_data['title'].str.contains(query, case=False)]

# Offline test.
# bs = BookSimilarity()
# res = bs.search('hitch')
# print(res.title.values)