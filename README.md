# Twitter Personas Using Python and Alchemy API

Sign up for a [Twitter API key](https://apps.twitter.com/)

Sign up for [Watson AI Platform](https://www.ibm.com/watson/developer/)

Add the Twitter handles you want to analyse to the file named `usernames.txt`

Sample contents for `usernames.txt`:

```
LinusTech
MKBHD
```

Add the API keys you created to the file named `config.json`. See `config.example.json` for an example.

Run script: `python get_tweets.py`

## Package as Windows Executable

To build using py2exe, download the [binary installer](http://sourceforge.net/projects/py2exe/files/py2exe/0.6.9/).

From outside your virual environment run:
```
$ python setup.py py2exe
```
