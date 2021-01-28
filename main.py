#!/usr/bin/python3
import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


def do_login():
    session.post(links['main'], data={'team': input().strip(),
                                      'password': input().strip(),
                                      'op': 'login'})
    response = session.get(links['main'])
    if not response.ok:
        print('bad connection')
        return False
    elif response.text.find('not logged') == -1:
        return True
    else:
        print('bad data')
        return False


def download_file(url, folder, name, progress_bar):
    if os.path.exists(f'{folder}/{name}'):
        return False
    if not os.path.exists('name'):
        os.system(f'mkdir -p "{folder}"')
    response = session.get(url, stream=True)
    progress_bar.total = int(response.headers.get('content-length', 0))
    progress_bar.unit_scale = True
    block_size = 1024  # 1 Kibibyte
    with open(f'{folder}/{name}', 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.reset()
    return True


def get_statement(link, folder, progress_bar):
    session.get(link)
    soup = BeautifulSoup(session.get(links['main']).text, 'html.parser')
    url = soup.find_all('a')[6].attrs['href']
    progress_bar.desc = 'statement.pdf'
    return download_file(url, folder, 'statement.pdf', progress_bar)


def clear_code(code):
    code = code.replace('View submit', '')
    code = code.replace('view feedback', '')
    code = code.strip()
    return code


def get_submits(folder, progress_bar):
    submits_count = 0
    soup = BeautifulSoup(session.get(links['submits']).text, 'html.parser')
    table_rows = soup.find_all('tr', attrs={'class': 'fok'})

    progress_bar.total = len(table_rows)
    for row in table_rows:
        column = row.find_all('td')
        name = column[1].string
        if column[4].string.find('C++'):
            name += '.cpp'
        elif column[4].string.find('Py'):
            name += '.py'
        url = links['base0'] + row.find_all('td')[7].find('a').attrs['href']
        progress_bar.desc = name

        # original code stored in a shitty format so we cant use download_file()
        code = clear_code(BeautifulSoup(session.get(url).text, 'html.parser').get_text())
        if not os.path.exists(f'{folder}/{name}'):
            submits_count += 1
            with open(f'{folder}/{name}', 'w') as file:
                file.write(code)

        progress_bar.update()
    progress_bar.reset()
    return submits_count


def get_contests():
    contest_count = 0
    submits_count = 0

    soup = BeautifulSoup(session.get(links['contests']).text, 'html.parser')
    table_rows = soup.find_all('tr')[2:]

    progress_bar = tqdm(position=1)
    for contest in tqdm(table_rows, position=0, desc='Contests'):
        date = contest.find_all('td')[0].find('a').string[0:-4]
        href = contest.find_all('td')[0].find('a').attrs['href']
        theme = contest.find_all('td')[1].find('a').string
        path = date + ':' + theme
        contest_count += get_statement(links['base'] + href, path, progress_bar)
        submits_count += get_submits(path, progress_bar)
    progress_bar.close()

    return contest_count, submits_count


if __name__ == '__main__':
    links = {'base0': 'http://acm.math.spbu.ru',
             'base': 'http://acm.math.spbu.ru/tsweb/',
             'main': 'http://acm.math.spbu.ru/tsweb/index',
             'submits': 'http://acm.math.spbu.ru/tsweb/allsubmits',
             'contests': 'http://acm.math.spbu.ru/tsweb/contests?mask=1'}
    with requests.session() as session:
        if do_login():
            contest_count, submits_count = get_contests()
            print(f'new contests: {contest_count}')
            print(f'new submits: {submits_count}')
