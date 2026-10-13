import logging
import os, atexit, json, itertools
import flask, secrets, apsw
import re
from base64 import b64decode
from box import Box
from datetime import date
from http import HTTPStatus
import time
import urllib.parse
from typing import Optional
from flask import (
    Flask,
    Response,
    abort,
    g,
    jsonify,
    redirect,
    request,
    send_from_directory,
    make_response,
    render_template,
    session,
    url_for,
)
import flask_login
from flask_login import LoginManager, UserMixin, current_user, login_required
from urllib.parse import urlparse
from werkzeug.exceptions import HTTPException
from werkzeug.datastructures import WWWAuthenticate
from werkzeug.security import generate_password_hash, check_password_hash
from .util import load_or_generate_secrets, setup_logging, footers
from .login_form import LoginForm
from .profile_form import ProfileForm
from authlib.integrations.flask_client import OAuth

db: Optional[apsw.Connection] = None
app: Flask
oauth: OAuth
#mindre eller lik 8 tegn med sto,små bokstaver og tall
PASSWORD_RE = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$') 

def is_strong_password(pw: str) -> bool:
    return bool (pw and PASSWORD_RE.match(pw))

def require_strong_password(pw: str):
    if not pw:
        flask.flash("Password cannot be empty.", category ="error")
        abort(HTTPStatus.BAD_REQUEST, description="Empty password")
    if not is_strong_password(pw):
        flask.flash("Password must be 8 chars + inlcude: lowercase, uppercase and a digit.", category="error")
        abort(HTTPStatus.BAD_REQUEST, description = "Weak password")

def ensure_hashed(pw: str) -> str:
    """If pw is not already a Werkzeug hash, then we can hash it now (PBKDF+salt)"""
    if pw and not str(pw).startswith("pbkdf2:"):
        return generate_password_hash(pw)
    return pw


#-------Validation helpers ---------
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{3}([0-9a-fA-F]{3})?$")
def is_safe_abs_http_url(url: str) -> bool:
    """Allow only absoulte http(s) URLs or empty string"""
    if not url:
        return True
    try:
        u = urllib.parse.urlparse(url)
        return u.scheme in {"http", "https"} and bool (u.netloc)
    except Exception:
        return False
    
def validate_profile_inputs(picture_url: str, color: str, about: str): 
    if picture_url and not is_safe_abs_http_url(picture_url):
        flask.flash ("Picture URL must be absolute http(s).", "error")
        abort (HTTPStatus.BAD_REQUEST, description = "Invalid picture URL")

    if color and not HEX_COLOR_RE.match(color):
        flask.flash("Color must be hex like #RRGGBB.", "error")
        abort (HTTPStatus.BAD_REQUEST, description="About too long")


#--------Access contorl helpers---------
def are_buddies_one_way(src_id: int, dst_id: int) -> bool:
        """Return true is src_if has added dst_id as buddy (one-way grant)."""
        row = sql_execute(
            "SELECT 1 FROM buddies WHERE user1_id = ? AND user2_id =?;",
        (src_id, dst_id),
        ).fetchone()
        return bool(row)

def can_view_full_profile(viewer_id: int, target_id: int) -> bool:
        """Viewer can see full profile if they are the target og target has added viewer as buddy"""
        if viewer_id == target_id:
            return True
        return are_buddies_one_way(target_id, viewer_id)

def sanitize_user_for_view (viewer_id: int, user: "User") -> dict:
        """Return pnly allowed fields for this viewer."""
        base ={"id": user.id, "username": user.username}
        if can_view_full_profile(viewer_id, user.id):
            base.update({
                "name": user.get("name"),
                "birthdate": user.get("birthdate"),
                "color": user.get("color"),
                "picture_url": user.get("picture_url"),
                "about": user.get("about"),
            })
        return base



################################
# Class to store user info
# UserMixin provides us with an `id` field and the necessary methods (`is_authenticated`, `is_active`, `is_anonymous` and `get_id()`).
# Box makes it behave like a dict, but also allows accessing data with `user.key`.
class User(UserMixin, Box):
    def __init__(self, user_data):
        super().__init__(user_data)

    def save(self):
        """Save this user object to the database"""
        if "password" in self and self.password:
            self.password = ensure_hashed(self.password)
        #pakk alt annet enn id/username/passsword inn i JSON
        info = json.dumps({k: self[k] for k in self if k not in ["username", "password", "id"]})
        if "id" in self:
            # TODO: maybe only SET the fields that have changed?
            sql_execute(
                "UPDATE users SET username = ?, password = ?, info = ? WHERE id = ?;",
                (self.username, self.password, info, self.id),
                )
        else: 
            sql_execute(
                "INSERT INTO users (username, password, info) VALUES (?, ?, ?);",
                (self.username, self.password, info),
            )
            self.id = db.last_insert_rowid()

    def add_token(self, name=""):
        """Add a new access token for a user"""
        token = secrets.token_urlsafe(32)
        sql_execute(
            "INSERT INTO tokens (user_id, token, name) VALUES (?, ?, ?);",
            (self.id, token, name),
            )

    def delete_token(self, token):
        """Delete an access token"""
        sql_execute(
            "DELETE FROM tokens WHERE user_id = ? AND token = ?;",
            (self.id, token),
            )

    def get_tokens(self):
        """Retrieve all access tokens belonging to a user"""
        return sql_execute(
            "SELECT token, name FROM tokens WHERE user_id = ?;",
            (self.id,),
            ).fetchall()

    @staticmethod
    def get_token_user(token):
        """Retrieve the user who owns a particular access token"""
        row = sql_execute(
            "SELECT user_id FROM tokens WHERE token = ?;",
            (token,),
        ).fetchone()
        if row:
            return User.get_user(row[0])
        return None

    @staticmethod
    def get_user(userid):
        if isinstance(userid, int) or (isinstance(userid, str) and userid.isnumeric()):
            row = sql_execute(
                "SELECT id, username, password, info FROM users WHERE id = ?;",
                (int(userid),),
            ).fetchone()
        else:
            row = sql_execute(
                 "SELECT id, username, password, info FROM users WHERE username = ?;",
                 (userid,),
                 ).fetchone()
        if row:
            user = User(json.loads(row[3]))
            user.update({"id": row[0], "username": row[1], "password": row[2]})
            return user
        else:
            return None  



################################
# Set up app

def create_app(test_config=None):
    global app
    app = Flask("myface", instance_relative_config=True)

#---- Cookie & secret hardening ---
    app.config.setdefault('SESSION_COOKIE_NAME','myface_session')
    app.config.setdefault('SESSION_COOKIE_HTTPONLY', True)
    app.config.setdefault('SESSION_COOKIE_SAMESITE','Lax')
    app.config.setdefault('SESSION_COOKIE_SECURE', not app.debug)

    if not app.config.get("SECRET_KEY"):
        env_key = os.environ.get("MYFACE_SECRET_KEY")
        if env_key:
            app.config["SECRET_KEY"] = env_key
        elif app.debug:
            app.config["SECRET_KEY"] = "dev-only-not-secret"
        else:
            raise RuntimeError ("SECRET_KEY missing: set MYFACE_SECRET_KEY")

    # ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Pick appropriate values for these
    # app.config['SESSION_COOKIE_NAME'] =
    # app.config['SESSION_COOKIE_SAMESITE'] =
    # app.config['SESSION_COOKIE_SECURE'] =
    # app.config['SESSION_COOKIE_HTTPONLY'] =

    # You can also load app configuration from a Python file
    if os.environ.get("MYFACE_SETTINGS"):
        app.logger.info("Loading config from %s", os.environ.get("MYFACE_SETTINGS"))
        app.config.from_envvar("MYFACE_SETTINGS")  # file name in environment variable

    # special config for running tests
    if test_config:
        app.config.from_mapping(test_config)

    # load config from environment variables starting with MYFACE_
    app.config.from_prefixed_env("MYFACE")

    # logging
    request_counter = itertools.count(start=0, step=1)  # used for numbered log entries
    setup_logging(app)
    logger = app.logger

    # Where to find stuff
    app.template_folder = os.path.normpath(os.path.join(app.root_path, app.config.get("TEMPLATE_DIR", "templates")))
    app.static_folder = os.path.normpath(os.path.join(app.root_path, app.config.get("STATIC_DIR", "static")))
    logger.setLevel(logging.DEBUG)
    logger.info("Starting MyFace")
    logger.debug("template folder: %s", app.template_folder)
    logger.debug("static folder: %s", app.static_folder)
    logger.debug("instance path: %s", app.instance_path)

    # The secret key enables storing encrypted session data in a cookie (TODO: make a secure random key for this! and don't store it in Git!)
    load_or_generate_secrets(app)
    if app.debug and not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"]= "mY s3kritz"

    app.logger.info(
    "OIDC cfg present? client_id=%s, client_secret=%s",
    bool(app.config.get("GITLAB_CLIENT_ID")),
    bool(app.config.get("GITLAB_CLIENT_SECRET")),
)


   #------- Authlib OAuth / OIDC ----------
    oauth = OAuth(app)
    oauth.register(
        name ="gitlab",
        client_id=app.config.get("GITLAB_CLIENT_ID"),
        client_secret=app.config.get("GITLAB_CLIENT_SECRET"),
        server_metadata_url ="https://git.app.uib.no/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid profile email"},
    )
    
    # open the database file
    app.oauth = oauth

    with app.app_context():
        sql_init()

    ################################
    # Set up for login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    # name of the function / view that generates the login page
    login_manager.login_view = "login"  # type: ignore

    @app.before_request
    def csrf_same_origin_guard():
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("Origin")
            if origin:
                origin_host = urllib.parse.urlparse(origin).netloc
                req_host = request.host
                if origin_host != req_host:
                    abort (HTTPStatus.FORBIDDEN, description="Cross-sire request blocked")

    @login_manager.user_loader
    def user_loader(user_id):
        """Called whenever the login manager needs to get the User object for a given user id.

        For example, when it finds the id of a logged in user in the session data (session['_user_id'])
        """
        app.logger.info("looking for user %s", user_id)
        user = User.get_user(user_id) 
        if user:
            session["username"] = user.username
        return user

    @login_manager.request_loader
    def request_loader(request):
        """This method is called to get a User object based on a request.

        For example, if using an api key or authentication token rather
        than getting the user name the standard way (from the session cookie)
        """
        # Even though this HTTP header is primarily used for *authentication*
        # rather than *authorization*, it's still called "Authorization".
        auth = request.headers.get("Authorization")

        # If there is not Authorization header, do nothing, and the login
        # manager will deal with it (i.e., by redirecting to a login page)
        if not auth:
            return
        
        try:
            (auth_scheme, auth_params) = auth.split(maxsplit=1)
        except ValueError:
            abort (HTTPStatus.UNAUTHORIZED, www_authenticate=WWWAuthenticate("Basic realm=myface, Bearer"))

        auth_scheme = auth_scheme.casefold()

        if auth_scheme == "basic":  # Basic auth has username:password in base64
            # TODO: maybe remove this, it's probably a bad idea to implement Basic authentication anyway
            if not app.debug:
                abort(HTTPStatus.UNAUTHORIZED, www_authenticate= WWWAuthenticate("Bearer"))
            try:
                up = b64decode(auth_params.encode(errors="ignore")).decode(errors="ignore")
                uname, passwd = up.split(":", maxsplit=1)
            except Exception:
                abort (HTTPStatus.UNAUTHORIZED, www_authenticate=WWWAuthenticate ("Basic realm=myface"))
            u = User.get_user(uname)
            if u and check_password_hash(u.password, passwd):
                return u
            
        elif auth_scheme == "bearer": 
            token = auth_params.strip()
            u = User.get_token_user(token)
            if u:
                return u
             # Bearer auth contains an access token;
            # an 'access token' is a unique string that both identifies
            # and authenticates a user, so no username is provided (unless
            # you encode it in the token – see JWT (JSON Web Token), which
            # encodes credentials and (possibly) authorization info)
    
         # probably also a bad idea to print the token in the debug log
            # TODO: implement bearer authentication
        # For other authentication schemes, see
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication

        # If we failed to find a valid Authorized header or valid credentials, fail
        # with "401 Unauthorized" and a list of valid authentication schemes
        # (The presence of the Authorized header probably means we're talking to
        # a program and not a user in a browser, so we should send a proper
        # error message rather than redirect to the login page.)
        # (If an authenticated user doesn't have authorization to view a page,
        # Flask will send a "403 Forbidden" response, so think of
        # "Unauthorized" as "Unauthenticated" and "Forbidden" as "Unauthorized")
        abort(
            HTTPStatus.UNAUTHORIZED,
            www_authenticate=WWWAuthenticate("Bearer"),
        )

    ################################
    # ROUTES – these get called to handle requests
    #
    #    Before we get this far, Flask has set up a session store with a session cookie, Flask-Login
    #    has dealt with authentication stuff (for routes marked `@login_required`), and the
    #    before_request() function has been called
    #
    #    Request data is available as global context variables, so you don't need to pass it
    #    around as arguments:
    #      * request – current request object
    #      * session – current session (stores arbitrary session data in a dict-like object)
    #      * g – can store whatever data you like while processing the current request
    #      * current_user – a User object with the currently logged in user (if any)

    @app.get("/")
    @app.get("/index.html")
    @login_required
    def index_html():
        """Render the home page"""
        # any keyword arguments to render_template will become variables
        # we can use inside the template
        return render_template("home.html", var1="value1")

    @app.get("/info/<name>")
    def info(name : str):
        """"""
        info = footers.get(name)
        if info:
            return render_template("_generic_info.html", info=info)
        else:
            abort(404)

    @app.route("/login/", methods=["GET", "POST"])
    def login():
        """Render (GET) or process (POST) login form"""

        logger.debug("/login/ session: %s", session)

        form = LoginForm()

        if not form.next.data:
            # if we got a `next` query parameter, add it to the form so we can redirect the user back to the page they started on
            form.next.data = flask.request.args.get("next")

        if form.is_submitted():
            logger.debug(
                f"Received form:\n    %s\n%s, errors=%s",
                form.data,
                "INVALID" if not form.validate() else "valid",
                form.errors,
            )
            if form.validate():
                username = form.username.data
                password = form.password.data
                user = user_loader(username) #injection?
                if user and (check_password_hash(user.password, password) or user.password == password):
                    if user.password == password:
                        user.password = generate_password_hash (password)
                        user.save()
                    return login_user_and_redirect(user)
                else:
                    logger.error("Invalid username or password for '%s': user=%s", username, user)
                    flask.flash(f"Invalid username or password!", category='error')
            elif form.errors.get('csrf_token'):
                logger.warning('CSRF timeout')
                flask.flash('Form timed out, please try again', category='warning')
            # other form errors are displayed automatically by the template
        return render_template("login.html", form=form)
    
   #login_user_and_redirect
    def login_user_and_redirect(user : User):
        # Login and set session cookie
        flask_login.login_user(user)

        logger.info("User %s logged in successfully.", user.username)
        # a 'flash' is a message to the user that can be rendered on the web page
        flask.flash(f"User {user.username} logged in successfully.")

        # we're done; redirect to front page or the page the user tried to visist
        next_url = get_safe_redirect_url() or url_for("index_html")
        logger.info("redirecting to %s", next_url)
        return redirect(next_url)
    
    @app.get("/logout/")
    def logout():
        if current_user and not current_user.is_anonymous:
            username = current_user.username
            flask_login.logout_user()
            logger.info(f"User {username} logged out successfully.")
        return redirect(url_for("index_html"))

    @app.route("/profile/", methods=["GET", "POST", "PUT"]) #her

    @login_required
    def profile():
        """Display or edit user's profile info"""
        logger.debug("%s /profile/ – current user: %s", request.method, current_user)

        form = ProfileForm()
        if form.is_submitted():
            logger.debug(
                f"Received form:\n    %s\n%s errors=%s",
                form.data,
                "INVALID" if not form.validate() else "valid",
                form.errors,
            )
            if form.validate():
                if form.password.data:  # change password if user set it
                    # TODO: should be protect the user against inadvertent password changes?
                    require_strong_password(form.password.data)
                    current_user.password = generate_password_hash(form.password.data)
                if form.birthdate.data:  # change birthday if set
                    current_user.birthdate = form.birthdate.data.isoformat()
                # TODO: do we need additional validation for these?
                current_user.name = form.name.data
                current_user.color = form.color.data
                current_user.picture_url = form.picture_url.data
                current_user.about = form.about.data
                validate_profile_inputs(
                    picture_url=form.picture_url.data or "",
                    color=form.color.data or "",
                    about=form.about.data or "",
                )
                current_user.save()
                logger.info("Updated user %s", current_user.username)
            elif form.errors.get('csrf_token'):
                logger.warning('CSRF timeout')
                flask.flash('Form timed out, please try again', category='warning')
            else:
                pass  # The profile.html template will automatically display any errors in form.errors
        else:  # fill in the form with the user's info
            form.username.data = current_user.username
            form.password.data = ""
            form.password_again.data = ""
            # only set this if we have a valid date
            form.birthdate.data = current_user.get("birthdate") and date.fromisoformat(current_user.get("birthdate"))
            form.name.data = current_user.get("name", "")
            form.color.data = current_user.get("color", "")
            form.picture_url.data = current_user.get("picture_url", "")
            form.about.data = current_user.get("about", "")

        return render_template("profile.html", form=form, user=current_user)  # template variables in action!

#-----------Buddy----------

    @app.post("/buddies/<int:userid>")
    @login_required
    def add_buddy(userid: int):
        if userid == current_user.id:
            abort(HTTPStatus.BAD_REQUEST, description = "Cannot buddy yourself.")
        target = User.get_user(userid)
        if not target:
            abort(404)
        sql_execute(
            "INSERT OR IGNORE INTO buddies (user1_id, user2_id) VALUES (?, ?);",
            (current_user.id, userid),
        )
        return jsonify({"status": "ok", "message": "Buddy added"})
    
    @app.delete("/buddies/<int:userid>")
    @login_required
    def remove_buddy(userid: int):
        sql_execute(
            "DELETE FROM buddies WHERE user1_id = ? AND user2_id = ?;",
            (current_user.id, userid),
        )
        return jsonify({"status": "ok", "message": "Buddy removed"})

    @app.get("/buddies/<int:userid>/status")
    @login_required
    def buddy_status(userid: int):
        """Helper for UI badges/buttons."""
        one_way_from_user = are_buddies_one_way(userid, current_user.id)
        i_granted = are_buddies_one_way(current_user.id, userid)
        mutual = one_way_from_user and i_granted
        return jsonify({"one_way_from_user": one_way_from_user, "i_granted": i_granted, "mutual": mutual})

#-------------User API----------
    
    @app.get("/users/")
    @login_required
    def get_users():
        """Retrieve the list of users."""
        rows = sql_execute("SELECT id, username FROM users;").fetchall()

        result = []
        for row in rows:
            user = User({"id": row[0], "username": row[1]})
            result.append(user)

        if prefers_json():
            return jsonify(result)
        else:
            return render_template("_users.html", users=result)

    @app.get("/users/<userid>")
    @login_required
    def get_user(userid):
        if userid == "me":
            u = current_user
        else:
            u = User.get_user(userid)

        if not u:
            abort(404)
        sanitized = sanitize_user_for_view(current_user.id, u)
        if prefers_json():
            return jsonify(sanitized)
        else:
            return render_template("_users.html", users=[sanitized])

    ################################
    # OpenID Connect endpoints (not fully implemented)
    @app.route("/login/gitlab")
    def login_gitlab():
        """
        Start the OIDC login: redirecting the user to GitLab's authorization endpoint.
        We preserve the 'next' URL (if any) so we can send the useer back after login. 
        """

        session["login_next"] = get_safe_redirect_url()

        redirect_uri = url_for("login_callback", _external=True)
        return app.oauth.gitlab.authorize_redirect(redirect_uri)
      # TODO: get the correct authorization endpoint URL from authlib
        
    

    @app.route("/login/callback")
    def login_callback():

        """
        OIDC callback:exchange code for tokens, read userinfo, log the user in
        (create a local user if needed), then redirect to home or the savec 'next'.
        """
        try:
            token = app.oauth.gitlab.authorize_access_token()
            # TODO: use authlib to get the access token
        except Exception as e:
            app.logger.exception("OIDC token exchange failed")
            flask.flash("Login with GitLab failed.", category="error")
            return redirect(url_for("login"))
        
        userinfo = token.get("userinfo") or {}
        sub = userinfo.get ("sub")
        preferred_username = userinfo.get("preferred_username") or userinfo.get("nickname")
        full_name = userinfo.get("name")
        picture = userinfo.get("picture")
        email = userinfo.get("email")

        if not sub:
            flask.flash("Login failed: missing subject.", category="error")
            return redirect(url_for("login"))
        
        local_username = f"gitlab:{preferred_username or sub}"

        user = User.get_user(local_username)
        if not user:
            user = User({
                "username": local_username,
                "password": generate_password_hash(secrets.token_urlsafe(24)),
                "name": full_name or "",
                "picture_url": picture or "",
            })
            user.save()

        changed = False
        if full_name and user.get("name") != full_name:
            user.name = full_name; changed = True
        if picture and user.get("picture_url") != picture:
            user.picture_url = picture; changed = True
        if changed:
            user.save()
        
        return login_user_and_redirect(user)

        
        
    @app.before_request
    def before_request():
        """This will be run at the start of every request, before the route function is called."""
        # used by logger so it's easy to see which messages belong to the same request
        g.log_ref = next(request_counter)
        # can be used to allow particular inline scripts with Content-Security-Policy
        g.csp_nonce = secrets.token_urlsafe(32)

    # Can be used to set HTTP headers on the responses
    @app.after_request
    def after_request(response: Response):
        """This will be run at after the route function returns."""
        # response.headers["Content-Security-Policy"] = …
        return response

    @app.route("/favicon.ico")
    def favicon_ico():
        return send_from_directory(app.static_folder or "", "favicon.ico", mimetype="image/vnd.microsoft.icon")

    # For full RFC2324 compatibilty
    @app.get("/coffee/")
    def nocoffee():
        abort(418)

    @app.route("/coffee/", methods=["POST", "PUT"])
    def gotcoffee():
        return "Thanks!"

    ################################
    # Set up standard template context
    @app.context_processor
    def template_context():
        return dict(footers=footers)

    ################################
    # Request context management

    @app.teardown_appcontext
    def teardown_db(exception):
        """Make sure we close the database cursor"""
        cursor = g.pop("cursor", None)

        if cursor is not None:
            cursor.close()

    ################################
    # Setup for the shell
    # (start with `flask -A myface shell`)

    @app.shell_context_processor
    def history_setup():
        """Save Flask shell command line history in a file."""
        app.logger.debug("history_setup")
        import readline

        histfile = os.path.join(app.instance_path, ".flask_shell_history")
        try:
            readline.read_history_file(histfile)
            # default history len is -1 (infinite), which may grow unruly
            # readline.set_history_length(1000)
        except FileNotFoundError:
            pass

        atexit.register(readline.write_history_file, histfile)
        return {}

    @app.shell_context_processor
    def shell_setup():
        """Make a request context and set up local variables for the shell"""
        app.logger.debug("shell_setup")

        ctx = app.test_request_context()
        ctx.push()

        def define_locals():
            # variables we define here (+ `app` and `g`) will be available when we start the Flask shell
            from .app import db, sql_execute, get_cursor, User, generate_password_hash, get_safe_redirect_url, oauth
            from flask import render_template, render_template_string, request, make_response, session
            import json, base64

            foo = "bar"

            __scope__ = locals().copy()
            return __scope__  # this dict will become local variables in the shell

        return define_locals()

    ################################
    # Error handling

    # This one intercepts HTTPExceptions.
    # Other exceptions will result in a 500 Internal Server Error, possibly displaying the debugger page
    @app.errorhandler(HTTPException)
    def handle_http_error(e: HTTPException):
        """Intercept exceptions and turn the into JSON if the client has requested a JSON reply"""
        app.logger.error("HTTPException %s %s %s", e.description, dir(e), type(e), exc_info=True)
        if prefers_json():
            response = make_response(
                jsonify(
                    {
                        "status": "error",
                        "error": {
                            "code": e.code,
                            "name": e.name,
                            "description": e.description,
                            "html_description": e.get_description(),
                            "exception": type(e).__name__,
                        },
                    }
                )
            )
            response.status = e.code or 200
            return response
        else:
            return e

    ################################
    # we're at the end of create_app(), need to return the app object
    # logger.debug("init: url map:\n%s", app.url_map)
    return app


###################################################
# Some utility functions


def prefers_json():
    """Returns True if the client requested a JSON response."""
    return request.accept_mimetypes.best_match(["application/json", "text/html"]) == "application/json"

def get_safe_redirect_url():
    """Make sure redirects from the login page are safe"""
    # see discussion at
    # https://stackoverflow.com/questions/60532973/how-do-i-get-a-is-safe-url-function-to-use-with-flask-and-how-does-it-work/61446498#61446498
    next = request.values.get("next")

    if next:
        url = urlparse(next)
        if not url.scheme and not url.netloc:  # ignore attempts to use absolute url
            return url.path  # use only the path
    return None


################################
# For database access

def get_cursor():
    """Use a single database server per request"""
    if "cursor" not in g:
        if db is None:
            raise RuntimeError("database not initilized; call sql_init()")
        g.cursor = db.cursor()
    return g.cursor


def sql_execute(stmt, *args, **kwargs):
    """Execute and log SQL statement"""
    app.logger.debug("SQL: %s %s %s", stmt, args or "", kwargs or "")
    return get_cursor().execute(stmt, *args, **kwargs)

def sql_init():
    """Set up connection to SQLite database. Database file will be created and initialised if needed."""
    global db
    db_file = os.path.join(app.instance_path, "users.db")
    app.logger.info('opening database %s', db_file)
    db = apsw.Connection(db_file)
    if db.pragma("user_version") == 0:
        sql_execute(
            """CREATE TABLE IF NOT EXISTS users (
            id integer PRIMARY KEY, 
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            info JSON NOT NULL);"""
        )
        sql_execute(
            """CREATE TABLE IF NOT EXISTS tokens (
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            token TEXT NOT NULL UNIQUE,
            name TEXT
            );"""
        )
        sql_execute(
            """CREATE TABLE IF NOT EXISTS buddies (
            user1_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            user2_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            PRIMARY KEY (user1_id, user2_id)
            );"""
        )
        alice = User(
            {
                "username": "alice",
                "password": generate_password_hash ("password123"),
                "name" : "Alice",
                "color": "green",
                "picture_url": "https://git.app.uib.no/uploads/-/system/user/avatar/788/avatar.png",
            }
        )
        alice.save()
        alice.add_token("example")

        swarnika = User({
            "username": "Swarnika",
            "password": generate_password_hash("Sw4rn1ka!"),
            "name": "Swarnika",
            "color": "pink",
        })
        swarnika.save()
        swarnika.add_token("example")

        bob = User({"username": "bob", "password": generate_password_hash("bananas"), "name" : "Bob", "color": "red"})
        bob.save()
        bob.add_token("test")
        sql_execute("INSERT INTO buddies (user1_id, user2_id) VALUES (?, ?), (?, ?);",
                    (alice.id, bob.id, bob.id, alice.id))
        # we might need to change the database schema later, so it's a good idea to have a versioin number
        sql_execute("PRAGMA user_version = 1;")
