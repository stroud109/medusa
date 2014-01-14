
from model import SearchTerm, BookInfo, session

import math

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
        if data:
            lowercased_words = data.lower()

            for token in lowercased_words.split(' '):
                # remove anything that does't match a word char or a number
                token = token.replace(r'[^\w\d]', '')
                tokens.append(token)

    return tokens


def recreate_index():
    '''
    This function indexes the book_info table of the database
    I'd eventually like to impliment tf-idf functionality, thus
    I am not deduplicating the docoment_ids for each SearchTerm
    http://en.wikipedia.org/wiki/Tf%E2%80%93idf
    '''

    # Right now, i'm saving a list of doc IDs, including duplicates,
    # for each search term. I think i need to save a dictionary of
    # doc IDs and TF/IDF scores for each search term.
    # Not sure how saving a dictionary will effect the json bit

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
    '''
    This function updates a dictionary containing all tokens for all books.
    '''

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


def get_term_frequency(some_document):
    '''
    `get_term_frequency` returns a dictionary where the keys are words
    and the values are the number of times the word occurs in the
    passed document.
    '''

    dictionary_of_terms_for_single_document = {}

    # split the words on whitespace within individual documents

    split_terms = some_document.split(' ')

    ## alternative with py built-in, part 1
    # term_frequency = Counter()

    for term in split_terms:
        ## alternative with Python built-in, part 2
        # term_frequency[term] += 1
        if term not in dictionary_of_terms_for_single_document:
            dictionary_of_terms_for_single_document[term] = 1
        else:
            dictionary_of_terms_for_single_document[term] += 1

    # should yeild keys and values for search term frequencies
    return dictionary_of_terms_for_single_document
    ## alternative with Python built-in, part 3
    # return term_frequency


def get_inverse_doc_frequency(list_of_strings, a_search_term):
    '''
    `get_inverse_doc_frequency` calculates the TF/IDF score
    for a given search term within the list of passed documents.

    More on TF/IDF: http://en.wikipedia.org/wiki/Tf%E2%80%93idf
    '''

    # find num of documents in the entire database that contain a_search_term
    list_of_docs_with_term = []

    for some_doc in list_of_strings:
        # I'm not using the full functionality of get_term_frequency
        # Instead, I'm basically using it like a set right now
        print 'Looking at this document: %s' % some_doc
        term_frequency_dict = get_term_frequency(some_doc)
        print 'Here\'s the TF dict for this document: %s' % term_frequency_dict

        if a_search_term in term_frequency_dict:
            list_of_docs_with_term.append(some_doc)
            print 'This doc contained the search term \'%s\'' % a_search_term
            print 'So far, these docs have term: %s' % list_of_docs_with_term

    return math.log(float(len(list_of_strings)) / len(list_of_docs_with_term))
