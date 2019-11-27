"""
An offline test for processing pages to avoid requesting the host website too often.
"""

import os
import scrapy

def parse_page(filename):
	with open(filename, 'r') as file:
		selector = scrapy.Selector(text=file.read())

	# Instead of parsing the hierarchy, just pull all `bookTitle` anchors, which are the titles/links of the books in the list.
	all_book_titles = selector.css('a.bookTitle')
	for curr_book in all_book_titles:
		book_link = curr_book.attrib['href']
		book_url = f'https://www.goodreads.com{book_link}'
		print(book_url)
		# parseBook(book_url) etc.
#end

parse_page('./page_1.html')