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
import requests
import hashlib
import json

_DEFAULT_FILE = "checklist.json"
_DEFAULT_HASHER = hashlib.sha512


class PageCheck:
    def __init__(self, json_file, notifier, verbose=False, hasher=_DEFAULT_HASHER):
        self.notifier = notifier
        self.json_file = json_file
        self.hasher = hasher
        if verbose:
            self.print = print
        else:
            self.print = lambda x: None

    def get_hash(self, url):
        """
        Returns the hash of the page at url.
        """
        self.print("Downloading page {}".format(url))
        page = requests.get(url)
        page_text = page.text.encode("utf-8")
        self.print("Hashing page {}".format(url))
        return self.hasher(page_text).hexdigest()

    def get_hash_dict(self, url_list):
        """
        Returns a dictionary with url_list as keys, and the hashes of the pages as values.
        """
        hash_dict = {}
        self.print("Starting to hash {} pages.".format(len(url_list)))
        for url in url_list:
            hash_dict[url] = self.get_hash(url)
        self.print("Hashing finished.")
        return hash_dict

    def compare_dicts(self, first_dict, second_dict):
        """
        Compares values of two dictionaries.
        Returns a new dictionary, containing the differences.
        Values of the returned pairs will be from first_dict if the keys are present in both dictionaries.
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

    def check_update_file(self):
        """
        Read the given file. The file should be a JSON file, containing a dictionary,
        with urls as keys, and hashes of the pages as values.
        If there are any changes in any page,
        update the file and call the notification_method with differences.
        Returns the number of changed pages.
        """
        with open(self.json_file, mode="r") as opened_file:
            self.print("Reading file {}".format(self.json_file))
            old_dict = json.load(opened_file)
        new_dict = self.get_hash_dict(old_dict.keys())
        diff = self.compare_dicts(new_dict, old_dict)
        if diff != {}:
            self.print("Sending notifications.")
            self.notifier(diff)
            with open(self.json_file, mode="w") as opened_file:
                self.print("Saving changes to the file.")
                json.dump(new_dict, opened_file, indent=2)
        return len(diff)


class SMTPNotify:
    def __init__(self, server, user, password, target, subject, verbose=False):
        self.server = server
        self.user = user
        self.password = password
        self.target = target
        self.subject = subject
        if verbose:
            self.print = print
        else:
            self.print = lambda x: None

    def __call__(self, msg_dict):
        import smtplib
        from email.mime.text import MIMEText
        self.print("Preparing message.")
        message = MIMEText('\n'.join(msg_dict.keys()))
        message["Subject"] = self.subject
        message["From"] = self.user
        message["To"] = self.target
        self.print("Connecting to mail server.")
        mail_server = smtplib.SMTP(self.server)
        mail_server.starttls()
        self.print("Logging into mail server.")
        mail_server.login(self.user, self.password)
        self.print("Sending the mail.")
        mail_server.send_message(message)
        mail_server.quit()
        self.print("Mail sent.")


if __name__ == "__main__":
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
                        help="Mail address to send the notification to.")
    parser.add_argument("-s", "--subject", type=str, default="Updated Websites",
                        help="Subject string to use while sending mail notifications.")
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
        mail_notifier = SMTPNotify(args.mail, args.user, args.passw, args.target, args.subject, args.verbose)
    else:
        mail_notifier = lambda x: None

    checker = PageCheck(args.file, mail_notifier, args.verbose)
    result = checker.check_update_file()
    if args.exitmessage:
        print("{} changes found.".format(result))

    """
    mail_notify = SMTPNotify("smtp.gmail.com:587", "SeriousBug@Gmail.com", "syqg uxcf ewez qhno", "Updated websites")
    check_update_file("checklist.json", mail_notify)
    """