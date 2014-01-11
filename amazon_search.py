import amazonproduct
# import lxml

from model import BookInfo

api = amazonproduct.API(locale='us')


def get_book_info_from_ean(ean):
    # ean = BookInfo.query.get('ean')

    # search by IDType: EAN
    # ResponseGroup: Images
    # ItemAttributes: Title, Author, Genre, NumberOfPages

    results = api.item_lookup(
        ItemId=ean,
        IdType='EAN',
        ResponseGroup='ItemAttributes',
        SearchIndex='Books',
        )

    book_genre = api.item_lookup(
        ItemId=ean,
        IdType='EAN',
        ResponseGroup='BrowseNodes',
        SearchIndex='Books',
        )

    title = results.Items.Item.ItemAttributes.Title
    author = results.Items.Item.ItemAttributes.Author
    genre = book_genre.Items.Item.BrowseNodes.BrowseNode.Name
    try:  # sometimes Amazon doesn't have number of pages
        number_pages = results.Items.Item.ItemAttributes.NumberOfPages
    except AttributeError:
        number_pages = 0
    isbn = results.Items.Item.ItemAttributes.ISBN

    print "YO! LOOK HERE!!"
    print genre
    print type(title)

    book_image = api.item_lookup(
        ItemId=ean,
        IdType='EAN',
        ResponseGroup='Images',
        SearchIndex='Books',
        )

    try:
        image_url = book_image.Items.Item.ImageSets.ImageSet.LargeImage.URL
    except AttributeError:
        image_url = None
    try:
        thumbnail_url = book_image.Items.Item.ImageSets.ImageSet.MediumImage.URL
    except AttributeError:
        thumbnail_url = None

    book_review = api.item_lookup(
        ItemId=ean,
        IdType='EAN',
        ResponseGroup='EditorialReview',
        SearchIndex='Books',
        )

    editorial_review = book_review.Items.Item.EditorialReviews.EditorialReview.Content

    # results_info = lxml.etree.tounicode(results, pretty_print=True)
    # image_info = lxml.etree.tounicode(book_image, pretty_print=True)
    # review_info = lxml.etree.tounicode(book_review, pretty_print=True)

    return BookInfo(
        ean=ean,
        isbn=str(isbn),
        title=str(title),
        author=str(author),
        number_pages=int(number_pages),
        genre=str(genre),
        image_url=str(image_url),
        thumbnail_url=str(thumbnail_url),
        # ^this is the medium image in amazon's api
        editorial_review=editorial_review.text,
        )
