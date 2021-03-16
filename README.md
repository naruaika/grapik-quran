# Grapik Quran

In the name of Allah, the Entirely Merciful, the Especially Merciful. This proof-of-concept application is specially made for the GNOME desktop. We use Quran images from [Quran Complex](https://qurancomplex.gov.sa/) to provide the same experience of reading a non-digital Quran. For Quran indexes, texts (Uthmani), and translations are from [Tanzil](http://tanzil.net). Here's a prototype of the app:

![Application's propotype](screenshot.png)

## Features

Using this app, you'll be able to:

- Open any Quran variant (8 variants in 5 qira'at)
- Read the full Quran
- Navigate to any specific page/surah/ayah/juz
- Read translation in 39 languages
- Select and copy (by pressing `ctrl+C`) the selected ayah(s) as text

## Background

All I'd like to do is have a digital Quran app installed on my desktop. I know very well that there are many great apps on mobile—such as [Quran for Android](https://play.google.com/store/apps/details?id=com.quran.labs.androidquran) and [Al Quran (Tafsir & by Word)](https://play.google.com/store/apps/details?id=com.greentech.quran)—or the web—such as [Ayat](https://quran.ksu.edu.sa/index.php#aya=1_1&m=hafs&qaree=husary&trans=ar_mu) and [Quran.com](https://quran.com/)—, but I just want one on the desktop at the moment.

Why not just use the [Ayat](https://quran.ksu.edu.sa/ayat/?l=en) app desktop version which was officially developed by KSU? Unfortunately, due to [Adobe AIR](https://en.wikipedia.org/wiki/Adobe_AIR) has reached [end of life](https://www.adelaide.edu.au/technology/your-services/software/adobe-air-end-of-life) on December 31, 2020, we won't be able to get it from the official GNU/Linux distro's repository. Not to mention that Adobe has decided to [no longer support](https://helpx.adobe.com/air/kb/install-air-2-64-bit.html) Adobe AIR for Linux desktop as of June 14, 2011. So, it has been such a pain to install Ayat on Linux since then.

There are many alternatives to Ayat, such as [Zekr](https://sourceforge.net/projects/zekr/), [Elforkane](https://github.com/zakariakov/elforkane), and [Albasheer](https://github.com/yucefsourani/albasheer-electronic-quran-browser). But they don't feel as great as Ayat to me. That's why I've been working hardly on **Grapik Quran** to meet my personal needs. Also that's not less important is learning to develop a real app from people as being open source.

## Motivation

I used to be a user of Sabily OS and I've been amazed how wonderful it is. May Allah forgive me all along the way by doing this project and I ask Allah for His _taufiq_ and _hidayah_ to the straight path.

## Contribution

The easiest way for beginners is clone this repository to your local computer, then build and run it using [GNOME Builder](https://wiki.gnome.org/Apps/Builder). To enable GTK Inspector, run `gsettings set org.gtk.Settings.Debug enable-inspector-keybinding true` in the runtime terminal.
