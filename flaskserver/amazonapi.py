#!/bin/env python2.6
# coding: utf-8

import datetime
from itertools import islice

import bottlenose
from lxml import objectify, etree
import dateutil.parser

DOCUMENT =  """
ResponseGroup:::
Besides these generic response groups, there are specific ones.
For example, if you want to return images of the items included in a response,
you would include the Image response group in the request.
If you wanted pricing information, you would include the Offer response group in the request.
To get browse node information, you'd include the BrowseNode response group.
The specificity of the response groups enables you to return only the information you want.
----- -----
"""


DOMAINS = {
    'CA': 'ca',
    'CN': 'cn',
    'DE': 'de',
    'ES': 'es',
    'FR': 'fr',
    'IN': 'in',
    'IT': 'it',
    'JP': 'co.jp',
    'UK': 'co.uk',
    'US': 'com',
}

AMAZON_ASSOCIATES_BASE_URL = 'http://www.amazon.{domain}/dp/'


class AmazonException(Exception): pass
class AsinNotFound(AmazonException): pass
class LookupException(AmazonException): pass
class SearchException(AmazonException): pass
class NoMorePages(SearchException): pass
class SimilartyLookupException(AmazonException): pass
class BrowseNodeLookupException(AmazonException): pass


class AmazonAPI(object):
    def __init__(self, aws_key, aws_secret, aws_associate_tag, **kwargs):
        """Initialize an Amazon API Proxy.

        kwargs values are passed directly to Bottlenose. Check the Bottlenose
        API for valid values (some are provided below).
        For legacy support, the older 'region' value is still supported.
        Code should be updated to use the Bottlenose 'Region' value
        instead.

        :param aws_key:
            A string representing an AWS authentication key.
        :param aws_secret:
            A string representing an AWS authentication secret.
        :param aws_associate_tag:
            A string representing an AWS associate tag.

        Important Bottlenose arguments:
        :param Region:
            ccTLD you want to search for products on (e.g. 'UK'
            for amazon.co.uk).
            See keys of bottlenose.api.SERVICE_DOMAINS for options, which were
            CA, CN, DE, ES, FR, IT, JP, UK, US at the time of writing.
            Must be uppercase. Default is 'US' (amazon.com).
        :param MaxQPS:
            Optional maximum queries per second. If we've made an API call
            on this object more recently that 1/MaxQPS, we'll wait
            before making the call. Useful for making batches of queries.
            You generally want to set this a little lower than the
            max (so 0.9, not 1.0).
            Amazon limits the number of calls per hour, so for long running
            tasks this should be set to 0.9 to ensure you don't hit the maximum.
            Defaults to None (unlimited).
        :param Timeout:
            Optional timeout for queries.
            Defaults to None.
        :param CacheReader:
            Called before attempting to make an API call.
            A function that takes a single argument, the URL that
            would be passed to the API, minus auth information,
            and returns a cached version of the (unparsed) response,
            or None.
            Defaults to None.
        :param CacheWriter:
            Called after a successful API call. A function that
            takes two arguments, the same URL passed to
            CacheReader, and the (unparsed) API response.
            Defaults to None.
        """
        # support older style calls
        if 'region' in kwargs:
            kwargs['Region'] = kwargs['region']
            del kwargs['region']
        self.api = bottlenose.Amazon(
            aws_key, aws_secret, aws_associate_tag, **kwargs)
        self.aws_associate_tag = aws_associate_tag
        self.region = kwargs.get('Region', 'US')

    def lookup(self, ResponseGroup="Large", **kwargs):
        """Lookup an Amazon Product.
        :return:
            An instance of :class:`~.AmazonProduct` if one item was returned,
            or a list of  :class:`~.AmazonProduct` instances if multiple
            items where returned.
        Example:
            >>> api.lookup(ItemId='B002L3XLBO')
        """
        response = self.api.ItemLookup(ResponseGroup=ResponseGroup, **kwargs)
        root = objectify.fromstring(response)
        if root.Items.Request.IsValid == 'False':
            code = root.Items.Request.Errors.Error.Code
            msg = root.Items.Request.Errors.Error.Message
            raise LookupException(
                "Amazon Product Lookup Error: '{0}', '{1}'".format(code, msg))
        if not hasattr(root.Items, 'Item'):
            raise AsinNotFound("ASIN(s) not found: '{0}'".format(
                etree.tostring(root, pretty_print=True)))
        if len(root.Items.Item) > 1:
            return [
                AmazonProduct(
                    item,
                    self.aws_associate_tag,
                    self,
                    region=self.region) for item in root.Items.Item
            ]
        else:
            return AmazonProduct(
                root.Items.Item,
                self.aws_associate_tag,
                self,
                region=self.region
            )

    def similarity_lookup(self, ResponseGroup="Large", **kwargs):
        """Similarty Lookup.
        Returns up to ten products that are similar to all items
        specified in the request.

        Example:
            >>> api.similarity_lookup(ItemId='B002L3XLBO,B000LQTBKI')
        """
        response = self.api.SimilarityLookup(
            ResponseGroup=ResponseGroup, **kwargs)
        root = objectify.fromstring(response)
        if root.Items.Request.IsValid == 'False':
            code = root.Items.Request.Errors.Error.Code
            msg = root.Items.Request.Errors.Error.Message
            raise SimilartyLookupException(
                "Amazon Similarty Lookup Error: '{0}', '{1}'".format(
                    code, msg))
        return [
            AmazonProduct(
                item,
                self.aws_associate_tag,
                self.api,
                region=self.region
            )
            for item in getattr(root.Items, 'Item', [])
        ]

    def browse_node_lookup(self, ResponseGroup="BrowseNodeInfo", **kwargs):
        """Browse Node Lookup.
        Returns the specified browse node's name, children, and ancestors.
        Example:
            >>> api.browse_node_lookup(BrowseNodeId='163357')
        """
        response = self.api.BrowseNodeLookup(
            ResponseGroup=ResponseGroup, **kwargs)
        root = objectify.fromstring(response)
        if root.BrowseNodes.Request.IsValid == 'False':
            code = root.BrowseNodes.Request.Errors.Error.Code
            msg = root.BrowseNodes.Request.Errors.Error.Message
            raise BrowseNodeLookupException(
                "Amazon BrowseNode Lookup Error: '{0}', '{1}'".format(
                    code, msg))
        return [AmazonBrowseNode(node.BrowseNode) for node in root.BrowseNodes]

    def search(self, **kwargs):
        """Search.

        :return:
            An :class:`~.AmazonSearch` iterable.
        """
        region = kwargs.get('region', self.region)
        kwargs.update({'region': region})
        return AmazonSearch(self.api, self.aws_associate_tag, **kwargs)

    def search_n(self, n, **kwargs):
        """Search and return first N results..

        :param n:
            An integer specifying the number of results to return.
        :return:
            A list of :class:`~.AmazonProduct`.
        """
        region = kwargs.get('region', self.region)
        kwargs.update({'region': region})
        items = AmazonSearch(self.api, self.aws_associate_tag, **kwargs)
        return list(islice(items, n))


class AmazonSearch(object):
    """ Amazon Search.
    A class providing an iterable over amazon search results.
    """
    def __init__(self, api, aws_associate_tag, **kwargs):
        """
        :param api:
            An instance of :class:`~.bottlenose.Amazon`.
        :param aws_associate_tag:
            An string representing an Amazon Associates tag.
        """
        self.kwargs = kwargs
        self.current_page = 1
        self.api = api
        self.aws_associate_tag = aws_associate_tag

    def __iter__(self):
        """Iterate.
        :return:
            Yields a :class:`~.AmazonProduct` for each result item.
        """
        for page in self.iterate_pages():
            for item in getattr(page.Items, 'Item', []):
                yield AmazonProduct(
                    item, self.aws_associate_tag, self.api, **self.kwargs)

    def iterate_pages(self):
        """
        :return:
            Yields lxml root elements.
        """
        try:
            while True:
                yield self._query(ItemPage=self.current_page, **self.kwargs)
                self.current_page += 1
        except NoMorePages:
            pass

    def _query(self, ResponseGroup="Large", **kwargs):
        """Query.

        :return:
            An lxml root element.
        """
        response = self.api.ItemSearch(ResponseGroup=ResponseGroup, **kwargs)
        root = objectify.fromstring(response)
        if root.Items.Request.IsValid == 'False':
            code = root.Items.Request.Errors.Error.Code
            msg = root.Items.Request.Errors.Error.Message
            if code == 'AWS.ParameterOutOfRange':
                raise NoMorePages(msg)
            else:
                raise SearchException(
                    "Amazon Search Error: '{0}', '{1}'".format(code, msg))
        return root


class AmazonBrowseNode(object):

    def __init__(self, element):
        self.element = element

    @property
    def id(self):
        """Browse Node ID.

        A positive integer that uniquely identifies a parent product category.

        :return:
            ID (integer)
        """
        if hasattr(self.element, 'BrowseNodeId'):
            return int(self.element['BrowseNodeId'])
        return None

    @property
    def name(self):
        """Browse Node Name.

        :return:
            Name (string)
        """
        return getattr(self.element, 'Name', None)

    @property
    def is_category_root(self):
        """Boolean value that specifies if the browse node is at the top of
        the browse node tree.
        """
        return getattr(self.element, 'IsCategoryRoot', False)

    @property
    def ancestor(self):
        """This browse node's immediate ancestor in the browse node tree.

        :return:
            The ancestor as an :class:`~.AmazonBrowseNode`, or None.
        """
        ancestors = getattr(self.element, 'Ancestors', None)
        if hasattr(ancestors, 'BrowseNode'):
            return AmazonBrowseNode(ancestors['BrowseNode'])
        return None

    @property
    def ancestors(self):
        """A list of this browse node's ancestors in the browse node tree.

        :return:
            List of :class:`~.AmazonBrowseNode` objects.
        """
        ancestors = []
        node = self.ancestor
        while node is not None:
            ancestors.append(node)
            node = node.ancestor
        return ancestors

    @property
    def children(self):
        """This browse node's children in the browse node tree.

        :return:
        A list of this browse node's children in the browse node tree.
        """
        children = []
        child_nodes = getattr(self.element, 'Children')
        for child in getattr(child_nodes, 'BrowseNode', []):
                children.append(AmazonBrowseNode(child))
        return children


class AmazonProduct(object):
    """A wrapper class for an Amazon product.
    """

    def __init__(self, item, aws_associate_tag, api, *args, **kwargs):
        """Initialize an Amazon Product Proxy.

        :param item:
            Lxml Item element.
        """
        self.item = item
        self.aws_associate_tag = aws_associate_tag
        self.api = api
        self.parent = None
        self.region = kwargs.get('region', 'US')

    def to_string(self):
        """Convert Item XML to string.

        :return:
            A string representation of the Item xml.
        """
        return etree.tostring(self.item, pretty_print=True)

    def _safe_get_element(self, path, root=None):
        """Safe Get Element.

        Get a child element of root (multiple levels deep) failing silently
        if any descendant does not exist.

        :param root:
            Lxml element.
        :param path:
            String path (i.e. 'Items.Item.Offers.Offer').
        :return:
            Element or None.
        """
        elements = path.split('.')
        parent = root if root is not None else self.item
        for element in elements[:-1]:
            parent = getattr(parent, element, None)
            if parent is None:
                return None
        return getattr(parent, elements[-1], None)

    def _safe_get_element_text(self, path, root=None):
        """Safe get element text.

        Get element as string or None,
        :param root:
            Lxml element.
        :param path:
            String path (i.e. 'Items.Item.Offers.Offer').
        :return:
            String or None.
        """
        element = self._safe_get_element(path, root)
        if element is not None:
            return element.text
        else:
            return None

    def _safe_get_element_date(self, path, root=None):
        """Safe get elemnent date.

        Get element as datetime.date or None,
        :param root:
            Lxml element.
        :param path:
            String path (i.e. 'Items.Item.Offers.Offer').
        :return:
            datetime.date or None.
        """
        value = self._safe_get_element_text(path=path, root=root)
        if value is not None:
            try:
                value = dateutil.parser.parse(value)
                if value:
                    value = value.date()
            except ValueError:
                value = None

        return value

    @property
    def price_and_currency(self):
        """Get Offer Price and Currency.

        Return price according to the following process:

        * If product has a sale return Sales Price, otherwise,
        * Return Price, otherwise,
        * Return lowest offer price, otherwise,
        * Return None.

        :return:
            A tuple containing:

                1. Float representation of price.
                2. ISO Currency code (string).
        """
        price = self._safe_get_element_text(
            'Offers.Offer.OfferListing.SalePrice.Amount')
        if price:
            currency = self._safe_get_element_text(
                'Offers.Offer.OfferListing.SalePrice.CurrencyCode')
        else:
            price = self._safe_get_element_text(
                'Offers.Offer.OfferListing.Price.Amount')
            if price:
                currency = self._safe_get_element_text(
                    'Offers.Offer.OfferListing.Price.CurrencyCode')
            else:
                price = self._safe_get_element_text(
                    'OfferSummary.LowestNewPrice.Amount')
                currency = self._safe_get_element_text(
                    'OfferSummary.LowestNewPrice.CurrencyCode')
        if price:
            return float(price) / 100, currency
        else:
            return None, None

    @property
    def asin(self):
        """ASIN (Amazon ID)

        :return:
            ASIN (string).
        """
        return self._safe_get_element_text('ASIN')

    @property
    def sales_rank(self):
        """Sales Rank

        :return:
            Sales Rank (integer).
        """
        return self._safe_get_element_text('SalesRank')

    @property
    def offer_url(self):
        """Offer URL

        :return:
            Offer URL (string).
        """
        return "{0}{1}/?tag={2}".format(
            AMAZON_ASSOCIATES_BASE_URL.format(domain=DOMAINS[self.region]),
            self.asin,
            self.aws_associate_tag)

    @property
    def author(self):
        """Author.

        Depricated, please use `authors`.
        :return:
            Author (string).
        """
        authors = self.authors
        if len(authors):
            return authors[0]
        else:
            return None

    @property
    def authors(self):
        """Authors.

        :return:
            Returns of list of authors
        """
        result = []
        authors = self._safe_get_element('ItemAttributes.Author')
        if authors is not None:
            for author in authors:
                result.append(author.text)
        return result

    @property
    def creators(self):
        """Creators.

        Creators are not the authors. These are usually editors, translators,
        narrators, etc.

        :return:
            Returns a list of creators where each is a tuple containing:

                1. The creators name (string).
                2. The creators role (string).

        """
        # return tuples of name and role
        result = []
        creators = self._safe_get_element('ItemAttributes.Creator')
        if creators is not None:
            for creator in creators:
                role = creator.attrib['Role'] if 'Role' in creator.attrib else None
                result.append((creator.text, role))
        return result

    @property
    def publisher(self):
        """Publisher.

        :return:
            Publisher (string)
        """
        return self._safe_get_element_text('ItemAttributes.Publisher')

    @property
    def label(self):
        """Label.

        :return:
            Label (string)
        """
        return self._safe_get_element_text('ItemAttributes.Label')

    @property
    def manufacturer(self):
        """Manufacturer.

        :return:
            Manufacturer (string)
        """
        return self._safe_get_element_text('ItemAttributes.Manufacturer')

    @property
    def brand(self):
        """Brand.

        :return:
            Brand (string)
        """
        return self._safe_get_element_text('ItemAttributes.Brand')

    @property
    def isbn(self):
        """ISBN.

        :return:
            ISBN (string)
        """
        return self._safe_get_element_text('ItemAttributes.ISBN')

    @property
    def eisbn(self):
        """EISBN (The ISBN of eBooks).

        :return:
            EISBN (string)
        """
        return self._safe_get_element_text('ItemAttributes.EISBN')

    @property
    def binding(self):
        """Binding.

        :return:
            Binding (string)
        """
        return self._safe_get_element_text('ItemAttributes.Binding')

    @property
    def pages(self):
        """Pages.

        :return:
            Pages (string)
        """
        return self._safe_get_element_text('ItemAttributes.NumberOfPages')

    @property
    def publication_date(self):
        """Pubdate.

        :return:
            Pubdate (datetime.date)
        """
        return self._safe_get_element_date('ItemAttributes.PublicationDate')

    @property
    def release_date(self):
        """Release date .

        :return:
            Release date (datetime.date)
        """
        return self._safe_get_element_date('ItemAttributes.ReleaseDate')

    @property
    def edition(self):
        """Edition.

        :return:
            Edition (string)
        """
        return self._safe_get_element_text('ItemAttributes.Edition')

    @property
    def large_image_url(self):
        """Large Image URL.

        :return:
            Large image url (string)
        """
        return self._safe_get_element_text('LargeImage.URL')

    @property
    def medium_image_url(self):
        """Medium Image URL.

        :return:
            Medium image url (string)
        """
        return self._safe_get_element_text('MediumImage.URL')

    @property
    def small_image_url(self):
        """Small Image URL.

        :return:
            Small image url (string)
        """
        return self._safe_get_element_text('SmallImage.URL')

    @property
    def tiny_image_url(self):
        """Tiny Image URL.

        :return:
            Tiny image url (string)
        """
        return self._safe_get_element_text('TinyImage.URL')

    @property
    def reviews(self):
        """Customer Reviews.

        Get a iframe URL for customer reviews.
        :return:
            A tuple of: has_reviews (bool), reviews url (string)
        """
        iframe = self._safe_get_element_text('CustomerReviews.IFrameURL')
        has_reviews = self._safe_get_element_text('CustomerReviews.HasReviews')
        if has_reviews and has_reviews == 'true':
            has_reviews = True
        else:
            has_reviews = False
        return has_reviews, iframe

    @property
    def ean(self):
        """EAN.

        :return:
            EAN (string)
        """
        ean = self._safe_get_element_text('ItemAttributes.EAN')
        if ean is None:
            ean_list = self._safe_get_element_text('ItemAttributes.EANList')
            if ean_list:
                ean = self._safe_get_element_text(
                    'EANListElement', root=ean_list[0])
        return ean

    @property
    def upc(self):
        """UPC.

        :return:
            UPC (string)
        """
        upc = self._safe_get_element_text('ItemAttributes.UPC')
        if upc is None:
            upc_list = self._safe_get_element_text('ItemAttributes.UPCList')
            if upc_list:
                upc = self._safe_get_element_text(
                    'UPCListElement', root=upc_list[0])
        return upc

    @property
    def sku(self):
        """SKU.

        :return:
            SKU (string)
        """
        return self._safe_get_element_text('ItemAttributes.SKU')

    @property
    def mpn(self):
        """MPN.

        :return:
            MPN (string)
        """
        return self._safe_get_element_text('ItemAttributes.MPN')

    @property
    def model(self):
        """Model Name.

        :return:
            Model (string)
        """
        return self._safe_get_element_text('ItemAttributes.Model')

    @property
    def part_number(self):
        """Part Number.

        :return:
            Part Number (string)
        """
        return self._safe_get_element_text('ItemAttributes.PartNumber')

    @property
    def title(self):
        """Title.

        :return:
            Title (string)
        """
        return self._safe_get_element_text('ItemAttributes.Title')

    @property
    def editorial_review(self):
        """Editorial Review.

        Returns an editorial review text.

        :return:
            Editorial Review (string)
        """
        reviews = self.editorial_reviews
        if reviews:
            return reviews[0]
        return ''

    @property
    def editorial_reviews(self):
        """Editorial Review.

        Returns a list of all editorial reviews.

        :return:
            A list containing:

                Editorial Review (string)
        """
        result = []
        reviews_node = self._safe_get_element('EditorialReviews')

        if reviews_node is not None:
            for review_node in reviews_node.iterchildren():
                content_node = getattr(review_node, 'Content')
                if content_node is not None:
                    result.append(content_node.text)
        return result

    @property
    def languages(self):
        """Languages.

        Returns a set of languages in lower-case.
        :return:
            Returns a set of languages in lower-case (strings).
        """
        result = set()
        languages = self._safe_get_element('ItemAttributes.Languages')
        if languages is not None:
            for language in languages.iterchildren():
                text = self._safe_get_element_text('Name', language)
                if text:
                    result.add(text.lower())
        return result

    @property
    def features(self):
        """Features.

        Returns a list of feature descriptions.
        :return:
            Returns a list of 'ItemAttributes.Feature' elements (strings).
        """
        result = []
        features = self._safe_get_element('ItemAttributes.Feature')
        if features is not None:
            for feature in features:
                result.append(feature.text)
        return result

    @property
    def list_price(self):
        """List Price.

        :return:
            A tuple containing:

                1. Float representation of price.
                2. ISO Currency code (string).
        """
        price = self._safe_get_element_text('ItemAttributes.ListPrice.Amount')
        currency = self._safe_get_element_text(
            'ItemAttributes.ListPrice.CurrencyCode')
        if price:
            return float(price) / 100, currency
        else:
            return None, None

    def get_attribute(self, name):
        """Get Attribute

        Get an attribute (child elements of 'ItemAttributes') value.

        :param name:
            Attribute name (string)
        :return:
            Attribute value (string) or None if not found.
        """
        return self._safe_get_element_text("ItemAttributes.{0}".format(name))

    def get_attribute_details(self, name):
        """Get Attribute Details

        Gets XML attributes of the product attribute. These usually contain
        details about the product attributes such as units.
        :param name:
            Attribute name (string)
        :return:
            A name/value dictionary.
        """
        return self._safe_get_element("ItemAttributes.{0}".format(name)).attrib

    def get_attributes(self, name_list):
        """Get Attributes

        Get a list of attributes as a name/value dictionary.

        :param name_list:
            A list of attribute names (strings).
        :return:
            A name/value dictionary (both names and values are strings).
        """
        properties = {}
        for name in name_list:
            value = self.get_attribute(name)
            if value is not None:
                properties[name] = value
        return properties

    @property
    def parent_asin(self):
        """Parent ASIN.

        Can be used to test if product has a parent.
        :return:
            Parent ASIN if product has a parent.
        """
        return self._safe_get_element('ParentASIN')

    def get_parent(self):
        """Get Parent.

        Fetch parent product if it exists.
        Use `parent_asin` to check if a parent exist before fetching.
        :return:
            An instance of :class:`~.AmazonProduct` representing the
            parent product.
        """
        if not self.parent:
            parent = self._safe_get_element('ParentASIN')
            if parent:
                self.parent = self.api.lookup(ItemId=parent)
        return self.parent

    @property
    def browse_nodes(self):
        """Browse Nodes.

        :return:
            A list of :class:`~.AmazonBrowseNode` objects.
        """
        root = self._safe_get_element('BrowseNodes')
        if root is None:
            return []

        return [AmazonBrowseNode(child) for child in root.iterchildren()]

