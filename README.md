#PageCheck
PageCheck is a tool to check if a page has changed. After every run, hashes of the web pages will be stored, and compared against in subsequent runs.

#Requirements
Outside standard library, PageCheck requires requests library, which can be found on pip.

    # pip install requests

#Usage
Using PageCheck is easy. Assuming you have added it to your PATH, you can add new pages to add with -a option.

    # pagecheck -a http://example.com

To remove a page, you can use the -r option.

    # pagecheck -r http://example.com

To run the actual check, all you have to do is run the script(without -a or -r options). However, the script won't have any output other than editing a json file. To see some output, you can use the -e option.

    # pagecheck -e
    1 changes found.

If you want a more detailed report, you can use -v option to read about everything the script does.

    # pagecheck -v
    Reading file checklist.json
    Starting to hash 1 pages.
    Downloading page http://example.com
    Hashing page http://example.com
    Hashing finished.
    Comparing 1 keys.
    0 differences found.
    No changes found.

PageCheck can also send a mail over SMTP to notify you.

    # pagecheck -m "smtp.example.com:587" -u "user@example.com" -p "hunter2" -v
    Reading file checklist.json
    Starting to hash 1 pages.
    Downloading page http://example.com
    Hashing page http://example.com
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

    # pagecheck -m "smtp.example.com:587" -u "user@example.com" -p "hunter2" -t "someone_else@example.com" -s "These pages have changed!"

You can easily use PageCheck in your own scripts as well. You just need to import it and create an object.

    >>> from pagecheck import PageCheck
    >>> p = PageCheck("file.json", print)
    >>> p.check_update_file()
    {'http://example.com': 'ddf40ddbc3887566ad782ea04cc6a4cbd5bc5db159fe9baa91b773cd7cc0c30498efdfb9fe7524ec1c2ded1e8513544c5a6703e0785d0bfd6aeca4be603701ff'}
    1

You can also use SMTPNotify to send mail notifications as well.

    >>> from pagecheck import PageCheck, SMTPNotify
    >>> n = SMTPNotify("smtp.example.com", "user@example.com", "hunter2", "target@example.com", "Subject")
    >>> p = PageCheck("file.json", n)
    >>> p.check_update_file()
    1

In fact, you can use a custom notifier. Just give it a callable that accepts a dictionary.
By default, PageCheck uses SHA512 to hash the pages. You can change this as well.

    >>> from pagecheck import PageCheck
    >>> import hashlib
    >>> p = PageCheck("file.json", print, hasher=hashlib.md5)
    >>> p.check_update_file()
    {'http://example.com': '09b9c392dc1f6e914cea287cb6be34b0'}
    1

PageCheck is licensed with GLP v3. Please see the COPYING file for details.
