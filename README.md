# WhisperOSC

This is a modified script from https://github.com/davabase/whisper_real_time to send the transcription to VRChat through OSC!

> This app requires you to have FFMpeg installed and added to your PATH
> ### This app requires Python 3.10 to be installed. Using pythong 3.11 will fail the installation
> This app requires you to have git installed to install the dependencies

Before running the app, make sure to install the dependencies by running the INSTALLREQUIREMENTS.bat file


There's different AI models to use, the better they are the more accurate the transcription, but the more performance and **VRAM** required. Play around with them to find what works best for you. I recommend base.

|  Size  | Parameters | Required VRAM | Relative speed |
|:------:|:----------:|:-------------:|:--------------:|
|  tiny  |    39 M    |     ~1 GB     |      ~32x      |
|  base  |    74 M    |     ~1 GB     |      ~16x      |
| small  |   244 M    |     ~2 GB     |      ~6x       |
| medium |   769 M    |     ~5 GB     |      ~2x       |
| large  |   1550 M   |    ~10 GB     |       1x       |

If you toggle Non English mode, it's a "language free" mode. This means that you can speak in whatever language you like, and it'll just work. You can switch language to language from one sentence to another. However, since the AI needs to identify the language it can get it wrong. If you're only going to speak english, stick to having it off.

To launch the app, double click the LaunchApp.vbs file :D