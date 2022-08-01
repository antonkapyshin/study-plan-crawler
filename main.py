import argparse
import pathlib
import re
import sys
from collections import namedtuple
from urllib.parse import urlsplit
from http.client import HTTPSConnection

import bs4


Subject = namedtuple("Subject", ["url", "name", "semester", "type", "credits"])
CommonSubject = namedtuple("CommonSubject", ["name", "programs"])


def get_response(url):
    urlparts = urlsplit(url)
    conn = HTTPSConnection(urlparts.netloc)
    conn.request("GET", urlparts.path)
    response = conn.getresponse()
    if response.status != 200:
        print(f"Got {response.status} status code")
        sys.exit(1)

    return response


def parse(html):
    soup = bs4.BeautifulSoup(html, features="html.parser")
    for tr in soup.find_all("tr"):
        tds = list(tr.find_all("td"))
        if len(tds) < 2:
            continue

        # code = tds[0].text
        link = tds[2].find_next("a")
        yield Subject(url=link.get("href"), name=link.text, semester=tds[3].text, type=tds[4].text, credits=tds[5].text)


def crawl(url):
    response = get_response(url)

    for index, subject in enumerate(parse(response.read().decode(encoding="utf-8"))):
        print(f"{index}. {subject.name} – {subject.semester}|{subject.type}|{subject.credits}")


def _find_common(files):
    result = {level: set() for level in range(1, len(files) + 1)}

    subjects = {}
    for file in files:
        with open(str(file)) as f:
            contents = f.readlines()
        subjects[file.name] = [line.split(".", 1)[1].strip().split("–", 1)[0].strip() for line in contents]

    seen = set()
    for file, candidates in subjects.items():
        for candidate in candidates:
            if candidate in seen:
                continue

            seen.add(candidate)
            programs = [file]
            candidate_counter = 1
            for file2, other in subjects.items():
                if file == file2:
                    continue

                if candidate in other:
                    programs.append(file2)
                    candidate_counter += 1
            result[candidate_counter].add(CommonSubject(name=candidate, programs=', '.join(programs)))

    return result


def find_common(prefix):
    files = []
    for file in pathlib.Path(".").iterdir():
        if file.name.startswith(prefix):
            files.append(file)
    common =  _find_common(files)

    for level, subjects in common.items():
        print("=" * 15 + f" {str(level)} " + "=" * 15)
        for index, subject in enumerate(subjects):
            print(f"{index}. {subject.name} – {subject.programs}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--find-common", action="store_true")
    args = parser.parse_args()

    if args.find_common:
        find_common(args.url)
    else:
        crawl(args.url)

if __name__ == "__main__":
    main()
