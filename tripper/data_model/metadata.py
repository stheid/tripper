import re
from collections import Counter
from pathlib import Path
from typing import List
from urllib.error import HTTPError
from urllib.request import urlopen

import pandas as pd
import requests
import yaml
from thefuzz import process

from tripper.util.path import older
from tripper.util.string import simplify


class WikipediaWrapper:
    def __init__(self, cache_dir: str, final_tatortdir: str, pred_thresholds: dict):
        self.cache_dir = Path(cache_dir)
        self.title_thresh = pred_thresholds['title_thresh']
        self.desc_thresh = pred_thresholds['desc_thresh']
        self.size_of_tatort = {int(re.match('(\d+)', p.name)[0]): p.stat().st_size for p in
                               Path(final_tatortdir).glob('*.mp4')}
        self.episodes = self._get_wiki_tatortlist()

    def _get_wiki_tatortlist(self):
        path = self.cache_dir / 'episodes.csv'

        if not path.exists() or older(path, days=5):
            req = requests.get('https://de.wikipedia.org/wiki/Liste_der_Tatort-Folgen')

            with open(self.cache_dir / 'teams.yaml') as f:
                teams = {simplify(team): city for team, city in yaml.safe_load(f).items()}

            def _predict_city(team):
                value, prob = process.extractOne(simplify(team), teams.keys())
                return teams[value] + ('??' if prob < 80 else '?' if prob < 90 else '')

            episodes = (
                pd.read_html(req.text)[0]
                    .replace('\s', ' ', regex=True)
                    # remove the secondary table header: series "Folge" contains literal "Folge"
                    .query('Folge != "Folge"')
                    .rename(columns=dict(Folge='id', Titel='title', Ermittler='team', Erstausstrahlung='airing_date',
                                         City='city', Besonderheiten='notes'))
                    .assign(city=lambda df: [_predict_city(team) for team in df.team])
                [['id', 'title', 'team', 'airing_date', 'city', 'notes']]
                    .assign(title=lambda df: df.title.str.replace(" ?\([\d\D]*\)$", "", regex=True))
                    .assign(meta_data=lambda df: df.airing_date.str.extract('(\d{4})$', expand=False)
                                                 + ' ' + df.team + ' ' + df.city + ' ' + df.notes)
            )
            episodes.to_csv(path)  # noqa
        else:
            episodes = pd.read_csv(path).set_index('id')

        return episodes

    def __getattr__(self, item):
        return getattr(self.episodes, item)

    def missing_or_smaller(self, tatort_id: int, url: str):
        try:
            size = urlopen(url).length
            # some files will be playlist files (.m3u8). those tiny files will never be larger than existing files,
            # but we will omit redownloading anyways.

            # significantly smaller
            return self.size_of_tatort[tatort_id] * 1.2 < size
        except KeyError:
            return True
        except HTTPError:
            print(f'error estimating filesize with url. file will be skipped: {url}')

    def filename(self, tatort_id: int):
        s = self.episodes.loc[tatort_id]
        return f'{tatort_id} {s.title} — {s.team} ({s.city}).mp4'

    def try_predict_id(self, title, descr) -> List[int]:
        """
        try to predict the tatort id for the given title and description.
        on

        :return: id, filename, prob: id of the tatort and the filename it it should be stored
        """
        titles = Counter(self.title)

        # there should be one and only closely matching title
        result = []
        for title_, score in process.extract(title, set(self.title)):
            if score > self.title_thresh:
                if titles.get(title_) == 1:
                    # if the title unique
                    result.append(self.title[self.title == title_].index[0])
                else:
                    # try to use description to disambiguate
                    for match_, score in process.extract(descr, set(self.metadata)):
                        if score > self.desc_thresh:
                            result.append(self.meta_data[self.meta_data == match_].index[0])

        return result
