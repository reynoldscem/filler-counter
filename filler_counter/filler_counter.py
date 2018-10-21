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
        help=(
            'Names in the format accepted by {}. '
            'Optionally followed by upper and lower episode limts. '
            'Inclusive range separated by colon.'
            'e.g. naruto, bleach:50, naruto-shippuden::400, naruto:10:50'
            ''.format(url_example)
        )
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


def chunks_to_count(chunks):
    return sum(
        count_chunk(chunk)
        for chunk in chunks
    )


def reverse_range(_range):
    first, second = _range.split('-')
    return '{}-{}'.format(second, first)


def reverse_ep_list(episode_chunks):
    return [
        reverse_range(item) if '-' in item else item
        for item in list(reversed(episode_chunks))
    ]


def episode_upper_limit(episodes_chunks, upper_limit):
    result = episode_bottom_limit(
        list(reversed(episodes_chunks)),
        -upper_limit, negate=True
    )

    return list(reversed(result))


def episode_bottom_limit(episodes_chunks, bottom_limit, negate=False):
    for index, chunk in enumerate(episodes_chunks):
        if '-' in chunk:
            first, second = map(int, chunk.split('-'))
            if negate:
                second, first = -first, -second

            if second == bottom_limit:
                return [str(abs(second))] + episodes_chunks[index + 1:]
            elif second < bottom_limit:
                continue
            elif first >= bottom_limit:
                return episodes_chunks[index:]
            elif first < bottom_limit:
                format_values = (abs(bottom_limit), abs(second))
                if negate:
                    format_values = reversed(format_values)
                return [
                    '{}-{}'.format(*format_values)
                ] + episodes_chunks[index + 1:]
            elif second > bottom_limit:
                continue
            else:
                raise Exception('Should not reach here')
        else:
            entry = int(chunk)
            if negate:
                entry = -entry
            if entry < bottom_limit:
                continue
            if entry >= bottom_limit:
                return episodes_chunks[index:]
    return []


def get_count(soup, div_class, lower=None, upper=None):
    containing_div = soup.find('div', {'class': div_class})
    episodes_span = containing_div.find('span', {'class': 'Episodes'})
    episodes_text = episodes_span.text
    episode_chunks = episodes_text.split(', ')

    check_episodes_text(episodes_text)

    if lower is not None:
        episode_chunks = episode_bottom_limit(episode_chunks, lower)
    if upper is not None:
        episode_chunks = episode_upper_limit(episode_chunks, upper)

    return chunks_to_count(episode_chunks)


def process_name(name):
    def postamble():
        print('-' * 40)
        print()

    if ':' in name:
        name, *rest = name.split(':')
        rest = [
            None if value == '' else int(value)
            for value in rest
        ]

        if len(rest) == 1:
            lower = rest[0]
            upper = None
        elif len(rest) == 2:
            if rest[0] is not None and rest[1] is not None:
                assert rest[0] <= rest[1]
            lower, upper = rest
        else:
            raise ValueError("Must be name:lower:upper.")

    url = URL_FORMAT.format(name)

    try:
        response = urlopen(url)
    except HTTPError:
        print('Could not find \'{}\'!'.format(name))
        postamble()
        return

    data = response.read()
    soup = BeautifulSoup(data, 'html.parser')

    filler_count = get_count(soup, 'filler', lower, upper)
    canon_count = get_count(soup, 'canon', lower, upper)
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
