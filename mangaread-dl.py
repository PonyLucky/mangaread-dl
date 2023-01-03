"""
In this script we will download manga from "https://www.mangaread.org/".

We will use the following modules:
    - modernqueue
    - requests
    - bs4
    - os
    - sys
    - time
    - urllib
    - urllib.request
"""

# Importing the modules
import argparse
import requests
import bs4
import os
import json
import re
import shutil
from datetime import datetime
from modernqueue import ModernQueue
from zipfile import ZipFile

class Mangaread:
    def __init__(self, url_manga: str, name: str, nb_threads: int = 15, debug: bool = False) -> None:
        # Debug mode
        self.debug = debug
        # Url of the manga
        self.url_manga = url_manga
        # Number of threads
        self.nb_threads = nb_threads
        # Manga name
        if name != None:
            self.manga_name = name
        elif self.url_manga.endswith("/"):
            self.manga_name = self.url_manga.split("/")[-2]
            # Camel case
            self.manga_name = " ".join([word.capitalize() for word in self.manga_name.split("-")])
        else:
            self.manga_name = self.url_manga.split("/")[-1]
            # Camel case
            self.manga_name = " ".join([word.capitalize() for word in self.manga_name.split("-")])
        # Manga path
        self.manga_path = os.path.join(os.getcwd(), "mangaread-dl", self.manga_name)
        # Chapter path
        self.chapter_path = "Chapter {}/"
        # Image path
        self.image_path = "{} - {}.{}"
        # Url of the chapters
        self.url_chapters = []
        # Chapters data - Images urls and chapter names
        self.chapters = []
        # Current chapter scraped
        self.currentChapterScrapped = 0
        # Current chapter downloaded
        self.currentChapterDownloaded = 0

        # Creating the manga folder
        if not os.path.exists(self.manga_path):
            os.makedirs(self.manga_path)
        
        # Remove 'mangaread-dl.log'
        self.log_path = os.path.join(os.getcwd(), "mangaread-dl", "mangaread-dl.log")
        if os.path.exists(self.log_path):
            os.remove(self.log_path)
        
        # Loading saved data
        self._load_data()

    def print_debug(self, *args, **kwargs) -> None:
        """
        This function will print the arguments if debug is True.
        """
        if self.debug:
            print("[DEBUG]", *args, **kwargs)

            # Get current time
            now = datetime.now()
            # Format the time "YYYY-MM-DD HH:MM:SS"
            now = now.strftime("%Y-%m-%d %H:%M:%S")
            # Append to log file
            with open(self.log_path, "a") as f:
                f.write(f"[{now}] {' '.join([str(arg) for arg in args])}\n")

    def _load_data(self) -> None:
        """
        This function will load saved data of the manga if any.

        We are currently in "/manga/manga_name/".
        A file named "data.json" is created in the manga folder.
        """
        # Path of the data file
        data_path = os.path.join(self.manga_path, "data.json")
        # If the data file exists
        if os.path.exists(data_path):
            self.print_debug("! Data file found")
            # Open the data file
            with open(data_path, "r") as f:
                # Read the data file
                data = f.read()
            # Convert the data to a dict
            data = json.loads(data)
            # Set the current chapter
            self.currentChapterScrapped = data["currentChapterScrapped"]
            self.currentChapterDownloaded = data["currentChapterDownloaded"]
            # Set the chapters
            self.chapters = data["chapters"]
            self.print_debug("Data loaded:")
            self.print_debug(f"- currentChapterScrapped: {self.currentChapterScrapped}")
            self.print_debug(f"- currentChapterDownloaded: {self.currentChapterDownloaded}")
            self.print_debug(f"- chapters: {self.chapters}")

    def _save_data(self) -> None:
        """
        This function will save the data of the manga.
        """
        # Path of the data file
        data_path = os.path.join(self.manga_path, "data.json")
        # Data to save
        data = {
            "currentChapterScrapped": self.currentChapterScrapped,
            "currentChapterDownloaded": self.currentChapterDownloaded,
            "chapters": self.chapters
        }
        # Open the data file
        with open(data_path, "w") as f:
            # Write the data
            f.write(json.dumps(data, indent=4))
        # Print a message
        print("> Data saved")

    def _get_chapters(self) -> None:
        """
        This function will get the url of the chapters.
        """
        # Getting the html of the manga
        html = requests.get(self.url_manga)
        # Parsing the html
        soup = bs4.BeautifulSoup(html.text, "html.parser")
        # Getting the chapters
        # ul.main > li > a
        chapters = soup.select("ul.main > li > a")
        # Reverse the chapters
        chapters.reverse()
        self.print_debug("Chapters found:")
        self.print_debug(f"- {chapters}")
        # Getting the url of the chapters
        for chapter in chapters:
            self.url_chapters.append(chapter["href"])

    def _get_images(self) -> bool:
        """
        This function will get the url of the images.

        Returns:
            bool: True if scraping was successful, False otherwise.
        """
        def get_images_from_chapter(chapter: str, i, _self) -> dict:
            # Getting the html of the chapter
            html = requests.get(chapter)
            # Parsing the html
            soup = bs4.BeautifulSoup(html.text, "html.parser")
            # Getting the images
            # div.reading-content img
            images = soup.select("div.reading-content img")
            _self.print_debug(f"Images found for chapter {i+1}:")
            _self.print_debug(f"- {images}")

            # Get chapter name
            chapter_name = soup.select_one("h1#chapter-heading").text.split(" - ")[-1]
            _self.print_debug(f"Chapter name: {chapter_name}")

            # Remove special characters
            chapter_name = re.sub(r"[^a-zA-Z0-9 ]", "", chapter_name)

            # Get the index after "Chapter DIGITS"
            index = 0
            if chapter_name.startswith("Chapter "):
                index = re.search(r"Chapter \d+", chapter_name).end()
            # Get the chapter number and force number to 4 digits
            chapter_number = i + 1
            chapter_number = str(chapter_number).zfill(4)
            # Set the chapter name
            if chapter_name[index+1:].strip() == "":
                chapter_name = f"Chapter {chapter_number}"
            else:
                chapter_name = f"Chapter {chapter_number} - {chapter_name[index:].strip()}"

            url_images = []
            # Getting the url of the images
            for image in images:
                # Replace all "\n" and "\t", spaces with ""
                url = re.sub(r"[\n\t ]", "", image["data-src"])
                # url in is the 'data-src' attribute
                url_images.append(url)
            

            # Set current chapter
            _self.currentChapterScrapped = i + 1

            # Print a message
            print("> {} images found from '{}' - {}/{}".format(
                len(url_images),
                chapter_name,
                _self.currentChapterScrapped,
                len(_self.url_chapters))
            )

            # Return the chapter infos
            return {
                "name": chapter_name,
                "images": url_images
            }
        # If currentChapterScrapped is equal to the number of chapters and different from 0
        if self.currentChapterScrapped == len(self.url_chapters) and self.currentChapterScrapped != 0:
            # Return True
            return True
        is_finished = False
        try:
            queue = ModernQueue(max_threads=self.nb_threads)
            self.print_debug(f"Images scrapping from {self.currentChapterScrapped} to {len(self.url_chapters)}")
            # Getting the images
            for i in range(self.currentChapterScrapped, len(self.url_chapters)):
                # Url of the chapter
                chapter = self.url_chapters[i]
                queue.add(
                    func=get_images_from_chapter,
                    args={
                        "chapter": chapter,
                        "i": i,
                        "_self": self
                    }
                )
            # Run the queue
            queue.run()
            # Get the results
            results = queue.get_results()
            # Add the results to the chapters
            self.chapters.extend(results)

            # Set is_finished to True
            is_finished = True
            # Print a message
            print("> Scraping finished")
        except KeyboardInterrupt:
            # Print a message
            print("\n> Stopping...")
            print("> Found images from {} chapters".format(self.currentChapterScrapped))
        except Exception as e:
            # Print a message
            print("> An error occured: {}".format(e))
            print("> Found images from {} chapters".format(self.currentChapterScrapped))
        finally:
            # Save data
            self._save_data()

        return is_finished

    def _download_images(self) -> None:
        """
        This function will download the images.
        """
        def download_image(url_image: str, path: str, chapter_pos: int, image_pos: int) -> None:
            """
            This function will download an image.

            Args:
                url_image (str): Url of the image.
                path (str): Path of the image.
                chapter_pos (int): Position of the chapter.
                image_pos (int): Position of the image.
            """
            # Download the image
            image = requests.get(url_image)
            # Write the image
            with open(path, "wb") as f:
                f.write(image.content)
            # Print a message
            print("> Downloaded '{}' - {}/{}\n".format(
                self.chapters[chapter_pos]["name"],
                image_pos + 1,
                len(self.chapters[chapter_pos]["images"])
            ), end="")


        # Create a queue
        queue = ModernQueue(max_threads=self.nb_threads)

        # Download images
        for i in range(self.currentChapterDownloaded, self.currentChapterScrapped):
            # Infos of the chapter
            chapter = self.chapters[i]
            # Name of the chapter, without special characters
            chapter_name = chapter["name"]
            # Url of the images
            url_images = chapter["images"]
            # Path of the chapter
            chapter_path = os.path.join(self.manga_path, chapter_name)
            self.print_debug(f"Chapter path: {chapter_path}")
            # Create the chapter folder
            os.makedirs(chapter_path, exist_ok=True)
            # Change chapter name to remove title
            chapter_name = "Chapter " + chapter_name.split(" - ")[0]
            # Add tasks to the queue
            for j in range(len(url_images)):
                # Url of the image
                url_image = url_images[j]
                # Path of the image
                path = os.path.join(
                    chapter_path,
                    self.image_path.format(
                        chapter_name,
                        str(j).zfill(4),
                        url_image.split(".")[-1]
                    )
                )
                # Add the task
                queue.add(download_image, (url_image, path, i, j))
        # Get chapter downloaded before running the queue
        old_chapter_downloaded = self.currentChapterDownloaded
        try:
            self.print_debug("Running queue...")
            # Run the queue
            queue.run()
        except:
            pass
        finally:
            print("\n> Starting checking images...")
            self.print_debug(f"Checking images from chapter {old_chapter_downloaded} to {self.currentChapterScrapped}")
            chapter_completed = 0
            # For each image, Check if all images are downloaded using their size
            # If the size is 0, the image is not downloaded
            for i in range(self.currentChapterDownloaded, self.currentChapterScrapped):
                # Infos of the chapter
                chapter = self.chapters[i]
                # Name of the chapter, without special characters
                chapter_name = chapter["name"]
                # Url of the images
                url_images = chapter["images"]
                # Path of the chapter
                chapter_path = os.path.join(self.manga_path, chapter_name)
                # Print a message
                print("> Checking images from '{}' - {}/{}".format(
                    chapter_name,
                    chapter_completed + 1,
                    self.currentChapterScrapped - old_chapter_downloaded
                ))
                chapter_name = "Chapter " + chapter_name.split(" - ")[0]
                nb_images_downloaded = 0
                # Check if all images are downloaded
                for j in range(len(url_images)):
                    # Path of the image
                    path = os.path.join(
                        chapter_path,
                        self.image_path.format(
                            chapter_name,
                            str(j).zfill(4),
                            url_images[j].split(".")[-1]
                        )
                    )
                    # If the size is 0, the image is not downloaded
                    if os.path.exists(path) == False and os.path.getsize(path) == 0:
                        # Print a message
                        print("> Image {} not downloaded".format(path))
                        # Remove the image
                        os.remove(path)
                        break
                    else:
                        # Increment nb_images_downloaded
                        nb_images_downloaded += 1
                if nb_images_downloaded == len(url_images):
                    # Print a message
                    print("> All images downloaded")
                    # Increment chapter_completed
                    chapter_completed += 1
                else:
                    break
            # Set currentChapterDownloaded
            self.currentChapterDownloaded = self.currentChapterDownloaded + chapter_completed
            # Print a message
            print("> Checking finished")
            print("> {} chapters correctly downloaded".format(
                self.currentChapterDownloaded - old_chapter_downloaded
            ))
            # Save data
            self._save_data()

    def _delete_folders(self) -> None:
        """
        This function will delete the folders.
        """
        # For each chapter
        for i in range(self.currentChapterDownloaded):
            # Infos of the chapter
            chapter = self.chapters[i]
            # Name of the chapter, without special characters
            chapter_name = re.sub(r"[^a-zA-Z0-9]+", " ", chapter["name"])
            # Get the index after "Chapter DIGITS"
            index = 0
            if chapter_name.startswith("Chapter "):
                index = re.search(r"Chapter \d+", chapter_name).end()
            # Get the chapter number and force number to 4 digits
            chapter_number = i + 1
            chapter_number = str(chapter_number).zfill(4)
            # Set the chapter name
            if chapter_name[index+1:].strip() == "":
                chapter_name = f"Chapter {chapter_number}"
            else:
                chapter_name = f"Chapter {chapter_number} - {chapter_name[index:].strip()}"
            # Path of the chapter
            chapter_path = os.path.join(self.manga_path, chapter_name)
            if not os.path.exists(chapter_path):
                continue
            # Print a message
            print("> Deleting '{}'".format(chapter_name))
            # Delete the folder
            shutil.rmtree(chapter_path, ignore_errors=True)

    def _convert_to_cbz(self, one_file: bool = False) -> None:
        """
        This function will convert the images to cbz.

        Args:
            one_file (bool, optional): If True,
            all chapters will be in one cbz. Defaults to False.
        """
        # If one_file is True
        if one_file:
            # Path of the cbz
            cbz_path = os.path.join(
                self.manga_path,
                f"{self.manga_name}.cbz"
            )
            # Print a message
            print("> Converting '{}'".format(self.manga_name))
            # Create the cbz
            with ZipFile(cbz_path, "w") as cbz:
                # For each chapter
                for i in range(self.currentChapterDownloaded):
                    # Infos of the chapter
                    chapter = self.chapters[i]
                    # Name of the chapter, without special characters
                    chapter_name = re.sub(r"[^a-zA-Z0-9]+", " ", chapter["name"])
                    # Get the index after "Chapter DIGITS"
                    index = 0
                    if chapter_name.startswith("Chapter "):
                        index = re.search(r"Chapter \d+", chapter_name).end()
                    # Get the chapter number and force number to 4 digits
                    chapter_number = i + 1
                    chapter_number = str(chapter_number).zfill(4)
                    # Set the chapter name
                    if chapter_name[index+1:].strip() == "":
                        chapter_name = f"Chapter {chapter_number}"
                    else:
                        chapter_name = f"Chapter {chapter_number} - {chapter_name[index:].strip()}"
                    # Path of the chapter
                    chapter_path = os.path.join(self.manga_path, chapter_name)
                    if not os.path.exists(chapter_path):
                        continue
                    # For each image
                    for image in os.listdir(chapter_path):
                        # continue if extension is cbz, zip
                        if image.split(".")[-1] in ["cbz", "zip"]:
                            continue
                        # Path of the image
                        path = os.path.join(chapter_path, image)
                        # Add the image to the cbz
                        cbz.write(path, arcname=image)
        else:
            # For each chapter
            for i in range(self.currentChapterDownloaded):
                # Infos of the chapter
                chapter = self.chapters[i]
                # Name of the chapter, without special characters
                chapter_name = re.sub(r"[^a-zA-Z0-9]+", " ", chapter["name"])
                # Get the index after "Chapter DIGITS"
                index = 0
                if chapter_name.startswith("Chapter "):
                    index = re.search(r"Chapter \d+", chapter_name).end()
                # Get the chapter number and force number to 4 digits
                chapter_number = i + 1
                chapter_number = str(chapter_number).zfill(4)
                # Set the chapter name
                if chapter_name[index+1:].strip() == "":
                    chapter_name = f"Chapter {chapter_number}"
                else:
                    chapter_name = f"Chapter {chapter_number} - {chapter_name[index:].strip()}"
                # Path of the chapter
                chapter_path = os.path.join(self.manga_path, chapter_name)
                if not os.path.exists(chapter_path):
                    continue
                # Path of the cbz
                cbz_path = os.path.join(
                    self.manga_path,
                    f"{self.manga_name} - {chapter_name}.cbz"
                )
                # Print a message
                print("> Converting '{}' - {}/{}".format(
                    chapter_name,
                    i + 1,
                    self.currentChapterDownloaded
                ))
                # Create the cbz
                with ZipFile(cbz_path, "w") as zip:
                    for image in os.listdir(chapter_path):
                        # continue if extension is cbz, zip
                        if image.split(".")[-1] in ["cbz", "zip"]:
                            continue
                        zip.write(
                            os.path.join(chapter_path, image),
                            arcname=image
                        )

    def _convert_to_zip(self, one_file: bool = False) -> None:
        """
        This function will convert the images to zip.

        Args:
            one_file (bool, optional): If True,
            all chapters will be in one zip. Defaults to False.
        """
        # If one_file is True
        if one_file:
            # Path of the zip
            zip_path = os.path.join(
                self.manga_path,
                f"{self.manga_name}.zip"
            )
            # Print a message
            print("> Converting '{}'".format(self.manga_name))
            # Create the zip
            with ZipFile(zip_path, "w") as zip:
                # For each chapter
                for i in range(self.currentChapterDownloaded):
                    # Infos of the chapter
                    chapter = self.chapters[i]
                    # Name of the chapter, without special characters
                    chapter_name = re.sub(r"[^a-zA-Z0-9]+", " ", chapter["name"])
                    # Get the index after "Chapter DIGITS"
                    index = 0
                    if chapter_name.startswith("Chapter "):
                        index = re.search(r"Chapter \d+", chapter_name).end()
                    # Get the chapter number and force number to 4 digits
                    chapter_number = i + 1
                    chapter_number = str(chapter_number).zfill(4)
                    # Set the chapter name
                    if chapter_name[index+1:].strip() == "":
                        chapter_name = f"Chapter {chapter_number}"
                    else:
                        chapter_name = f"Chapter {chapter_number} - {chapter_name[index:].strip()}"
                    # Path of the chapter
                    chapter_path = os.path.join(self.manga_path, chapter_name)
                    if not os.path.exists(chapter_path):
                        continue
                    # For each image
                    for image in os.listdir(chapter_path):
                        # continue if extension is cbz, zip
                        if image.split(".")[-1] in ["cbz", "zip"]:
                            continue
                        # Path of the image
                        path = os.path.join(chapter_path, image)
                        # Add the image to the zip
                        zip.write(path, arcname=image)
        else:
            # For each chapter
            for i in range(self.currentChapterDownloaded):
                # Infos of the chapter
                chapter = self.chapters[i]
                # Name of the chapter, without special characters
                chapter_name = re.sub(r"[^a-zA-Z0-9]+", " ", chapter["name"])
                # Get the index after "Chapter DIGITS"
                index = 0
                if chapter_name.startswith("Chapter "):
                    index = re.search(r"Chapter \d+", chapter_name).end()
                # Get the chapter number and force number to 4 digits
                chapter_number = i + 1
                chapter_number = str(chapter_number).zfill(4)
                # Set the chapter name
                if chapter_name[index+1:].strip() == "":
                    chapter_name = f"Chapter {chapter_number}"
                else:
                    chapter_name = f"Chapter {chapter_number} - {chapter_name[index:].strip()}"
                # Path of the chapter
                chapter_path = os.path.join(self.manga_path, chapter_name)
                if not os.path.exists(chapter_path):
                    continue
                # Path of the zip
                zip_path = os.path.join(
                    self.manga_path,
                    f"{self.manga_name} - {chapter_name}.zip"
                )
                # Print a message
                print("> Converting '{}' - {}/{}".format(
                    chapter_name,
                    i + 1,
                    self.currentChapterDownloaded
                ))
                # Create the zip
                with ZipFile(zip_path, "w") as zip:
                    for image in os.listdir(chapter_path):
                        # continue if extension is cbz, zip
                        if image.split(".")[-1] in ["cbz", "zip"]:
                            continue
                        zip.write(
                            os.path.join(chapter_path, image),
                            arcname=image
                        )

    def download(self, force: bool = False) -> bool:
        """
        This function will download the manga.

        Args:
            force (bool): If True, the whole manga will be downloaded again.

        Returns:
            bool: True if the download is successful, False otherwise.
        """
        # If force is True, we will download the whole manga again
        if force:
            # Print a message
            print("> Force download")
            # Set currentChapterDownloaded to 0
            self.currentChapterDownloaded = 0
            # Set currentChapterScrapped to 0
            self.currentChapterScrapped = 0

        self.print_debug("Getting chapters")
        # Scrap the chapters
        self._get_chapters()
        self.print_debug("Getting chapters done")

        # If current downloaded chapters is equal to number of chapters scrapped
        # We don't need to download the manga again
        if self.currentChapterScrapped != 0 and self.currentChapterDownloaded == self.currentChapterScrapped:
            print("> Manga already downloaded")
            print("There is no new chapter")
            return True
        
        self.print_debug("Getting images")
        # Scrap the images
        is_successful = self._get_images()
        self.print_debug("Getting images done")

        # If the scrapping of the images is not successful
        # Ask the user if he wants to try again or download found chapters
        if not is_successful:
            # Print a message
            print("> Failed to scrap images")

            ok = False
            while ok == False:
                print("'y' to try again ; 'n' to download found chapters ; 'stop' to stop the program")
                # Ask the user
                answer = input("Do you want to try again ? (y/n/stop) ")
                # If the answer is yes
                if answer.lower() == "y":
                    ok = True
                    # Try again
                    self.download(force)
                    return True
                # If the answer is no
                elif answer.lower() == "n":
                    # Download found chapters
                    ok = True
                # If the answer is stop
                elif answer.lower() == "stop":
                    ok = True
                    # Stop the program
                    return False

        # Set currentChapterDownloaded
        old_chapter_downloaded = self.currentChapterDownloaded

        self.print_debug("Downloading images")
        # Download the images
        self._download_images()
        self.print_debug("Downloading images done")

        # Print a message
        print("> Download finished")
        print("> {} new chapters downloaded".format(
            self.currentChapterDownloaded - old_chapter_downloaded
        ))

        # Return True
        return True

    def convert(self, format: any, convert_one_file: bool = False) -> None:
        """
        This function will convert the manga to the given format.

        Args:
            format (any): The format to convert the manga to.
        """
        # If format is None, we don't need to convert the manga
        if format == None:
            return
        # new line
        print()
        # Check if fomat is a string
        if not isinstance(format, str):
            # Print a message
            print("> Format must be a string")
            print("> Available formats : cbz, zip")
            return
        # Print a message
        print("> Converting to {}".format(format))
        # If format is cbz
        if format == "cbz":
            # Convert the manga to cbz
            self._convert_to_cbz(convert_one_file)
        # If format is zip
        elif format == "zip":
            # Convert the manga to zip
            self._convert_to_zip(convert_one_file)
        else:
            # Print a message
            print("> Unknown format")
            return
        # Print a message
        print("> Conversion finished")

        # Ask the user if he wants to delete the folders
        ok = False
        while ok == False:
            print("'y' to delete folders ; 'n' to keep folders")
            # Ask the user
            answer = input("Do you want to delete the image folders ? (y/n) ")
            # If the answer is yes
            if answer.lower() == "y":
                ok = True
                # Delete the folders
                self._delete_folders()
            # If the answer is no
            elif answer.lower() == "n":
                ok = True
            else:
                print("> Unknown answer")

    def print_output_dir(self):
        """
        This function will print the output directory.
        """
        print("> Output directory : {}".format(self.manga_path))


if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description="Download manga from mangadex")
    # Add the arguments
    parser.add_argument("-u", "--url", type=str, help="Url of the manga")
    parser.add_argument("-mn", "--manga-name", type=str, help="Friendly name of the manga.", default=None)
    parser.add_argument("-f", "--force", action="store_true", help="Force download")
    parser.add_argument("-t", "--threads", type=int, help="Number of threads", default=15)
    parser.add_argument("-c", "--convert", type=str, help="Convert the manga to: cbz, zip", default=None, choices=["cbz", "zip"])
    parser.add_argument("-cof", "--convert-one-file", action="store_true", help="Convert the manga to one file")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    # Parse the arguments
    args = parser.parse_args()

    # If the url is not given
    url = None
    name = None
    convert = None
    if args.url == None:
        # Ask the user
        while True:
            url = input("Url of the manga: ")
            if url != "":
                break
        name = input("Name of the manga (optional): ")
        while True:
            convert = input("Convert to cbz or zip (optional): ")
            if convert == "" or convert == "cbz" or convert == "zip":
                break
    else:
        url = args.url
        name = args.manga_name
        convert = args.convert


    # Create the manga object
    manga = Mangaread(url_manga=url, name=name, nb_threads=args.threads, debug=args.debug)
    # Download the manga
    success = manga.download(args.force)
    # Convert the manga
    if success:
        manga.convert(convert, args.convert_one_file)
        manga.print_output_dir()

    # Wait for a key press
    input("\nPress any key to exit...")
