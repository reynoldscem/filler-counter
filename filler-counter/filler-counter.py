'Script to get counts of filler and canon episodes from animefillerlist.com'
from urllib.request import urlopen
from urllib.error import HTTPError
from bs4 import BeautifulSoup
import argparse
import re


URL_FORMAT = 'http://www.animefillerlist.com/shows/{}'


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)

    url_example = URL_FORMAT.format('NAME')
    parser.add_argument(
        'names', type=str, nargs='+',
        help='Names in the format accepted by {}'.format(url_example)
    )

    return parser


def get_regex():
    digit_group = r'(:?^\d+(?:-\d+))'
    regex_str = r'^(?:{}, )*{}?$'.format(*(digit_group,) * 2)
    return re.compile(regex_str)


def check_episodes_text(episodes_text, regex=get_regex()):
    return re.match(regex, episodes_text) is not None


def count_chunk(chunk):
    if '-' not in chunk:
        return 1
    else:
        first, second = map(int, chunk.split('-'))
        assert second >= first, 'Second episode less than first.'
        return (second - first) + 1


def string_to_count(string):
    return sum(
        count_chunk(chunk)
        for chunk in string.split(', ')
    )


def get_count(soup, div_class):
    containing_div = soup.find('div', {'class': div_class})
    episodes_span = containing_div.find('span', {'class': 'Episodes'})
    episodes_text = episodes_span.text

    check_episodes_text(episodes_text)

    return string_to_count(episodes_text)


def process_name(name):
    def postamble():
        print('-' * 40)
        print()

    url = URL_FORMAT.format(name)

    try:
        response = urlopen(url)
    except HTTPError:
        print('Could not find \'{}\'!'.format(name))
        postamble()
        return

    data = response.read()
    soup = BeautifulSoup(data, 'html.parser')

    filler_count = get_count(soup, 'filler')
    canon_count = get_count(soup, 'canon')
    total_count = filler_count + canon_count

    print('{}:'.format(name))
    print('\tFiller count:\t{}'.format(filler_count))
    print('\tCanon count:\t{}'.format(canon_count))
    print('\tTotal count:\t{}'.format(total_count))
    postamble()


def main():
    args = build_parser().parse_args()

    names = args.names

    for name in names:
        process_name(name)


if __name__ == '__main__':
    main()
