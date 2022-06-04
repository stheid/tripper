import logging
import re
from operator import itemgetter
from pathlib import Path

from requests import get, RequestException
from tqdm import tqdm
from youtube_dl import YoutubeDL
from youtube_dl.utils import DownloadError

from tripper.data_model import MediathekWrapper, WikipediaWrapper

logger = logging.getLogger(__name__)


class Runner:
    def __init__(self, conf):
        for attr, value in conf['general'].items():
            setattr(self, attr, value)

        del conf['general']
        self.conf = conf

    def run(self):
        folders = self.conf['folders']
        Path(folders['cache']).mkdir(parents=True, exist_ok=True)
        pred_thresholds = self.conf['pred_thresholds']
        mediathek = self.conf['mediathek']

        logger.info('Retrieving mediathek and wikipedia data')
        processed = dict()
        model = WikipediaWrapper(cache_dir=folders['cache'], final_tatortdirs=[folders['final'], folders['output']],
                                 pred_thresholds=pred_thresholds)
        tatorte = MediathekWrapper(cache_dir=folders['cache'], mediathek_query_size=mediathek['query_size'])

        logger.info('Preprocessing all Tatort entries and filtering for new or higher quality versions.')
        downloads = dict()
        check_downloads = []
        for tatort in tqdm(tatorte, total=len(tatorte)):
            ids = model.try_predict_id(tatort.title, tatort.description)

            if len(ids) == 1:
                # download file to output folder
                tid = ids[0]
                new_size = model.get_size_if_missing_or_smaller(tid, tatort.url)
                if new_size is not None and new_size > processed.get(tid, 0):
                    processed[tid] = new_size
                    downloads[tid] = (tatort, model.filename(tid))
            else:
                check_downloads.append((tatort.url, f'{tatort.title} – {tatort.description[:100]}.mp4'))

        if downloads:
            logger.info(f'Start downloading {len(downloads)} movies')
            target = Path(folders['tatort_store_prefix']) / folders['output']
            for _, (tatort, dest) in tqdm(sorted(downloads.items(), key=itemgetter(0), reverse=True), disable=None):
                self.download(tatort.url, target / dest.replace('/', '⧸'))

                try:
                    # subtitle
                    r = get(tatort.url_subtitle)
                    mapping = [('.*text/xml.*', 'ttml'), ('.*', 'vtt')]
                    suffix = [suff for pat, suff in mapping if re.match(pat, r.headers['content-type'])][0]
                    with open(target / (dest.replace('/', '⧸')[:-3] + suffix), 'w') as f:
                        print(r.text, file=f)
                except RequestException:
                    logger.warning(f'Was not able to download subtitle for {tatort.title}')

        if check_downloads:
            logger.info(f'Start downloading {len(check_downloads)} check/error movies')
            target = Path(folders['tatort_store_prefix']) / folders['error']
            for url, dest in tqdm(check_downloads):
                self.download(url, target / dest.replace('/', '⧸'), overwrite=False)

    def download(self, url, dest: Path, overwrite=True):
        dest.parent.mkdir(parents=True, exist_ok=True)
        if self.dry_run:  # noqa
            logger.info(f'would create {dest} from {url}')
        else:
            if overwrite:
                # remove old finished files (happens if we download, because of higher quality)
                # fortunately this will not remove partial files, which youtube-dl will continue!
                dest.unlink(missing_ok=True)
            ydl_opts = dict(outtmpl=str(dest), retries=5,
                            external_downloader_args=['-hide_banner', '-loglevel', 'panic'])
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            except DownloadError:
                logger.error(f'Failed to download {dest}. Skipping {url}')
