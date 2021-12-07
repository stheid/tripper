from pathlib import Path
from urllib.request import urlretrieve

from tqdm import tqdm

from tripper.data_model import MediathekWrapper, WikipediaWrapper


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

        downloaded = set()
        model = WikipediaWrapper(cache_dir=folders['cache'], final_tatortdir=folders['final'],
                                 pred_thresholds=pred_thresholds)

        tatorte = MediathekWrapper(cache_dir=folders['cache'], mediathek_query_size=mediathek['query_size'])

        for tatort in tqdm(tatorte, total=len(tatorte)):
            ids = model.try_predict_id(tatort.title, tatort.description)

            target = Path(folders['tatort_store_prefix'])
            if len(ids) == 1:  # noqa
                # download file to output folder
                tid = ids[0]
                if id not in downloaded:
                    downloaded.add(tid)
                    target /= folders['output']
                    model.missing_or_smaller(tid, tatort.filesize)
                    self.download(tatort.url, target / model.filename(tid))
            else:
                target /= folders['error']
                self.download(tatort.url, target / ','.join(map(str, ids)))

    def download(self, url, dest: Path):
        dest.mkdir(parents=True, exist_ok=True)
        if self.dry_run:  # noqa
            print(f'would create {dest} from {url}')
        else:
            urlretrieve(url, dest)
