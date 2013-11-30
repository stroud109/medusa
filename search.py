
from model import SearchTerm, BookInfo, session

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
    tokens = []
    for column in COLUMNS_TO_INDEX:
        data = getattr(book_info, column)
        # getattr is a shortcut for 'info.<attribute name>
        if data:
            lowercased_words = data.lower()

            for token in lowercased_words.split(' '):
                token = token.replace(r'[^\w\d]', '')
                # remove anything that does't match a word char or a number
                tokens.append(token)

    return tokens


def recreate_index():
    '''
    This function indexes the book_info table of the database
    I'd eventually like to impliment tf-idf functionality, thus
    I am not deduplicating the docoment_ids for each SearchTerm
    http://en.wikipedia.org/wiki/Tf%E2%80%93idf
    '''

    book_infos = BookInfo.query.all()
    book_info_ids_by_token = {}

    for info in book_infos:
        tokens = get_tokens_from_book_info(info)

        for token in tokens:
            if not token in book_info_ids_by_token:
                book_info_ids_by_token[token] = []
            book_info_ids_by_token[token].append(info.id)
            # use set to avoid redundant keys

    # deleting all search terms before recreating index
    SearchTerm.query.delete()

    for token, book_ids in book_info_ids_by_token.items():

        search_term = SearchTerm(
            token=token,
            num_results=len(book_ids),
            # creates a json string from the book_ids array
            document_ids=json.dumps(book_ids),
        )

        session.add(search_term)

    session.commit()

    return book_info_ids_by_token


def index_new_book_info(book_info):

    book_info_ids_by_token = {}

    tokens = get_tokens_from_book_info(book_info)

    for token in tokens:
        if not token in book_info_ids_by_token:
            book_info_ids_by_token[token] = []
        book_info_ids_by_token[token].append(book_info.id)

    for token, book_ids in book_info_ids_by_token.items():

        search_term = SearchTerm(
            token=token,
            num_results=len(book_ids),
            # creates a json string from the book_ids array
            document_ids=json.dumps(book_ids),
        )

        session.add(search_term)

    session.commit()

    return book_info_ids_by_token
