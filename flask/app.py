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