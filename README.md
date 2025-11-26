# What is it?

This is script for removing filenames from Recently Played list in VLC Playeron MacOS.

# How to use

Call script with arguments.

`--drop-ext` to remove references to played files with this extension 

`--drop-dir` to remove references to played files inside specified directory

**Sample:**
removing files with extensions "mp3" * "flac" along with files inside "~/tmp" directory
 
```
python3 vlc_recent_cleanup.py --drop-ext mp3 --drop-ext flac --drop-dir ~/tmp/
```

# Other platforms:

Feel free to fork-then-alter script paths and filenames accroding to VLC documentation:

https://images.videolan.org/support/faq.html#Config
