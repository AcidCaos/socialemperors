# Linux

:warning: To play on GNU/Linux, you have to run the server from source.

You will need:

- A browser with Flash support (see [Flash Chromium browser](#flash-chromium-browser) section).
- Adobe Flash Player installed (see [Flash Player for Linux Pepper](#flash-player-for-linux-pepper) section).

## Flash Chromium browser

Download a Chromium version with PPAPI support.
<br>Tested with version *86.0.4240.75*, which can be downloaded [here](https://chromium.cypress.io/linux/stable/86.0.4240.75).

Fancy trying other versions? Here are some relevant Linux Chromium release comments:

| Version | Date | Comment |
| --- | --- | --- |
| 54.0.2840 | October 2016 | The message "Right-click to play Adobe Flash Player" now appears<br>while pages with Adobe Flash Player are loading. |
| 56.0.2924 | January 2017 | Adobe Flash Player is automatically blocked for most sites that<br>require the plugin. |
| 87.0.4280 | November 2020 | Flash Player end of support notifications now displaying at every<br>launch unless Flash is disabled. |

## Flash Player for Linux Pepper

Download `flashplayer32_0r0_371_linuxpep.x86_64.tar.gz` from the [32.0.0.371 archive](https://archive.org/download/flashplayerarchive/pub/flashplayer/installers/archive/fp_32.0.0.371_archive.zip/).
<br>For 32-bit, download `flashplayer32_0r0_371_linuxpep.i386.tar.gz`.

Extract its contents to `/usr/lib/adobe-flashplugin`

## Running Chromium with PPAPI Flash

Run the chrome binary with `--ppapi-flash-path=/usr/lib/adobe-flashplugin/libpepflashplayer.so`
<br>and `--ppapi-flash-version=32.0.0.371` flags.

*Note:* To avoid providing those flags every time, you might want to set `CHROMIUM_FLAGS`.
