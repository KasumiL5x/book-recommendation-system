# https://stackoverflow.com/questions/41487473/nameerror-name-request-is-not-defined
# https://stackoverflow.com/questions/34704997/jquery-autocomplete-in-flask
# https://kite.com/python/docs/flask.jsonify

import flask

app = flask.Flask(__name__)

@app.route('/')
def index():
	return flask.render_template('index.html')

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
	search = flask.request.args.get('q')
	books = ["The Canterbury Tales", "The Things They Carried", "Cloud Atlas", "The Eyre Affair", "The Corrections", "On Writing: A Memoir of the Craft", "The Tin Drum", "Where the Red Fern Grows", "Stones from the River", "Under the Never Sky", "The Warded Man", "The Sirens of Titan", "Lisey's Story", "The King of Attolia", "Nevermore", "London", "As You Like It", "I've Got Your Number", "Carpe Corpus", "The Runaway Bunny", "Wyrd Sisters"]
	filtered_books = [b for b in books if search in b.lower()]
	return flask.jsonify(matching_results=filtered_books)