from tripper.data_model import MediathekWrapper


def test__get_mediathek():
    for tatort in MediathekWrapper(cache_dir='tmp', mediathek_query_size=1):
        print(tatort)
