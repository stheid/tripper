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

```
$> apt install ffmpeg # (or similar commands)
$> pip install git+git://github.com/stheid/tripper.git
```


Usage
-----

Adapt the `config.yaml` to your liking and run the program:

```
$> tripper
```


Setting persistent systemd.service
----------------------------------


```
/etc/systemd/system/tripper.service
———————————————————————————————————
[Unit]
Description=Downloading Tatort collection

[Service]
Type=oneshot
User=<user> # if this line is omited the service will be run as root
WorkingDirectory=<path where your collection resides>
ExecStart=/home/<user>/.local/bin/tripper # or whatever "which tripper" returns
Work
```

```
/etc/systemd/system/tripper.timer
———————————————————————————————————
[Unit]
Description=Downloading Tatort collection

[Service]
OnCalendar=Mon *-*-* 20:15:00
Persistent=true

[Install]
WantedBy=timers.target
```

Execute the following lines as root
```
$> su
$> systemctl daemon-reload
$> systemctl start tripper.timer
$> systemctl enable tripper.timer
# verify using:
$> systemctl list-timers
```

[documentation systemd.service](https://man.archlinux.org/man/systemd.service.5)

[documentation systemd.timer](https://man.archlinux.org/man/systemd.timer.5)


Roadmap
-------

1. Add docker image


