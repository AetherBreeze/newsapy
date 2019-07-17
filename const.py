# newsapi_client.py
TOP_HEADLINES_URL = 'https://newsapi.org/v2/top-headlines'
EVERYTHING_URL = 'https://newsapi.org/v2/everything'
SOURCES_URL = 'https://newsapi.org/v2/sources'

countries = {'ae','ar','at','au','be','bg','br','ca','ch','cn','co','cu','cz','de','eg','fr','gb','gr','hk',
             'hu','id','ie','il','in','it','jp','kr','lt','lv','ma','mx','my','ng','nl','no','nz','ph','pl',
             'pt','ro','rs','ru','sa','se','sg','si','sk','th','tr','tw','ua','us','ve','za'}

languages = {'ar','en','cn','de','es','fr','he','it','nl','no','pt','ru','sv','ud'}

categories = {'business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology'}

sort_method = {'relevancy','popularity','publishedAt'}

HTTP_OK = 200
IMAGE_DIRECTORY = "images"

# newsapi_article.py
NEWS_SIGNATURES = ["| TheHill",  "- CNN", "  Guardian News", "| NYT News - The New York Times", " | NBC Nightly News", " - Bloomberg", " - The Boston Globe", "at CNN.com", "NY POST:", " - Fox News", "Visit MarketsInsider.com …", "Visit Business Insider"]

# nltk_handler.py
TAGGERS = ["maxent_treebank_pos_tagger", "averaged_perceptron_tagger"]

# proper_noun_extraction.py
FAKE_PROPER_NOUNS = ["~", "oh", "*content*", "Factbox", "Explainer", "you're", "Co", "Inc", "Are", "Ldt", "Mr", "Ms", "Mrs", "A", "An", "It", "Here", "How", "Many", "EXCLUSIVE", "v", "-", "Rep", "Sen", "P.M", "A.M", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
JOINERS = ["of"]
PUNCTUATION_REPLACEMENT = "{}"
TITLES = ["Rep", "Sen", "Representative", "Senator", "President", "Chair", "Head"] # currently unused
PUNCTUATION = ['.', ',', '?', '!', ":", u"\u2014", u"\u2013", "|", "...", "..", u"\u2026"] # u2013, u2014 = em dash, u2026 = ellipsis
ELLIPSES = ["...", "..", u"\u2026"] # \u2026 = …
SENTENCE_INTERRUPTORS = ["“", "”", '"', "(", ")"]
SINGLE_QUOTES = ["‘", "’", "'", u'\u2018', u'\u2019', ] # u2018, 2019 = forward and backward single quotes
UPPERCASE_ASCII_VALUES_UPPER_BOUND = 91
UPPERCASE_WORD_GARBAGE_THRESHHOLD = 5/6 # this may be a bit low
PROBLEM_WORDS = {"U.s": "United States", "U.n": "United Nations", "D.c": "Washington, D.C."}
PROBLEM_PHRASES = {"House of": "House of Representatives", "United": "United States", }
GARBAGE_SOURCES = ["youtube.com/", "bbc.co.uk/programmes"] # currently unused
NODE_DISTINGUISHERS = ["Junior", "Senior", "Jr.", "Sr.", "St."]
WORD_SEPERATORS = ["\r", "\n", "-"]