import logging
from pathlib import Path

from tqdm import tqdm
from youtube_dl import YoutubeDL

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
        downloaded = set()
        model = WikipediaWrapper(cache_dir=folders['cache'], final_tatortdir=folders['final'],
                                 pred_thresholds=pred_thresholds)

        tatorte = MediathekWrapper(cache_dir=folders['cache'], mediathek_query_size=mediathek['query_size'])

        logger.info('Creating list of Tatorts to download ')
        downloads = []
        for tatort in tatorte:
            ids = model.try_predict_id(tatort.title, tatort.description)

            target = Path(folders['tatort_store_prefix'])
            if len(ids) == 1:  # noqa
                # download file to output folder
                tid = ids[0]
                if id not in downloaded:
                    downloaded.add(tid)
                    target /= folders['output']
                    model.missing_or_smaller(tid, tatort.url)
                    downloads.append((tatort.url, target / model.filename(tid)))
            else:
                target /= folders['error']
                downloads.append(
                    (tatort.url, target / (','.join(map(str, ids)) + f' {tatort.title} – {tatort.description[:40]}')))

        logger.info('Start downloading')
        for url, dest in tqdm(downloads):
            self.download(url, dest)

    def download(self, url, dest: Path):
        dest.parent.mkdir(parents=True, exist_ok=True)
        if self.dry_run:  # noqa
            print(f'would create {dest} from {url}')
        else:
            # remove old finished files (happens if we download, because of higher quality)
            # fortunately this will not remove partial files, which youtube-dl will continue!
            dest.unlink(missing_ok=True)
            ydl_opts = dict(outtmpl=str(dest))
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
