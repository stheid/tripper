import json
import logging
from pathlib import Path

import pandas as pd
import requests

from tripper.util.path import older

logger = logging.getLogger(__name__)


class MediathekWrapper:
    def __init__(self, cache_dir: str, mediathek_query_size: int):
        self.cache_dir = Path(cache_dir)
        self.mediathek_query_size = mediathek_query_size
        self.mediathek = self._get_mediathek()

    def _get_mediathek(self):
        logger.info('Preprocessing Mediathek data')
        path = self.cache_dir / 'mediathek.csv'

        if not path.exists() or older(path, days=1):
            res = requests.post('https://mediathekviewweb.de/api/query',
                                headers={'Content-Type': 'text/plain'},
                                data=json.dumps({"queries": [{
                                    "fields": ["topic", "title"],
                                    "query": "tatort"}],
                                    "sortBy": "timestamp", "sortOrder": "desc", "offset": 0, 'future': True,
                                    "size": self.mediathek_query_size,
                                    'duration_min': 84 * 60, 'duration_max': 92 * 60}))

            df = pd.json_normalize(res.json()['result']['results'])
            logger.info('Downloaded data from mediathekview')

            mediathek = (
                df.set_index('id')
                    .assign(url=lambda df_: df_.url_video_hd.replace('', pd.NA).fillna(df_.url_video))
                    .drop(columns=['url_video', 'url_video_low', 'url_video_hd', 'url_website', 'url_subtitle',
                                   'filmlisteTimestamp'])
                    # the sorting is important, so that ARD is always favoured when dropping duplicate (A is the first character)
                    .sort_values(["channel"])
                    .drop(columns=['channel', 'duration'])
                    .drop_duplicates(subset='url')
                    .query(
                    "(topic.str.contains('Tatort') or title.str.contains('Tatort'))"
                    " and not topic.str.contains('AD | Tatort') and not topic.str.contains('Audiodeskription')"
                    " and not (title.str.contains('Hörfassung') or title.str.contains('Audiodeskription')"
                    " or title.str.endswith('(AD)') or title.str.startswith('AD | ')"
                    " or title.str.contains('Gebärdensprache'))"
                    " and not url.str.contains('hallohessen')"
                    " and not topic.str.contains('Einstein')"
                    " and not topic.str.contains('DOK') and not topic.str.contains('Doku')"
                    " and not topic.str.contains('Polizeiruf 110') and not title.str.contains('Polizeiruf 110')",
                    engine="python")
                    .assign(title=lambda df: df.title.str.replace("^Tatort: ", "", regex=True)
                            .replace("^Tatort (-|–) ", "", regex=True)
                            .replace(" \| tatort$", "", regex=True)
                            .replace(" ?\(ab \d+ Jahre\)$", "", regex=True)
                            .replace(" ?\(FSK \d+\)$", "", regex=True)
                            .replace(" ?\(\d+\)$", "", regex=True)
                            .replace("^«(?P<x>[\w\s]*)» – [\S\s]*$", "\g<x>", regex=True)
                            )
                [['title', 'description', 'url', 'timestamp']]
            )

            logger.info('Processed data from mediathekview')

            mediathek.to_csv(path)  # noqa
        else:
            mediathek = pd.read_csv(path)
            logger.info('Using cached mediathekview data')

        return mediathek

    def __iter__(self):
        for index, row in self.mediathek.iterrows():
            yield row
