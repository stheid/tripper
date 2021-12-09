import logging
import re
from collections import Counter
from operator import itemgetter
from pathlib import Path
from subprocess import check_output, CalledProcessError
from typing import List
from urllib.error import HTTPError

import pandas as pd
import requests
import yaml
from thefuzz import process

from tripper.util.path import older
from tripper.util.string import simplify

logger = logging.getLogger(__name__)


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
            logger.info('Downloading and processing wikipedia meta data')

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
                    .assign(id=lambda df: df.id.astype(int))
                [['id', 'title', 'team', 'airing_date', 'city', 'notes']]
                    .assign(title=lambda df: df.title.str.replace(" ?\([\d\D]*\)$", "", regex=True))
                    .assign(meta_data=lambda df: df.airing_date.str.extract('(\d{4})$', expand=False)
                                                 + ' ' + df.team + ' ' + df.city + ' ' + df.notes)
            )
            episodes.to_csv(path)  # noqa
        else:
            logger.info('Using cached wikipedia meta data')
            episodes = pd.read_csv(path)

        return episodes.set_index('id')

    def __getattr__(self, item):
        if item == 'episodes':
            return
        if hasattr(self, 'episodes'):
            return getattr(self.episodes, item)

    def missing_or_smaller(self, tatort_id: int, url: str):
        if tatort_id not in self.size_of_tatort:
            return True
        try:
            result = (
                check_output(['ffprobe', url, '-show_entries', 'format=size,duration', '-v' 'quiet', '-of', 'csv=p=0'])
                    .encode('utf-8')
            )
            if not result:
                logger.warning('ffprobe did not return filesize and duration estimate.'
                               f' The url is likely geoblocked! Skipping: {url}')
            duration, size = result.split(',')
            if duration < 80 * 60:
                logger.info('The url contains a tatort that is shorter than 80 minutes.'
                            f' That is likely not a tatort url. Skipping: {url} ')
                return False

            # existing is significantly smaller
            return self.size_of_tatort[tatort_id] * 1.2 < size
        except KeyError:
            return True
        except CalledProcessError:
            logger.error('Calling ffprobe failed. Is ffmpeg installed?')
        except HTTPError:
            logger.info(
                f'{self.filename(tatort_id)} exists, but size of the remote file could not be determined. Skipping: {url}')
            return False

    def filename(self, tatort_id: int):
        s = self.episodes.loc[tatort_id]
        return f'{tatort_id} {s.title} — {s.team} ({s.city}).mp4'

    def try_predict_id(self, title, descr) -> List[int]:
        """
        try to predict the tatort id for the given title and description.
        on

        :return: id, filename, prob: id of the tatort and the filename it it should be stored
        """
        titles_multiset = Counter(self.title)

        # there should be one and only closely matching title
        title_candidates = []
        if title in titles_multiset:
            # title is an exact match
            title_candidates.append(title)
        else:
            # we use fuzzy matching as a fallback
            fuzzy_matches = sorted(process.extract(title, set(self.title)), key=itemgetter(1), reverse=True)
            first_score = fuzzy_matches[0][1]
            for i, (title_, score) in enumerate(fuzzy_matches):
                if score > self.title_thresh or score == first_score:
                    # take the first of the list and all others that have a higher score than the threshold
                    title_candidates.append(title_)
                else:
                    # the list is sorted, so we can break if the score no longer exceeds the threshold
                    break

        id_candidates = []
        for title_ in title_candidates:
            if titles_multiset.get(title_) == 1:
                # if the title unique
                id_candidates.append(self.episodes[self.title == title_].index[0])
            else:
                # try to use description to disambiguate
                for match_, score in process.extract(descr, set(self.metadata)):
                    if score > self.desc_thresh:
                        id_candidates.append(self.episodes[self.meta_data == match_].index[0])

        return id_candidates
