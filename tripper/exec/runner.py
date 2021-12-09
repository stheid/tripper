import logging
from operator import itemgetter
from pathlib import Path

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
        pred_thresholds = self.conf['pred_thresholds']
        mediathek = self.conf['mediathek']

        logger.info('Retrieving mediathek and wikipedia data')
        processed = set()
        model = WikipediaWrapper(cache_dir=folders['cache'], final_tatortdir=folders['final'],
                                 pred_thresholds=pred_thresholds)
        tatorte = MediathekWrapper(cache_dir=folders['cache'], mediathek_query_size=mediathek['query_size'])

        logger.info('Preprocessing all Tatort entries and filtering for new or higher quality versions.')
        downloads = []
        for tatort in tqdm(tatorte, total=len(tatorte)):
            ids = model.try_predict_id(tatort.title, tatort.description)

            target = Path(folders['tatort_store_prefix'])
            if len(ids) == 1:
                # download file to output folder
                tid = ids[0]
                if tid not in processed:
                    processed.add(tid)
                    target /= folders['output']
                    if model.missing_or_smaller(tid, tatort.url):
                        downloads.append((tid, tatort.url, target / model.filename(tid)))
            else:
                target /= folders['error']
                downloads.append(
                    (ids[0], tatort.url,
                     target / (','.join(map(str, ids)) + f' {tatort.title} – {tatort.description[:100]}')))

        logger.info(f'Start downloading {len(downloads)} movies')
        for _, url, dest in tqdm(sorted(downloads, key=itemgetter(0))):
            self.download(url, dest)

    def download(self, url, dest: Path):
        dest.parent.mkdir(parents=True, exist_ok=True)
        if self.dry_run:  # noqa
            logger.info(f'would create {dest} from {url}')
        else:
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
