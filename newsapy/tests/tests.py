from newsapy.proper_noun_extraction import extract_proper_nouns_from_text, select_better_proper_noun_from


def select_better_proper_noun_from_tests():
    # 2-word names are selected over 1-word ones
    assert select_better_proper_noun_from("trump", "donald trump") == "donald trump"

    # 2-word names with distinguishers (Jr., Sr.) are selected over 2-word shorter versions
    assert select_better_proper_noun_from("Trump Jr.", "Donald Trump Jr.") == "Donald Trump Jr."

    # same-words-length names return the longer name
    assert select_better_proper_noun_from("mr. putin", "vladimir putin") == "vladimir putin"

    # different-word-length names return the name with fewer words
    assert select_better_proper_noun_from("theresa may", "prime minister may") == "theresa may"

    # accumulation
    assert extract_proper_nouns_from_text("Trump took his friend Donald Trump to President Donald Trump's favorite McDonalds.") == ["Donald Trump", "McDonalds"]

if __name__ == "__main__":
    select_better_proper_noun_from_tests()