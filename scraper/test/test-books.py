"""
An offline test for processing books to avoid requesting the host website too often.
"""

import os
import re
import scrapy
import pandas as pd

def process_book_description(spans):
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

def parse_book(filename):
	with open(filename, 'r') as file:
		selector = scrapy.Selector(text=file.read())
	#end

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
	book_avg_rating = selector.css('span[itemprop="ratingValue"]::text').get().strip()

	# Number of ratings and reviews are deep in `#bookMeta` in impossible to differentiate tags.
	# Unfortunately the only real solution here is to get all children and find which has `ratings` and `reviews` in it!
	book_metas = selector.css('#bookMeta > a::text').getall()
	#
	# Ratings (contains `ratings`).
	num_ratings_idx = [i for i,s in enumerate(book_metas) if 'ratings' in s]
	if len(num_ratings_idx):
		book_num_ratings = book_metas[num_ratings_idx[0]].replace('\n', '').replace(',', '').replace('ratings', '').strip()
	# Reviews (contains `reviews`).
	num_reviews_idx = [i for i,s in enumerate(book_metas) if 'reviews' in s]
	if len(num_reviews_idx):
		book_num_reviews = book_metas[num_reviews_idx[0]].replace('\n', '').replace(',', '').replace('reviews', '').strip()
	#end

	# Genre(s).
	book_genres = selector.css('div.left > a.bookPageGenreLink::text').getall()

	# Description (see function comments).
	desc_texts = process_book_description(selector.xpath('//*[@id="description"]/span[contains(@style, "display:none")]/node()').getall())
	book_description = ' '.join(desc_texts)
	# The `display:none` span is only present when the preview needs expanding. If the preview is small enough, it's just
	# a regular span. So, repeat the above process for a normal span if the text is empty
	if not len(book_description):
		desc_texts = process_book_description(selector.xpath('//*[@id="description"]/span/node()').getall())
		book_description = ' '.join(desc_texts)


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

	# Concat with the main df (would do in normally).
	# all_books_df = pd.concat([all_books_df, book_df], sort=False)


	# Debug print.
	print(f'Title: {book_title}')
	print(f'Original title: {book_orig_title}')
	print(f'Series: {book_series}')
	print(f'Language: {book_language}')
	print(f'Authors: {book_authors}')
	print(f'Average rating: {book_avg_rating}')
	print(f'No. ratings: {book_num_ratings}')
	print(f'No. reviews: {book_num_reviews}')
	print(f'Genres: {book_genres}')
	print(f'Description: {book_description}')
	print()
#end

# parse_book('./book_1.html')
# parse_book('./book_2.html')
# parse_book('./book_3.html')
# parse_book('./book_4.html')
# parse_book('./book_5.html')
# parse_book('./book_6.html')
parse_book('./book_7.html')