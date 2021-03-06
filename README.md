TRipper - a Tatort download utility
===================================

The software downloads [Tatort](https://en.wikipedia.org/wiki/Tatort) episodes from the mediathek.
The tool is aimed for people that want to create a local collection of all episodes.

TRipper comes with two data-wrappers:

1. Mediathekview - to retrieve the available episodes and their download urls

2. Wikipedia - to retrieve the metadata


Future releases will therefore also come with a scheduler such that the tool can run peridodicly.

The implementation heavily relies on ffmpeg and youtube-dl (as a python dependency)

Special thanks to the folkes at [mediathekview](https://mediathekviewweb.de) for providing an easy to use api.

Installation
------------

```bash
apt install ffmpeg # (or similar commands)
pip install git+https://github.com/stheid/tripper.git
```

to install current development version (or any other branch)
```bash
pip install git+https://github.com/stheid/tripper.git@develop
```



Usage
-----

Adapt the `config.yaml` to your liking and run the program:

```bash
tripper
```


Setting persistent systemd.service
----------------------------------

`/etc/systemd/system/tripper.service` [doc](https://man.archlinux.org/man/systemd.service.5)
```.service
[Unit]
Description=Downloading Tatort collection

[Service]
Type=oneshot
User=<user> # if this line is omited the service will be run as root
WorkingDirectory=<path where your collection resides>
ExecStart=/home/<user>/.local/bin/tripper # or whatever "which tripper" returns
```

</br>`/etc/systemd/system/tripper.timer` [doc](https://man.archlinux.org/man/systemd.timer.5)
```.service
[Unit]
Description=Downloading Tatort collection

[Timer]
OnCalendar=Sun *-*-* 20:15:00
Persistent=true

[Install]
WantedBy=timers.target
```

Execute the following lines as root
```bash
su
systemctl daemon-reload
systemctl enable --now tripper.timer
# verify using:
systemctl list-timers | grep "tripper\|UNIT"
```

Manually run systemd.service or debug service
---------------------------------------------

Run tripper service
```
sudo systemctl start --no-block tripper 
```

Inspect complete service logs
```
journalctl -b -u tripper
```

Roadmap
-------

1. Add docker image
