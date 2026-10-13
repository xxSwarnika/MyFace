import os
import logging
from datetime import datetime
from flask import Flask, g, request, session
from markupsafe import Markup


def load_or_generate_secrets(app: Flask):
    """Load secrets from `secrets.cfg`, or generate it from `_secrets.tmpl` with a random secret key."""
    secrets_path = os.path.join(app.instance_path, f"secrets{'_debug' if app.debug else ''}.cfg")
    tmpl_path = os.path.join(app.template_folder or "", "_secrets.tmpl")

    if not os.path.exists(secrets_path) and os.path.exists(tmpl_path):
        generated_secret_key = None  # replace with code that actually makes a securely random secret key
        if generated_secret_key:
            with open(tmpl_path, "r") as infile:
                data = infile.read()
            # IMPORTANT: use 'x' to avoid overwriting file if it has been created by a concurrent process
            with open(secrets_path, "x") as outfile:
                outfile.write(data.replace("SECRET_KEY=None", f"SECRET_KEY='{generated_secret_key}'"))
                app.logger.info("Wrote new secret key to %s", secrets_path)

    app.logger.info("attempting to load secrets from '%s'", secrets_path)
    if os.path.exists(secrets_path):
        app.config.from_pyfile(secrets_path)
    else:
        app.logger.info("no secrets file '%s'", secrets_path)



class LogFilter(logging.Filter):
    def filter(self, record):
        try:
            # record.isotime = datetime.now().astimezone().isoformat(sep='T')
            record.isotime = datetime.now().isoformat(sep="T", timespec="seconds")
            record.remote_addr = ""
            record.url = ""
            record.log_ref = ""
            record.sep = " "
            if request:
                record.remote_addr = f"{request.remote_addr or '(unknown)':15s} "
                record.url = f'"{request.path or '-path-'}"'

            record.user = f"{'(anon)':8s} "
            if session:
                # we don't use current_user, otherwise we risk an infinite loop if get_user uses the logger
                record.user = f"{session.get('username', '(anon)'):8s} "

            if g:
                record.log_ref = f"#{getattr(g, 'log_ref', 0):04} "
                record.sep = "\n"
            # record.args = util.mask_secrets(record.args)
        except Exception as e:
            print("log filter failed: ", e)
            pass
        return True


def setup_logging(app: Flask):
    from flask.logging import default_handler

    app.logger.removeHandler(default_handler)
    format = "{log_ref}{isotime} {remote_addr}{user} {url} {funcName}:{lineno}{sep}{log_ref}{levelname:8s} {message}"
    _streamHandler = logging.StreamHandler()
    _streamHandler.setLevel(logging.DEBUG)
    _streamHandler.addFilter(LogFilter())
    try:
        # use colors in console log if we have coloredlogs installed
        import coloredlogs

        _streamHandler.setFormatter(coloredlogs.ColoredFormatter(format, style="{"))
    except:
        _streamHandler.setFormatter(logging.Formatter(format, style="{"))

    handlers: list = [_streamHandler]
    app.logger.addHandler(_streamHandler)

    log_dir = app.config.get("LOG_DIR") or app.instance_path
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{app.name}.log")
    _fileHandler = logging.FileHandler(log_file, "a")
    _fileHandler.setLevel(logging.DEBUG)
    _fileHandler.addFilter(LogFilter())
    _fileHandler.setFormatter(logging.Formatter(format, style="{"))
    app.logger.addHandler(_fileHandler)
    handlers.append(_fileHandler)
    print("logging to", log_file)

    # logging.basicConfig(level=logging.DEBUG, encoding="utf-8",format=format, style='{', handlers=[_fileHandler,_streamHandler])


footers = {
    "about": {
        "linktitle": "About",
        "title": "Our Story",
        "content": Markup(
            """
<p>After years of never-ending ostehøvel cuts, University budgets were getting strained.
In order to secure more funding for new courses and activities, we at the Department of Informatics
decided to build an innovative new web app aimed at the lucrative social media market.
                          
<p>After an extensive naming competition among our students, we settled on <em>MyFace™</em> — a name that we feel reflects our vision
for the future, while still respecting the traditions of legacy sites. Our original plan was to go with just <code>Å</code>, but unfortunately
Elon Musk had already picked up the domain name for his new orbital ride share service.

<p>We hope you enjoy MyFace™, and if you have any questions, please hesitate to <a href="contect">contact us!</a>
<p><em>— The MyFace™ Team</em>
"""
        ),
    },
    "accessibility": {
        "linktitle": "Accessibility",
        "title": "Accessibility Statement",
        "content": Markup("We're fully non-compliant with <a href='https://www.w3.org/WAI/standards-guidelines/wcag/'>WCAG 2.2</a>!"),
    },
    "careers": {
        "linktitle": "Careers",
        "title": "Work with us!",
        "content": Markup(
            '<a href="https://www.uib.no/en/about/84777/vacant-positions-uib">See all open MyFace positions</a>'
        ),
    },
    "contact": {"linktitle": "Contact", "title": "Contact Us", "content": Markup("<em>Please don't!</em>")},
    "press": {"linktitle": "Press", "title": "Press Info", "content": "To be added"},
    "privacy": {
        "linktitle": "Privacy",
        "title": "Privacy Statement",
        "content": Markup("At MyFace, Inc., we care about your privacy..."),
    },
}
