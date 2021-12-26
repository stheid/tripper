import logging
import re
from collections import Counter
from importlib import resources
from operator import itemgetter
from pathlib import Path
from shutil import which
from subprocess import check_output, CalledProcessError
from typing import List, Optional, Tuple
from urllib.error import HTTPError
from urllib.request import urlopen

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
        self.filesize_estimator = FilesizeEstimator()

    def _get_wiki_tatortlist(self):
        path = self.cache_dir / 'episodes.csv'

        if not path.exists() or older(path, days=5):
            logger.info('Downloading and processing wikipedia meta data')

            req = requests.get('https://de.wikipedia.org/wiki/Liste_der_Tatort-Folgen')

            teams_s = resources.read_text('tripper.resources', 'teams.yaml')
            teams = {simplify(team): city for team, city in yaml.safe_load(teams_s).items()}

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

    def get_size_if_missing_or_smaller(self, tatort_id: int, url: str) -> Optional[float]:
        duration, size = self.filesize_estimator(url)

        if size is None:
            return None

        if duration is not None and duration < 80 * 60:
            logger.info('The url contains a video that is shorter than 80 minutes.'
                        f' That is likely not a tatort url. Skipping: {url} ')
            return None

        if tatort_id not in self.size_of_tatort or self.size_of_tatort[tatort_id] * 1.2 < size:
            # missing or existing is significantly smaller
            return size
        return None

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


class FilesizeEstimator:
    methods = ['ffmpeg', 'fallback']

    def __init__(self):
        self.method = 'fallback' if which('ffprobe') is None else 'ffmpeg'
        self.succesfull_methods = dict()

    def __call__(self, url, *args, **kwargs):
        return self.get_filesize(url)

    def get_filesize(self, url) -> Tuple[Optional[float], Optional[float]]:
        """

        :param url:
        :return: duration if known, approximate filesize
        """
        if self.method == 'ffmpeg':
            try:
                result = (
                    check_output(
                        ['ffprobe', url, '-show_entries', 'format=size,duration', '-v', 'quiet', '-of', 'csv=p=0'])
                        .decode('utf-8')
                )
                if not result:
                    logger.warning('ffprobe did not return filesize and duration estimate.'
                                   f' The url is likely geoblocked! Skipping: {url}')
                self.succesfull_methods['ffmpeg'] = True
                return tuple([float(entry) for entry in result.split(',')])  # noqa
            except CalledProcessError as e:
                logger.warning(f'Calling ffprobe failed. Maybe a 404 error. Skipping {url}')
                return None, None

        try:
            size = urlopen(url).length
            if size < 1000000:
                direct_url = check_output(['youtube-dl', url, '-g']).decode('utf-8')
                if 'geoblock' in direct_url or 'geoprotect' in direct_url:
                    logger.info(f'The url is geoblocked. Skipping {url}')
                    return None, None
            return None, size
        except HTTPError:
            logger.warning(f'Calling ffprobe failed. Maybe a 404 error. Skipping {url}')

            return None, None
