
from collections import Counter, defaultdict
from model import SearchTerm, BookInfo, session
import re

import json

COLUMNS_TO_INDEX = (
    'ean',
    'isbn',
    'title',
    'author',
    'genre',
    'editorial_review',
)


def get_tokens_from_book_info(book_info):
    '''
    This function makes a list of lowercased word tokens out of
    a book's EAN, ISBN, title, author, genre and editorial review.
    Tokens can be repeats.
    '''
    tokens = []
    for column in COLUMNS_TO_INDEX:
        # getattr is a shortcut for 'info.<attribute name>
        data = getattr(book_info, column)
        tokens += get_tokens_from_string(data)

    return tokens


def get_tokens_from_string(data):
    '''
    This function cleans up the tokens so formatting doesn't
    throw off search results.
    '''
    tokens = []

    if data:
        lowercased_words = data.lower()
        # remove anything that does't match a word char or a number
        lowercased_words = re.sub(r'[^a-z0-9-]', ' ', lowercased_words)

        for token in lowercased_words.split(' '):
            if token:
                tokens.append(token)

    return tokens


def recreate_index():
    '''
    This function indexes the book_info table of the database.
    I'm implimenting tf-idf functionality, so I save the number
    of documents in which the term shows up, and I also save a
    record of the specific documents that contain the term.
    '''

    book_infos = BookInfo.query.all()
    freq_by_id_by_token = defaultdict(Counter)

    for info in book_infos:
        tokens = get_tokens_from_book_info(info)

        for token in tokens:
            freq_by_id_by_token[token][info.id] += 1

    # deletes all search terms before recreating index
    SearchTerm.query.delete()

    for token, frequency_by_id in freq_by_id_by_token.items():

        search_term = SearchTerm(
            token=token,
            num_results=len(frequency_by_id),
            # creates a json string from the `frequency_by_id` dict
            document_ids=json.dumps(frequency_by_id),
        )

        session.add(search_term)

    session.commit()


def index_new_book_info(book_info):
    '''
    This function updates a dictionary containing all tokens for a book.
    New search terms are saved to the SearchTerm table. The key is the
    token, the value is a list of document IDs that contain the token.
    '''

    book_info_ids_by_token = {}

    tokens = get_tokens_from_book_info(book_info)

    for token in tokens:
        if not token in book_info_ids_by_token:
            book_info_ids_by_token[token] = []
        book_info_ids_by_token[token].append(book_info.id)

    for token, book_ids in book_info_ids_by_token.items():

        # TODO: check the DB first before creating new search term
        search_term = SearchTerm(
            token=token,
            num_results=len(book_ids),
            # creates a json string from the book_ids array
            document_ids=json.dumps(book_ids),
        )

        session.add(search_term)

    session.commit()

    return book_info_ids_by_token
