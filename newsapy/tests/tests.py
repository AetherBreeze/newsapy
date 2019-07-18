from proper_noun_extraction import select_better_proper_noun_from


def select_better_proper_noun_from_tests():
    # 2-word names are selected over 1-word ones
    assert select_better_proper_noun_from("trump", "donald trump") == "donald trump"

    # 2-word names with distinguishers (Jr., Sr.) are selected over 2-word shorter versions
    assert select_better_proper_noun_from("Trump Jr.", "Donald Trump Jr.") == "Donald Trump Jr."

    # same-words-length names return the longer name
    assert select_better_proper_noun_from("mr. putin", "vladimir putin") == "vladimir putin"

    # different-word-length names return the name with fewer words
    assert select_better_proper_noun_from("theresa may", "prime minister may") == "theresa may"

if __name__ == "__main__":
    select_better_proper_noun_from_tests()