import cv2
import json

from newsapy import image_utils
from datetime import datetime
from collections import OrderedDict
from newsapy.const import NEWS_SIGNATURES, GARBAGE_SOURCES, TEXT_ENCODING_FORMAT, IMAGE_URL_FORMAT, NEWSAPI_PARSED_TIME_FORMAT
from newsapy.proper_noun_extraction import extract_proper_nouns_from_text, select_better_proper_noun_from

class NewsArticle(object):
    def __init__(self, client, article_json, force_initialize_proper_nouns=False):
        self.__uid = None # used in some databases
        self.id = None # used for UID in some applications after fetching
        self.source = article_json["source"]["name"]
        self.authors = article_json["author"]
        self.url = article_json["url"]
        self.time_published = parse_newsapi_time(article_json["publishedAt"])
        self.__parent_client = client

        for source in GARBAGE_SOURCES:
            if source in self.url:
                self.title = ""
                self.image_url = None
                self.description = ""
                self.content = ""
                return

        self.image_url = article_json["urlToImage"]
        self.title = format_text(article_json["title"]) if article_json["title"] else ""
        self.description = format_text(article_json["description"]) if article_json["description"] else ""
        self.content = format_text(article_json["content"]) if article_json["content"] else ""

        self.__proper_nouns_in_title = None
        self.__proper_nouns_in_description = None
        self.__all_proper_nouns = None
        if force_initialize_proper_nouns: # these "properties" are actually lazy methods; setting FIPN forces them to evaluate immediately
            self.__proper_nouns_in_title = self.proper_nouns_in_title
            self.__proper_nouns_in_description = self.proper_nouns_in_description
            self.__all_proper_nouns = self.all_proper_nouns
        self.__images = OrderedDict() # always stores the full-sized image first

    @property
    def proper_nouns_in_title(self):
        if self.title == "": # for garbage sources, we dont want their proper nouns
            return []

        if self.__proper_nouns_in_title is None: # if we havent already computed the list
            self.__proper_nouns_in_title = extract_proper_nouns_from_text(self.title) # do that

        return self.__proper_nouns_in_title

    @property
    def proper_nouns_in_description(self):
        if self.description == "": # for garbage sources, we dont want their proper nouns
            return []

        if self.__proper_nouns_in_description is None: # if we havent already computed the list
            self.__proper_nouns_in_description = extract_proper_nouns_from_text(self.description) # do that

        return self.__proper_nouns_in_description

    @property
    def all_proper_nouns(self):
        if self.title == "" and self.description == "":
            return None
        if self.__all_proper_nouns is None: # if we havent already computed the list, do it now
            ret = set()
            proper_nouns = list(set().union(self.proper_nouns_in_title, self.proper_nouns_in_description)) # the non-repetitive union of two sets of proper nouns
            for first_proper_noun in proper_nouns:
                to_add = first_proper_noun
                marked_for_removal_from_ret = []
                for second_proper_noun in ret:
                    if first_proper_noun in second_proper_noun or second_proper_noun in first_proper_noun: # if this proper noun is a smaller version of another one later in the list
                        to_add = select_better_proper_noun_from(first_proper_noun, second_proper_noun)
                        if not to_add == second_proper_noun:
                            marked_for_removal_from_ret.append(second_proper_noun)

                for subsumed_noun in marked_for_removal_from_ret:
                    ret.remove(subsumed_noun)
                ret.add(to_add)

            self.__all_proper_nouns = list(ret) # set the property so we only have to compute it once

        return self.__all_proper_nouns

    @property
    def uid(self):
        if not (self.title and self.source): # since the hash is a combination of these two, we cant make one without them
            return None
        elif not self.__uid:
            self.__parent_client.hasher.update((self.title + self.source).encode(TEXT_ENCODING_FORMAT))
            self.__uid = self.__parent_client.hasher.hexdigest()

        return self.__uid

    async def image_async(self, dimensions=None):
        filename = "{}__{}".format(self.source, self.title)
        img_path = None

        if self.image_url is None:
            return None
        elif not self.__images: # if we havent fetched the image for this article yet
            img_path, dimensions = await image_utils.fetch_and_resize_image(self.__parent_client.http_session, self.image_url, filename) # download the full-sized image
        elif not dimensions: # if weve fetched it, and no specific dims were requested
            return self.title, list(self.__images.values())[-1]  # return the most recently fetched image
        elif dimensions not in [*self.__images]: # if it's requested for a size we havent made yet
            img_path = image_utils.resize_image(cv2.imread(list(self.__images.values())[0]), dimensions, filename, filetype="JPEG") # downsize the original image and return it instead
        # if none of these trip, then we already have the image in that size stored in self.__images[dimensions]

        if img_path: # if the fetch didnt fail
            self.__images[dimensions] = img_path # store it so we can use it again
            return self.title, self.__images[dimensions] # return the title too, since this is frequently called from get_images_of_articles and we need to track which article each image is from
        else:
            return self.title, None

    def image(self, dimensions=None):
        return self.__parent_client.event_loop.run_until_complete(self.image_async(dimensions=dimensions))

    def to_json(self):
        ret = {}

        ret["uid"] = self.uid
        ret["title"] = self.title
        ret["description"] = self.description
        ret["content"] = self.content
        ret["url"] = self.url
        ret["image_url"] = IMAGE_URL_FORMAT.format(ret["uid"]) # self.uid is a lazy method, so this is ever so slightly faster
        ret["keywords"] = self.all_proper_nouns
        ret["source"] = self.source
        ret["time_published"] = datetime.strftime(self.time_published, NEWSAPI_PARSED_TIME_FORMAT)

        return json.dumps(ret)

def parse_newsapi_time(newsapi_time_string): # WORKS
    actual_datetime = newsapi_time_string.split('+')[0].split('.')[0] # filters out time offset and useless decimal seconds
    actual_datetime = actual_datetime.replace('Z', '') # sometimes there's a Z on the end of the time?
    return datetime.strptime(actual_datetime, NEWSAPI_PARSED_TIME_FORMAT)


def format_text(text):
    ret = text.split('\r')[0].replace("\xa0", " ") # filters out long description ads and non-breaking spaces
    for signature in NEWS_SIGNATURES:
        ret = ret.replace(signature, "") # removes news signatures that trip proper noun detection

    return ret.strip() # remove end spaces and return
