"""
    PageCheck, checks web pages for changes and sends notifications.
    Copyright (C) 2014  Kaan Genç

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import urllib.request
import hashlib
import json
import multiprocessing

_DEFAULT_FILE = "checklist.json"
_DEFAULT_HASHLIB_ALGORITHM = hashlib.sha256
_DEFAULT_NOTIFIER = lambda x: None
_DEFAULT_PROCESS_COUNT = 4


class GetHash:
    """A class that downloads and hashes pages when called."""
    def __init__(self, hashlib_algorithm=_DEFAULT_HASHLIB_ALGORITHM):
        """
        Args:
            hashlib_algorithm: The algorithm from hashlib to use.
                The default is hashlib.sha512, as denoted by _DEFAULT_HASHLIB_ALGORITHM.
        """
        self.algorithm = hashlib_algorithm

    def __call__(self, url):
        """Returns a tuple of the url and the hash of the page.

        Args:
            url: A URL to a page. It should start with 'http://' or 'https://'.
                HTTPS connections will be made, but no verification is done on the certificate.

        Returns:
            A tuple of the url, and hash of the page.
            For example:
            (http://example.com", "09b9c392dc1f6e914cea287cb6be34b0")
         """
        page = urllib.request.urlopen(url)
        page_text = page.read()
        return url, self.algorithm(page_text).hexdigest()


class PageCheck:
    """A class to manage the dictionary mapping the URLs to hashes."""
    def __init__(self, page_dict, notifier=_DEFAULT_NOTIFIER,
                 verbose=False, hasher=GetHash(),
                 process_count=_DEFAULT_PROCESS_COUNT):
        """
        Args:
            page_dict: A dictionary with keys as URLs, and the values as hashes of the
                pages referenced by the URLs. For example:
                {"http://example.com": "09b9c392dc1f6e914cea287cb6be34b0",
                 "https://www.python.org/": "b2cc0b046167c335127408b5fe2b5d9b"}
            notifier: A callable that accepts a dictionary like the dictionary given to page_dict.
                When check_update_notify method is called, notifier will be given
                such a dictionary, containing the pages that have change since the last run
                with their new hashes.
            verbose: A True or False value. If True, then PageCheck will print messages for many actions it takes.
            hasher: A callable that returns the hash of the page when given an URL. By default, this is
                GetHash created with its default values.
            process_count: Number of processes that should be created when downloading and hashing pages.
                If set to a value lower than 2, multiprocessing will not be used at all.
        """
        self.notifier = notifier
        self.page_dict = page_dict
        self.hasher = hasher
        self.process_count = process_count
        if verbose:
            self.print = print
        else:
            self.print = lambda x: None

    def get_hash_dict(self, url_list):
        """Returns a dictionary with url_list as keys, and the hashes of the pages as values."""
        self.print("Starting to download and hash {} pages.".format(len(url_list)))
        if self.process_count > 2:  # Use multiprocessing
            with multiprocessing.Pool(processes=self.process_count) as hash_pool:
                self.print("Spawning {} processes.".format(self.process_count))
                hash_dict = dict(hash_pool.map(self.hasher, url_list))
        else:  # Do not use multiprocessing
            hash_dict = {}
            for url in url_list:
                returnedurl, hash_dict[url] = self.hasher(url)
        self.print("Hashing finished.")
        return hash_dict

    def diff_dict(self, first_dict, second_dict):
        """Compares values of two dictionaries.

        Values for matching keys are compared to find differences. The keys that exist in one dictionary,
        but not the other are also treated as differences.

        Args:
            first_dict: The first dictionary to compare. If keys with different values are found,
                the returned dictionary will take its value from this dictionary.
            second_dict: The second dictionary to compare.

        Returns:
            A dictionary contaning the pages that have changed, with keys as URLs and values as hashes.
            For example, comparing:

            first_dict = {"https://www.python.org/": "b2cc0b046167c335127408b5fe2b5d9b"}
            second_dict = {"https://www.python.org/": "53e99a6a74d9f1005df462285329a6f6",
                           "http://example.com": "09b9c392dc1f6e914cea287cb6be34b0"}

            will result in:
                {"https://www.python.org/": "b2cc0b046167c335127408b5fe2b5d9b",
                 "http://example.com": "09b9c392dc1f6e914cea287cb6be34b0"}
        """
        diff = {}
        all_keys = set(list(first_dict.keys()) + list(second_dict.keys()))
        self.print("Comparing {} keys.".format(len(all_keys)))
        for key in all_keys:
            # Key found in first, but not the second
            if key not in second_dict.keys():
                diff[key] = first_dict[key]
            # Key found in second, but not first
            elif key not in first_dict.keys():
                diff[key] = second_dict[key]
            # Key found in both, value is different
            elif first_dict[key] != second_dict[key]:
                diff[key] = first_dict[key]
        self.print("{} differences found.".format(len(diff)))
        return diff

    def check_update_notify(self, run_silent=False):
        """Check the self.page_dict to find if any pages have changed.

        If there are any changes in any of the pages, the dictionary will be updated and
        self.notifier will be called with the changes.
        Finally, a dictionary containing the changed pages will be returned.

        Args:
            run_silent: If this is set to True, the notifier will not be called if some pages have changed.
                self.page_dict will still be updated.

        Returns:
            A dictionary containing the changed pages, and their new hashes. For example:

            {
            "http://example.com": "ddf40d...701ff",
            "http://another.com/some_page.html": "adf21...2ka4as"
            }
        """
        new_dict = self.get_hash_dict(self.page_dict.keys())
        diff = self.diff_dict(new_dict, self.page_dict)
        if diff != {} and not run_silent:
            self.notifier(diff)
        self.page_dict = new_dict
        return diff

    def load_json(self, path_to_file):
        """Load self.page_dict from a json file.

        The file should contain a dictionary, with keys as URLs to the pages,
        and values as hashes of these pages or empty strings. For example:
        {
            "http://example.com": "ddf40d...701ff",
            "http://another.com/some_page.html": ""
        }
        Please note that the file is not checked to see if it fits to this format,
        and it is possible to load a JSON file that will cause errors during the page requests.

        Args:
            path_to_file: A string containing the file path. The file will be opened read-only.

        Raises:
            OSError: The file at path_to_file does not exist or otherwise is inaccessible.
            ValueError: The file at path_to_file is not a valid JSON file.
        """
        with open(path_to_file, mode="r") as file:
            self.page_dict = json.load(file)
        return True

    def save_json(self, path_to_file):
        """Save self.page_dict into a json file.

        Args:
            path_to_file: A string containing the file path. The file will be truncated before writing.

        Raises:
            OSError: The file at path_to_file does not exist and can't be created, or
                the file is inaccessible.
        """
        with open(path_to_file, mode="w") as file:
            json.dump(self.page_dict, file, indent=2)
        return True


class SMTPNotify:
    """A class that sends a mail over SMTP."""
    def __init__(self, server, user, password, target, subject, use_tls=True, verbose=False):
        """
        Args:
            server: The server to connect to send the mail.
                For example: "smtp.example.com:587"
            user: The username to use when authenticating. Use an empty string to skip authentication.
            password: The password to use when authenticating. Use an empty string to skip authentication.
            target: Recipients of the mail, the "To" address. Accepts a single string, or a list of strings.
            subject: The subject line of the mail.
            use_tls: If set to False, then TLS will not be used.
            verbose: If True, then SMTPNotify will print messages about the actions it takes as it runs.
        """
        self.server = server
        self.user = user
        self.password = password
        self.target = target
        self.use_tls = use_tls
        self.subject = subject
        if verbose:
            self.print = print
        else:
            self.print = lambda x: None

    def __call__(self, msg_dict):
        """Send the mail.

        Args:
            msg_dict: A dictionary. Keys of this dictionary will be sent as the message.

        Returns:
            A dictionary, containing one entry for each recipient that was refused.
            If the dictionary is empty, all recipients have received the mail.
            See smtplib.SMTP.sendmail for details.
        """
        import smtplib
        from email.mime.text import MIMEText
        self.print("Preparing message.")
        message = MIMEText('\n'.join(msg_dict.keys()))
        message["Subject"] = self.subject
        message["From"] = self.user
        message["To"] = self.target
        self.print("Connecting to mail server.")
        mail_server = smtplib.SMTP(self.server)
        if self.use_tls:
            self.print("Enabling TLS.")
            mail_server.starttls()
        if not all((self.user == "", self.password == "")):
            self.print("Logging into mail server.")
            mail_server.login(self.user, self.password)
        self.print("Sending the mail.")
        refused = mail_server.send_message(message)
        mail_server.quit()
        self.print("Mail sent.")
        return refused


def _main():
    """The function that will be called when the script is run, rather than imported."""
    import argparse
    parser = argparse.ArgumentParser(description="Check websites for changes.")
    parser.add_argument("-v", "--verbose", action="store_true", default=False,
                        help="Output messages to explain scripts actions as it runs.")
    parser.add_argument("-e", "--exitmessage", action="store_true", default=False,
                        help="Prints a line in the end to explain the result, independent of --verbose.")
    parser.add_argument("-f", "--file", type=str, default=_DEFAULT_FILE,
                        help="The file containing pages to check.")
    parser.add_argument("-a", "--add", type=str, default="",
                        help="Add given websites to the file and exit without checking.")
    parser.add_argument("-r", "--remove", type=str, default="",
                        help="Remove given website from the file and exit without checking.")
    parser.add_argument("-m", "--mail", type=str, default="",
                        help="Set to a SMTP server in form of example.com:587 to enable mail notifications.")
    parser.add_argument("-u", "--user", type=str, default="",
                        help="User mail address to use while connecting to SMTP.")
    parser.add_argument("-p", "--passw", type=str, default="",
                        help="Password to use while connecting to SMTP.")
    parser.add_argument("-t", "--target", type=str, default="",
                        help="Mail address to send the notification to. Either a single mail address, or a list of"
                             "addresses separated with ; .")
    parser.add_argument("-s", "--subject", type=str, default="Updated Websites",
                        help="Subject string to use while sending mail notifications.")
    parser.add_argument("-c", "--processcount", type=int, default=_DEFAULT_PROCESS_COUNT,
                        help="Number of processes to use while downloading and hashing.")
    parser.add_argument("-g", "--hashingalgorithm", type=str, default="sha256",
                        help="Hashing algorithms to use. Possible values are md5, sha256, sha512.")
    args = parser.parse_args()
    if args.verbose:
        vprint = print
    else:
        vprint = lambda x: None

    if args.add != "" or args.remove != "":
        with open(args.file, mode="r") as file:
            vprint("Reading file {}".format(args.file))
            saved_dict = json.load(file)
        if args.add != "":
            saved_dict[args.add] = ""
            vprint("Added key {} to file.".format(args.add))
        if args.remove != "":
            try:
                del saved_dict[args.remove]
                vprint("Removed key {} from file.".format(args.remove))
            except KeyError:
                vprint("Key to remove not found!")
        with open(args.file, mode="w") as file:
            vprint("Writing changes to the file.")
            json.dump(saved_dict, file, indent=2)
        exit()

    if args.mail != "":
        if args.target == "":
            args.target = args.user
        else:
            args.target = args.target.strip(";")
        mail_notifier = SMTPNotify(args.mail, args.user, args.passw, args.target, args.subject, args.verbose)
    else:
        mail_notifier = lambda x: None

    hashalg = _DEFAULT_HASHLIB_ALGORITHM
    if args.hashingalgorithm == "md5":
        hashalg = hashlib.md5
    elif args.hashingalgorithm == "sha256":
        hashalg = hashlib.sha256
    elif args.hashingalgorithm == "sha512":
        hashalg = hashlib.sha512

    checker = PageCheck({}, mail_notifier, args.verbose, hasher=GetHash(hashalg), process_count=args.processcount)
    checker.load_json(args.file)
    result = checker.check_update_notify()
    if len(result) > 0:
        checker.save_json(args.file)
    if args.exitmessage:
        print("{} changes found.".format(len(result)))


if __name__ == "__main__":
    _main()