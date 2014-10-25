# PageCheck
PageCheck is a tool to check if a page has changed. After every run, hashes of the web pages will be stored, and compared against in subsequent runs. PageChecker can notify you via e-mails.

# Requirements
PageCheck has no requirements outside the standard library.

# Usage
Using PageCheck is easy. Assuming you have added it to your PATH, you can add new pages to check with -a option.

    # pagecheck -a http://example.com

To remove a page, you can use the -r option.

    # pagecheck -r http://example.com

To run the actual check, all you have to do is run the script(without -a or -r options). However, the script won't have any output other than editing a json file. To see some output, you can use the -e option.

    # pagecheck -e
    1 changes found.

PageCheck also makes use of multiprocessing. By default, it will use 4 processes to download and hash pages. You can set the number of processes to use with -c option. Setting it to 1 or less will disable multiprocessing.
    # pagecheck -e -c 17
    12 changes found.

If you want a more detailed report, you can use -v option to read about everything the script does.

    # pagecheck -v
    Reading file checklist.json
    Starting to download and hash 4 pages.
    Spawning 4 processes.
    Hashing finished.
    Comparing 4 keys.
    2 differences found.

PageCheck can also send a mail over SMTP to notify you.

    # pagecheck -m "smtp.example.com:587" -u "user@example.com" -p "hunter2" -c 1 -v
    Reading file checklist.json
    Starting to hash 1 pages.
    Hashing finished.
    Comparing 1 keys.
    1 differences found.
    Sending notifications.
    Preparing message.
    Connecting to mail server.
    Logging into mail server.
    Sending the mail.
    Mail sent.
    Saving changes to the file.

You can also send the notification mail to someone else with -t option, or set a subject line with -s option.
If you want to send notifications to multiple people, just put ";" between their email addresses.

    # pagecheck -m "smtp.example.com:587" -u "user@example.com" -p "hunter2" -t "someone@example.com;else@example.com" -s "These pages have changed!"

If you want to move the checklist.json file to somewhere else, or use a different name, you can specify the file with -f option.

    # pagecheck -e -f somefile.json
    1 changes found.

You can also pick another hashing algoritm to use. PageCheck uses SHA256 by default, you can also use "md5" and "sha512".

    # pagecheck -e -g md5
    1 changes found.

# Using in your own scripts

You can easily use PageCheck in your own scripts as well. You just need to import it and create an object.

    >>> from pagecheck import PageCheck
    >>> pages = {"http://example.com":"", "https://python.org":""}
    >>> p = PageCheck(pages)
    >>> p.check_update_file()
    {'https://www.python.org': 'c647d3da8d920168cb9dc6479e5567dcb7578844849c3cbe94a9c76e767c127a',
    'http://example.com': '3587cb776ce0e4e8237f215800b7dffba0f25865cb84550e87ea8bbac838c423'}

You can also use SMTPNotify to send mail notifications as well.

    >>> from pagecheck import PageCheck, SMTPNotify
    >>> n = SMTPNotify("smtp.example.com", "user@example.com", "hunter2", "target@example.com", "Subject")
    >>> pages = {"http://example.com":"", "https://python.org":""}
    >>> p = PageCheck(pages, notifier=n)
    >>> p.check_update_file()
    {'https://www.python.org': 'c647d3da8d920168cb9dc6479e5567dcb7578844849c3cbe94a9c76e767c127a',
    'http://example.com': '3587cb776ce0e4e8237f215800b7dffba0f25865cb84550e87ea8bbac838c423'}

In fact, you can use a custom notifier. You only need a callable that accepts a dictionary. If you just want to pick another hashing algorithm from hashlib, you can use the GetHash class.

If you want to change the number of processes PageCheck uses, that can be done by setting process_count variable.

    >>> import hashlib
    >>> from pagecheck import PageCheck, GetHash
    >>> d = {"http://example.com":""}
    >>> h = GetHash(hashlib.md5)
    >>> p = PageCheck(d, hasher=h, process_count=1)
    >>> p.check_update_notify()
    {'http://example.com': '09b9c392dc1f6e914cea287cb6be34b0'}

PageCheck is licensed with GLP v3. Please see the COPYING file for details.
