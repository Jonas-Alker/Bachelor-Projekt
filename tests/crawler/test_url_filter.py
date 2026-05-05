import os
from src.crawler.url_filter import (
    load_rules,
    filter_urls
)

def test_load_rules_fallback():
    include, exclude = load_rules("does_not_exist")
    include_default, exclude_default = load_rules("default")

    assert include == include_default
    assert exclude == exclude_default

def test_filter_logic():
    test_iput_dir = "tests/test_data/raw"
    test_output_dir = "tests/test_data/filtered"
    portal_name = "test_portal"

    input_path = f"{test_iput_dir}/{portal_name}_urls.txt"
    output_path = f"{test_output_dir}/{portal_name}_filtered_urls.txt"

    if not os.path.exists(test_iput_dir):
        os.makedirs(test_iput_dir)

    if os.path.exists(input_path):
        os.remove(input_path)

    if os.path.exists(output_path):
        os.remove(output_path)

    with open(input_path, "w", encoding="utf-8") as f:
        f.write("https://mimikama.org/artikel-1\n")
        f.write("https://mimikama.org/faktencheck-2\n")
        f.write("https://mimikama.org/impressum\n")
        f.write("https://mimikama.org/news\n")

    filter_urls(portal_name, input_base= test_iput_dir, output_base= test_output_dir)


    assert os.path.exists(output_path)

    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "artikel-1" in content
        assert "faktencheck-2" in content
        assert "news" not in content
        assert "impressum" not in content