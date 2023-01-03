# Mangaread Downloader
This script helps you to download manga from mangaread.org.

## Requirements
- Python 3.6 or higher.
- Modules: `pip install -r requirements.txt`.

## Usage
- `python mangaread.py -h` for help.
- `python mangaread.py -u "URL_MANGA"` to download the manga from the URL.

## Parameters
### -h, --help
Show the help message and exit.

```bash
python mangaread.py -h
```

### -u URL, --url URL
URL of the manga to download.

```bash
python mangaread.py -u "https://www.mangaread.org/manga/one-piece"
```

### -mn MANGA_NAME, --manga-name MANGA_NAME
Name of the manga to download. If not specified, the name will be extracted from the URL.

```bash
python mangaread.py -u "https://www.mangaread.org/manga/one-piece" -mn "One Piece"
```

### -c FORMAT, --convert FORMAT
Convert the manga to the specified format. The format can be `zip` or `cbz`.

```bash
python mangaread.py -u "https://www.mangaread.org/manga/one-piece" -c "zip"
```

### -cof, --convert-one-file
Convert the manga to one file instead of one file per chapter.

```bash
python mangaread.py -u "https://www.mangaread.org/manga/one-piece" -c "zip" -cof
```

### -t THREADS, --threads THREADS
Number of threads to use for downloading the manga. Default is 10.

This can speed up the download process.

```bash
python mangaread.py -u "https://www.mangaread.org/manga/one-piece" -t 20
```

### -f, --force
Force to download the whole manga even if chapters already exists.

```bash
python mangaread.py -u "https://www.mangaread.org/manga/one-piece" -f
```

### -d, --debug
Show debug messages.

```bash
python mangaread.py -u "https://www.mangaread.org/manga/one-piece" -d
```


## Example
Force download of the manga One Piece in cbz format in one file with 20 threads.

```bash
python mangaread.py -u "https://www.mangaread.org/manga/one-piece" -c "cbz" -cof -t 20 -f
```

Output directory will look like:
```text
./
./manga/
-------/One Piece/
-----------------/One Piece.cbz
-----------------/data.json
-----------------/Chapter 0001/
------------------------------/Chapter 0001 - 0001.jpg
------------------------------/Chapter 0001 - 0002.jpg
-----------------/Chapter 0001/...
-----------------/Chapter 0002/
------------------------------/Chapter 0002 - 0001.jpg
------------------------------/Chapter 0002 - 0002.jpg
-----------------/Chapter 0002/...
-----------------/...
```

## License
This project is open source and available under the [MIT License](LICENSE).

## Disclaimer
This script is for educational purposes and to promote the usefulness of my `modernqueue` module only. I am not responsible for any misuse of this script.

Also, I am not affiliated with mangaread.org in any way. And I do not own any of the manga downloaded with this script.

Please know that if the manga can be bought in your country, it is illegal to download it for free.
