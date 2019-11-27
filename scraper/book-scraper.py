"""
GoodReads `Best Books Ever` scraper
Daniel Green / KasumiL5x

Purpose:
	This spider crawls the `Best Books Ever` user list on GoodReads (https://www.goodreads.com/list/show/1.Best_Books_Ever).
	It pulls metadata about each book in the list, which as of 25 Nov 19 has almost 57,000 books!

Notes:
	Lucky for us, the URL format for a list's pages is [link]?page=x, where x is the page number.
	The div with ID `all_votes` contains a table, which further contains each book.
	The GoodReads development team have done well by using both the Book and Person schema standards for names (http://schema.org/Book and http://schema.org/Person).
	For each book, we will open the book's page and pull more information about the book.
"""

import os
import re
import pandas as pd
import scrapy
from scrapy.crawler import CrawlerProcess

class GoodReadsSpider(scrapy.Spider):
	name = 'goodreads_spider'
	download_delay = 0.25 # Avoid requesting too quickly.

	def start_requests(self):
		for page_id in range(START_PAGE, END_PAGE+1):
			page_url = f'https://www.goodreads.com/list/show/1.Best_Books_Ever?page={page_id}'
			yield scrapy.Request(url=page_url, callback=self.parse_page)
		#end
	#end

	def parse_page(self, selector):
		# Instead of parsing the hierarchy, just pull all `bookTitle` anchors, which are the titles/links of the books in the list.
		all_book_titles = selector.css('a.bookTitle')
		for curr_book in all_book_titles:
			book_link = curr_book.attrib['href']
			book_url = f'https://www.goodreads.com{book_link}'
			yield selector.follow(url=book_url, callback=self.parse_book)
		#end
	#end

	def parse_book(self, selector):
		# Values we will fill in.
		book_title = None
		book_orig_title = None # Title in the original language.
		book_series = None
		book_language = None
		book_authors = []
		book_avg_rating = None
		book_num_ratings = None
		book_num_reviews = None
		book_genres = []
		book_description = ''

		# Regular title (usually in English).
		book_title = selector.css('h1#bookTitle::text').get()
		book_title = None if book_title is None else book_title.strip()

		# Each book has a metadata listing, but it's quite difficult to parse, so grab it all.
		book_data = selector.css('#bookDataBox > div.clearFloats')
		for data in book_data:
			# What and how we parse differs based on the value of this.
			row_title = data.css('.infoBoxRowTitle::text').get()

			# Original book title.
			if 'Original Title' == row_title:
				book_orig_title = data.css('.infoBoxRowItem::text').get()
				book_orig_title = None if book_orig_title is None else book_orig_title.strip() # Cleanup.
			#end

			# Series.
			if 'Series' == row_title:
				book_series = data.css('.infoBoxRowItem > a::text').get()
				hash_idx = book_series.find('#')
				if hash_idx != -1:
					book_series = book_series[:hash_idx-1]
				#end
			#end

			# Language.
			if 'Edition Language' == row_title:
				book_language = data.css('.infoBoxRowItem::text').get()
				book_language = None if book_language is None else book_language.strip()
			#end
		#end

		# Author(s).  Multiple can be listed.
		for author in selector.css('.authorName__container'):
			author_name = author.css('a > span::text').get()
			author_role = author.css('.role::text').get()
			# Add either just the author or combined with their role.
			book_authors.append(author_name if author_role is None else ' '.join([author_name, author_role]))
		#end

		# Average rating (?/5).
		book_avg_rating = selector.css('span[itemprop="ratingValue"]::text').get()
		if book_avg_rating != None:
			book_avg_rating = book_avg_rating.strip()

		# Number of ratings and reviews are deep in `#bookMeta` in impossible to differentiate tags.
		# Unfortunately the only real solution here is to get all children and find which has `ratings` and `reviews` in it!
		book_metas = selector.css('#bookMeta > a::text').getall()
		#
		# Ratings (contains `ratings`).
		num_ratings_idx = [i for i,s in enumerate(book_metas) if ('ratings' in s or 'rating' in s)]
		if len(num_ratings_idx):
			book_num_ratings = book_metas[num_ratings_idx[0]].replace('\n', '').replace(',', '').replace('ratings', '').replace('rating', '').strip()
		# Reviews (contains `reviews`).
		num_reviews_idx = [i for i,s in enumerate(book_metas) if ('reviews' in s or 'review' in s)]
		if len(num_reviews_idx):
			book_num_reviews = book_metas[num_reviews_idx[0]].replace('\n', '').replace(',', '').replace('reviews', '').replace('review', '').strip()
		#end

		# Genre(s).
		book_genres = selector.css('div.left > a.bookPageGenreLink::text').getall()

		# Description (see function comments).
		desc_texts = self.process_book_description(selector.xpath('//*[@id="description"]/span[contains(@style, "display:none")]/node()').getall())
		book_description = ' '.join(desc_texts)
		# The `display:none` span is only present when the preview needs expanding. If the preview is small enough, it's just
		# a regular span. So, repeat the above process for a normal span if the text is empty
		if not len(book_description):
			desc_texts = self.process_book_description(selector.xpath('//*[@id="description"]/span/node()').getall())
			book_description = ' '.join(desc_texts)


		## Error checking.
		# Needs title.
		if None == book_title:
			print(f'Error: Missing book title ({selector.url}).')
			return
		# Original title.
		if None == book_orig_title:
			print(f'Warning: Missing book original title ({selector.url}).')
		# Series.
		if None == book_series:
			print(f'Warning: Book missing series ({selector.url}).')
		# Language.
		if None == book_language:
			print(f'Warning: Book missing language ({selector.url}).')
		# Authors.
		if not len(book_authors):
			print(f'Warning: Book missing authors ({selector.url}).')
		# Average rating.
		if None == book_avg_rating:
			print(f'Warning: Book missing average rating ({selector.url}).')
		# Number of ratings.
		if None == book_num_ratings:
			print(f'Warning: Book missing number of ratings ({selector.url}).')
		# Number of reviews.
		if None == book_num_reviews:
			print(f'Warning: Book missing number of reviews ({selector.url}).')
		# Genres.
		if not len(book_genres):
			print(f'Warning: Book missing genres ({selector.url}).')
		# Description.
		if not len(book_description):
			print(f'Warning: Book missing description ({selector.url}).')

		# Fill in the df.
		book_df = pd.DataFrame()
		book_df['title'] = [book_title]
		book_df['original_title'] = [book_orig_title]
		book_df['series'] = [book_series]
		book_df['language'] = [book_language]
		book_df['authors'] = ','.join(book_authors)
		book_df['avg_rating'] = book_avg_rating
		book_df['num_ratings'] = book_num_ratings
		book_df['num_reviews'] = book_num_reviews
		book_df['genres'] = ','.join(book_genres)
		book_df['description'] = book_description
		book_df['url'] = selector.url # Easier to debug.

		# Append to the master df.
		global all_books_df
		all_books_df = pd.concat([all_books_df, book_df], sort=False)
	#end

	def process_book_description(self, spans):
		# This is a strange one. There's a div w/ the ID `description` which contains a bunch of `span` tags.
		# However, one is the preview before pressing `...more`, and the other is hidden (`display:none`).
		# Inside the span is arbitrary HTML but it seems only one layer deep.  So, I'm processing all of the strings and then
		# pooling them together.  I'd do it in one line but there's some oddities that mean it must be looped.
		texts = []

		for desc_span in spans:
			desc_text = desc_span.strip()
			# Remove newlines.
			desc_text = desc_text.replace('\n', '')
			# Remove tabs in case I store in TSV.
			desc_text = desc_text.replace('\t', ' ')
			# Remove HTML tags (a bit risky but seems to be okay).
			desc_text = re.sub(r"<[^>]*>", '', desc_text)

			# Only add if not empty as some nodes are just pure HTML (would add extra spaces when concatenating).
			if len(desc_text):
				texts.append(desc_text)
		#end

		return texts
	#end
#end

# Which page to begin and end at.  You could always automate the end but I want a manual range.
START_PAGE = 1
END_PAGE = 100
# Master DF with all books for the given range.
all_books_df = pd.DataFrame()

process = CrawlerProcess()
process.crawl(GoodReadsSpider)
process.start()

# Write a TSV.
output_tsv = f'./output/pages-{START_PAGE}-{END_PAGE}.tsv'
all_books_df.to_csv(output_tsv, index=False, sep='\t')

# Write a CSV.
output_csv = f'./output/pages-{START_PAGE}-{END_PAGE}.csv'
all_books_df.to_csv(output_csv, index=False)