
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
        for column in COLUMNS_TO_INDEX:
            data = getattr(info, column)
            # getattr is a shortcut for 'info.<attribute name>
            if data:
                lowercased_words = data.ascii_lowercase()
                tokens = lowercased_words.split(' ')

                for token in tokens:
                    if not token in book_info_ids_by_token:
                        book_info_ids_by_token[token] = []
                    book_info_ids_by_token[token].append(info.id)
                    # use set to avoid redundant keys

    # id = Column(Integer, primary_key=True)
    # token = Column(String(1000), nullable=False)
    # num_results = Column(Integer(), nullable=False)
    # document_ids = Column(String(1000), nullable=False)

    for token, book_ids in book_info_ids_by_token.items():

        search_term = SearchTerm(
            token=token,
            document_ids=json.dumps(book_ids),
            # creates a json string from the book_ids array
            num_results=len(book_ids),
        )

        session.add(search_term)

    session.commit()

    return book_info_ids_by_token

    # create a dictionary of keywords where key is a token
    # and value is a list of book ids
    # create tokens from book metadata (book info) from every column
    # take resulting dictionary, loop over keys and values
    # save each key as new SearchTerm
