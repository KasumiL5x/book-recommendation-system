# https://stackoverflow.com/questions/41487473/nameerror-name-request-is-not-defined
# https://stackoverflow.com/questions/34704997/jquery-autocomplete-in-flask
# https://kite.com/python/docs/flask.jsonify

import flask
from api import BookSimilarity

app = flask.Flask(__name__)
booksim = BookSimilarity()

@app.route('/')
def index():
	return flask.render_template('index.html')

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
	search = flask.request.args.get('q')
	filtered_books = list(booksim.search(search)['title'].values)
	return flask.jsonify(matching_results=filtered_books)

@app.route('/recommend')
def recommend():
	# Dynamic page help:
	# https://stackoverflow.com/questions/40963401/flask-dynamic-data-update-without-reload-page/40964086
	
	searchText = flask.request.args.get('jsdata')

	output = []
	if searchText:
		print(f'Search text: {searchText}')
		results = booksim.recommend(searchText)
		if results is not None:
			output = results.title.values
			print(output)

	# TODO: Convert a fuller version to JSON rather than just an array (title, url, etc.) and render as a table instead.
	# https://stackoverflow.com/questions/48050769/pandas-dataframe-to-flask-template-as-a-json
	return flask.render_template('results.html', recommendations=output)