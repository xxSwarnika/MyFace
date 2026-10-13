# INF226 Portfolio Assignment 2 (Fall 2025)

[*Read the Wiki to make sure you have the most updated version.*](https://git.app.uib.no/inf226/25h/inf226-25h/-/wikis/portfolio-2/myface)

## Practical information

* **Deadline**
  * **Friday, November 7th, 2025 at 23:59**
  * For [Task *z* (improvements)](#improvements), the deadline is **Friday, December 12th, 2025 at 23:59**.

* This assignment **counts towards your grade (20%)**, togehter with the previous assignment (10%) and the exam (70%).
* See general UiB guidelines on [cheating and its consequences](https://www.uib.no/en/quality-in-studies/77940/cheating-and-its-consequences) and [using sources](https://www.uib.no/en/education/49058/use-sources-written-work). We might ask you to explain your work to verify that you've done it yourself.
* For more details on collaboration, AI use, deadline extension etc, see [Boilerplate](#boilerplate) below.
* **The goal is to finish a prototype web application and reflect on its security.**

### Questions?

**[See the FAQ](./faq)**

### Objectives

Afterwards, you should be able to explain…

* what the main threats against web services are,
* and how to mitigate them;

and you should be able to…

* work with sessions and cookies,
* use libraries for authentication,
* do simple security analysis of an application

and be familiar with…

* [same-origin policy](https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy)
* [cross-origin resource sharing (CORS)](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS).
* [content security policy (CSP)](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)

### Deliverables

A Git repository will be set up for you at [git.app.uib.no](https://git.app.uib.no/inf226/25h/proj). Deliver your work by committing and pushing before the deadline:

* a `REPORT.md` file with 
   * a brief overview of what you've done,
   * answers to questions,
   * instructions on how to test/demo it,
   * any other necessary technical details on the implementation (e.g. if any configuration is needed),

* the source code of your project

If you write (parts of) the report in something other than Markdown, add the PDF to the project, and make a clearly marked link to it in `REPORT.md`. **Any code or documents not included in *your own project repository* will not be assessed.**

**Important:** for each part of the assignment, please *commit **and push** your work* before proceeding to the next part, so we can see all the steps you took towards the final result. Commit as often as possible/practical, this makes it easier to see that the work is your own and not copied / LLM generated. Pushing makes it easier for us to see that you're on the right track and might also give you useful feedback from automated tests.


## Overview
### MyFace

After years of never-ending [*ostehøvel*](https://en.wikipedia.org/wiki/Cheese_knife) cuts, University budgets are getting strained. In order to secure more funding for new courses and activities, the Department of Informatics has decided to build a new web app aimed at the lucrative social media market. The app will be called *MyFace*, following in the tradition of similar older sites (the original plan was to go with just *Å*, but apparently Elon Musk has already picked up the domain name for his new orbital ride share service).

Unfortunately, the prototype has been hacked a few times already and the code is bit of a mess (asking Anya to develop it in her spare time was a bad idea, and now she's away on vacation or something). You've been asked to clean up the code and bring it in line with web security best practices.

### The source code
You can [browse the source code here](https://git.app.uib.no/inf226/25h/myface), but **make sure you do any development against your own repository**.

* `myface/` – contains Python code
  * `app.py` – the main server application. Contains initialization code, and routes that map request paths to Python functions. Launch with `flask -A myface run --debug`.
  * `*_form.py`– declarations for forms. You probably don't need to touch these.
  * `util.py` – extra stuff that you don't need to touch.
  * `static/` – contains files that are served directly, including some images and:
    * `script.js` – JavaScript code used to render the main page; also includes some examples.
    * `style.css` – CSS style declarations, generated from `style.scss` – you don't need to understand it or change it
    * You can ignore these files:
    * `_uhtml.js` - the µhtml library (no need to look at this code, it's unreadable anyway)
    * `_flashes.js` – small library for displaying messages on screen
  * `templates/` – the templates will be rendered/expanded by the server to produce HTML responses.
     * `home.html` – the main page (i.e., `index.html`); it uses JavaScript to show a clickable list of all the users in the system
     * `login.html` – the login form
     * `profile.html` – form for editing the user's profile
     * `field.html` – used by other templates to render form fields
     * You can mostly ignore the templates with names beginning with `_` (i.e., you can assume there are no vulnerabilities):
     * `_generic_info.html` – used to render some boilerplate pages
     * `_layout.html` – overall page layout for the other templates
     * `_users.html` – optionally used to render some data as HTML instead of JSON
     * `_secrets.tmpl` – used to generate a config file for secrets, so you won't be tempted to add them to Git
* `instance/` – this folder will be created the first time you run the project, and will contain the database, a log file, and configuration files (if any)
* `REPORT.md` – write your answers and security analysis here 

<details><summary>Modifying CSS</summary>

You don't need to read or change the CSS code, but if you want to do it anyway, you may want to do it properly by editing the original code: The CSS code in `style.css` is generated from `style.scss` using [Sass](https://sass-lang.com/), which is an extension of CSS with some very useful features. Setting up the infrastructure for this is beyond the scope of this assignment, but if you have the [`npx` command](https://docs.npmjs.com/cli/v9/commands/npx?v=true) available, you can run Sass from the command line with `npx sass myface/static/`. With the `--watch` option (`npx sass --watch myface/static/`), it will keep running and automatically regenerate `style.css` whenever `style.scss` changes.

</details>

### Thing to note in the code

* `@app.route("/path", methods=[…])`, `@app.get(…)`, `@app.post(…)` – these set up [URL routes](https://flask.palletsprojects.com/en/3.0.x/quickstart/#routing). Be mindful of [HTTP method semantics](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods) – for instance, `GET` and `POST` should usually not be handled the same way.
* [`@login_required`](https://flask-login.readthedocs.io/en/latest/#flask_login.login_required) – routes with this annotation check for a logged in user, and redirect to the login page if necessary. The user that sent the request can be found in the `current_user` variable.
* [`request`](https://flask.palletsprojects.com/en/3.0.x/quickstart/#accessing-request-data), [`session`](https://flask.palletsprojects.com/en/3.0.x/quickstart/#sessions), [`g`](https://flask.palletsprojects.com/en/3.0.x/api/#flask.g), [`current_user`](https://flask-login.readthedocs.io/en/latest/#flask_login.current_user), etc – for convenience, Flask makes data about the current request (the [request context](https://flask.palletsprojects.com/en/3.0.x/reqcontext/)) available in these global variables
* [`f"Hello, {expr}!"`](https://docs.python.org/3/reference/lexical_analysis.html#formatted-string-literals) (Python) or [<code>\`Hello, ${expr}\`</code>](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Template_literals) (JavaScript) – [string interpolation](https://en.wikipedia.org/wiki/String_interpolation). Remember that string interpolation and string concatenation can lead to [code injection](https://en.wikipedia.org/wiki/Code_injection) issues (SQL injection, cross-site scripting)!
* The templates (in `myface/templates/`) are rendered using the [Jinja2](https://flask.palletsprojects.com/en/3.0.x/templating/) template engine, which uses Python-like statements `{% … %}` and expressions `{{ … }}` to produce the final result. Additional variables can be passed to the templates as keyword arguments to `render_template()`

# Tasks
## **a)** SQL Injection [4 pts]

You think the code might be vulnerable to [SQL injection attacks](https://owasp.org/www-community/attacks/SQL_Injection).

* **Find a way to do an SQL injection attack against the app** (e.g., create a fake user from the login form)
* **Describe briefly how you did it**
* **Fix the code in `app.py` so that it's no longer vulnerable to SQL injections**

### SQL Injection Resources
* [APSW Library documentation (Executing SQL)](https://rogerbinns.github.io/apsw/example.html#executing-sql)
* [SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)

***Commit and push before moving on to the next task.***

## **b)** Code Injection [4 pts]

You also suspect that the code might be vulnerable to [Cross-Site Scripting (XSS) / code injection](https://en.wikipedia.org/wiki/Code_injection).
* **Find a way to inject JavaScript code into the home page**, for example by editing the *About* field in your profile. The code should run when you view or click on a user on the home page.
* **Describe briefly how you did it**
* Could we solve (some of) the injection problems with a restrictive [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy)? **Explain.**
  
The list of users on the home page is constructed dynamically by JavaScript code in `home.html` and `script.js`. The user information is queried from the server with calls to `/users/` (for the full list) and `/users/<user_id>` (for profile details). The scripts receives JSON data which it then renders as HTML. But, the server also supports sending this data as HTML (rendered with the template `_users.html`; the choice is made depending on the `Accept` header in the request.
* Try visiting `/users/me` in the browser. Does your code injection still work? **Explain.**

The Jinja2 templating system used by Flask seems to protect against code injection. We still need to protect the HTML code we generate from JavaScript, however. A few ideas come to mind:
* We could generate *all* HTML code using server-side templates – but that would be boring and not very dynamic, so let's not do that.
* We could make sure that all the data values served only contain [“safe”](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html#html-sanitization) HTML, or that all special characters are escaped (e.g., with [`html.escape`](https://docs.python.org/3/library/html.html#html.escape) in Python. That might be difficult, though, since HTML element, HTML attributes, URLs, CSS and JavaScript code all have different conventions, and we might not know exactly how a piece of data will be used.
* A safe solution is to rewrite the JavaScript code to avoid using [`innerHTML`](https://developer.mozilla.org/en-US/docs/Web/API/Element/innerHTML) – text content should be inserted using [`element.innerText = …`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/innerText) (or by creating text nodes), attributes should be set using [`element.setAttribute(…)`](https://developer.mozilla.org/en-US/docs/Web/API/Element/setAttribute) (or `element.attributeName = …` if available), styles can be set using [`element.style.propertyName = …`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/style), and so on. This can be a bit cumbersome, though, since each HTML element must be created manually (e.g., with [`document.createElement('TAG')`](https://developer.mozilla.org/en-US/docs/Web/API/Document/createElement)).
* A safe and easier solution is to use templates on the client side. The templating engine will build HTML elements from tags and make sure that any data inserted into the template will not be misinterpreted. There are many such systems, but our `script.js` has been set up to use a very minimal (yet convenient) template system called [µhtml](https://github.com/WebReflection/uhtml/blob/main/DOCUMENTATION.md).
* **Fix the code injection problems you find in `script.js`.** You can either build elements manually or use µhtml – see the [Hints](#hints) section and `myface/static/script.js` for a quick intro to both.

To see that the injected code is actually running, use something like `alert('u got hacked')` or `console.warn('u got hacked')` (no need to steal credit card info or anything like that!).

### Injection Resources
* Try out some basic ways to inject code with [Google's XSS Game](https://xss-game.appspot.com/) – the trick from Level 2 should probably work
* [Cross Site Scripting Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html) (in particular, the app relies on `innerHTML` and string interpolation/concatenation).
* [What is cross-site scripting and how can you fix it?](https://www.acunetix.com/websitesecurity/cross-site-scripting/)

***Commit and push before moving on to the next task.***

## **c)** Access Control [4 pts]

There are several other problems with the project:

* The code dealing with passwords is a bit suspicious. How are passwords stored? Can a user have an empty password? The user can change passwords on the profile page, but are there any checks to see if the new password is strong enough? Is this in line with security best practices? **Explain.**
* **Implement safer password storage.** (Minimum hash with salt.)
* **Implement some form of checking of new passwords.**

There should probably be some form of access control, otherwise all users can see the full profile of all other users. The *buddy* relationship might be used for this (see the `relations` and `relation_kinds` tables in the database). For example, if Alice has added Bob as a buddy, then Bob should be able to see Alice's full profile, otherwise we just show the username.
* **Implement some form of simple access control scheme.** Make sure that users can't bypass it by accessing the `/users/` API directly.
* **If you wish, implement adding/removing buddies and checking buddy status.** It probably makes sense to think of it as a one-way relation: Alice adding Bob as a buddy is kind of like sending a friend request, and gives Bob access; if Bob then adds Alice, they're proper buddies (marked by some symbol in the user interface, for example). There are [some hints in the FAQ](https://git.app.uib.no/inf226/25h/inf226-25h/-/wikis/portfolio-2/faq#making-the-add-buddy-button-only-show-up-if-you-arent-already-buddies)
* Is it possible for a user to *change* another user's profile information? **Check this, and explain why/why not.**
* Remember to explain your choices and what you have done.

### Password and access control resources

* Flask's underlying framework [Werkzeug](https://werkzeug.palletsprojects.com/en/stable/) has a convenient module for password hashing: [`werkzeug.security`](https://werkzeug.palletsprojects.com/en/3.0.x/utils/#module-werkzeug.security)
* Simple password strength checking can be done using regular expressions. See [StackOverflow discussion](https://stackoverflow.com/questions/16709638/checking-the-strength-of-a-password-how-to-check-conditions#32542964) for more suggestions. There's also a library available: [password-strength](https://pypi.org/project/password-strength/)
* You probably have to tweak the database a bit (change passwords for the pre-created users, for example) – a simple way of doing this is by modifying `sql_init()` and then just deleting `users.db` so it gets recreated when you start the server.
* In the FAQ, you can read more about [CSRF protection](https://git.app.uib.no/inf226/25h/inf226-25h/-/wikis/portfolio-2/faq#csrf-tokens) for Flask, and how to do [Bearer authentication](https://git.app.uib.no/inf226/25h/inf226-25h/-/wikis/portfolio-2/faq#how-to-do-bearer-token-authentication).

***Commit and push before moving on to the next task.***

## **d)** Analysis and code review [5 pts]

*For this task, it's best to collaborate with other students and review each others' projects, but you could also work on your own project.*

* **Go through** the whole application (both Python, JavaScript, SQL and HTML code), and **make a note** of possible vulnerabilities, things your are uncertain about or that seem to not follow best practices. Fix any small problems you can deal with in a reasonable amount of time.
* **Write a short report** documenting the threat model, which potential vulnerabilities you've considered, which vulnerabilities you've closed/mitigated and so on.
* You can extend the application with more features if you like.

### Particular things to consider

* Can another developer understand the overall design, based on the documentation and available source code?
* Do you see any potential improvements that could be made in design / coding style / best practices? I.e., to make the source code clearer and make it easier to spot bugs.
* What is the [threat model](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html) – who might attack the application? What can an attacker do? What damage could be done (in terms of *confidentiality*, *integrity*, *availability*)? Are there limits to what an attacker can do? Are there limits to what we can sensibly protect against?
* Is the session cookie options set appropriately?
* Is the SECRET_KEY set to secure random value?
* Are secrets stored separately, not checked in to Git? (`app.config.from_pyfile` is an easy way to load secrets and configuration data from a separate file)
* Could the application benefit from setting `Content-Security-Policy` or other HTTP headers? (There's an `after_request()` hook where you can add headers to any response.)
* Do you see any security risks that you *haven't* considered yet? (Have a look at the [OWASP Top Ten list](https://owasp.org/www-project-top-ten/) and  “Unit 2: Attack Vectors” in *Security for Software Engineers*)
* How can you know that you security is good enough? ([*traceability*](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)) 
* Is the application vulnerable to
  * [Cross-site scripting attacks](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)?
  * [Cross-site request forgery](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)?
  * [SQL injection](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)?
  * [Insecure design](https://owasp.org/Top10/A04_2021-Insecure_Design/)?

### Useful Resources
* *Security for Software Engineers* (textbook, available online through UiB's network) – Ch. 5–9 on code hardening, ch. 10 & 11 on authentication and access control
* *Secure by Design* (textbook)
* *[OWASP Web Service Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Web_Service_Security_Cheat_Sheet.html)*
* [OWASP Attack Surface Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Attack_Surface_Analysis_Cheat_Sheet.html)
* [Security Considerations (Flask Documentation)](https://flask.palletsprojects.com/en/3.0.x/security/)
* [Best Practices for Flask Security](https://www.securecoding.com/blog/flask-security-best-practices/)
* [Best Practices for Flask API Development](https://auth0.com/blog/best-practices-for-flask-api-development/)
* You may find it useful to try [some security testing tools](https://hackr.io/blog/top-10-open-source-security-testing-tools-for-web-applications). Also, consider the code injection techniques from the [XSS attack game](https://xss-game.appspot.com/). Is it possible to do damage by tricking a logged-in user into click on a link or form submission?

***Commit and push before moving on to the next task.***

## **e)** OpenId Connect [3 pts]

***Do this last, if you have time.***

The managers also want MyFace to support [OpenID Connect (OIDC)](https://openid.net/developers/how-connect-works/) for integration with [Feide](https://www.feide.no/), [BankID](https://developer.bankid.no/bankid-oidc-provider/getting-started/) and more. For now, the goal is to make it work with [git.app.uib.no](https://git.app.uib.no/) which also [works as an OAuth 2.0 and OIDC provider](https://git.app.uib.no/help/api/oauth2.md).

* **Set up OIDC login using [authlib](https://docs.authlib.org/en/latest/client/flask.html).**

### Implementing OIDC
* First of all, you need to configure a new application on your [GitLab profile page](https://git.app.uib.no/-/profile/applications). Give it a name, and select the `openid` and `profile` scopes (maybe `email` as well). For *Redirect URI*, you need the URI of the callback route you'll set up on your own server. Assuming you're running your server locally, and you picked `/login/callback` for the callback route, the URI would be `http://localhost:5000/login/callback`. You can have multiple redirect URIs, so you deploy application, you might add `https://example.com/login/callback`. Make a note of the *client id* and *client secret*, which you'll need in the next step.
* In the server app, you need to create an `OAuth` object and [register an OIDC client](https://docs.authlib.org/en/latest/client/flask.html#flask-openid-connect-client). If register it with the name `'gitlab'`, you can access it as `oauth.gitlab` and it'll automatically look for the client id and secret in the `GITLAB_CLIENT_ID` and `GITLAB_CLIENT_SECRET` config variables. For the `server_metadata_url`, you can use [https://git.app.uib.no/.well-known/openid-configuration](https://git.app.uib.no/.well-known/openid-configuration), then the rest of the configuration will be automatic. For the scope, `'openid profile'` is probably sufficient; you might add `email`.
* As explained in the lectures, there are four steps to a successful OIDC login:
   1. The user visits our *Log in with git.app.uib.no* page (e.g., `/login/gitlab`). We redirect the user to the authorization endpoint at git.app.uib.no. The `authorize_redirect(external_url_of_our_callback_route)` function can help us with this (the callback URL must match one of the *Redirect URI* entries you set up on GitLab).
   2. The GitLab server may ask the user to grant us access to their information, if they haven't already given permission. If successful, GitLab will the redirect the user back to our chosen callback URL (e.g., `/login/callback?code=…`)
   3. On our server, the callback will receive an authorization code, which we use (together with our client ID and secret) to obtain an access token and an id token from the GitLab server. The access token can be used to make requests to GitLab on behalf of the user (useful if we asked permission to do API calls (scope `api` or `read_api`)), and the id token is a JSON Web Token (JWT), containing information about the user, such as name, username, email, etc. We use this information to log the user in, or even add a new user (if we didn't recognize the username). The `authorize_access_token()` function takes care of this, the resulting token will then have the user's info in the `token['userinfo']` field.
   4. Finally, we redirect the user to the home page (or whatever page they originally requested).
* Relevant fields in the `userinfo` (from a GitLab server, with scope `openid profile`):
   * `sub` – the GitLab user id (a number)
   * `preferred_username` – the GitLab user name
   * `picture` – profile picture URL
   * `name` – user's full name
   * [See the full list here](https://docs.gitlab.com/ee/integration/openid_connect_provider.html) (favourite color not included, unfortunately)


### OIDC Resources
* OAuth 2.0 is actually meant to be used to authorize an application to talk to another application on the user's behalf. OpenID Connect (ab)uses this for authentication purposes, based on the assumption that only user *A* will be able to authorize us to look at user *A*'s userinfo.
* [How OpenID Connect Works](https://openid.net/developers/how-connect-works/)

***Remember to commit and push!***

## Improvements
### **z**) [up to +5 pts bonus]

* You can fix any deficiencies, bugs, missing features, silly mistakes you noticed five seconds after the deadline, etc. Just make very clear in the `REPORT.md` what improvements you have made, so the TAs don't have to guess.
* You can gain up to 5 pts from this, but no more than **30 pts** total from the portfolio assignments.
* The deadline for this task is ***December 12th, 2025*** (one week after the exam)

# Hints
## Constructing HTML with `createElement()`
Doing this with *only* `createElement()` is extremely cumbersome, so it helps to create a little help function, for example:

```javascript
    function element(tag, {cssClass, child}={}) {
        const elt = document.createElement(tag);
        if(cssClass)
            elt.className = cssClass;
        if (typeof child === 'string' || typeof child === 'number')
            elt.innerText = `${child}`;
        else if (child)
            elt.appendChild(text);
        return elt;
    }
```

Then, to create this HTML code:

```html
<div class="data">
  <li class="field"><span class="key">Name</span> <span class="value">alice</span></li>
</div>
```

You'd do something like:

```javascript
    const outerDiv = element('div', {cssClass:'data'});
    fields.forEach(field => {
        const item = element('li', {cssClass:'field'});
        item.appendChild(element('span', {cssClass:'key', child:field.key}))
        item.appendChild(element('span', {cssClass:'value', child:field.value}))
        outerDiv.appendChild(item)
    })
```

Run `createElement_demo()` (source code in `script.js`) in the console on the app home page to see the above example.

## Construction HTML with `µhtml` templates
`µhtml` extends the built-in string templating facility in JavaScript to deal with HTML code. Instead of:

```javascript
const unsafe_data = '<script>alert()</script>';
elt.innerHTML = `<em>${unsafe_data}</em>` // builds a string that gets parsed as HTML
```

you do:

```javascript
const unsafe_data = '<script>alert()</script>';
render(elt, html`<em>${unsafe_data}</em>`) // builds a HTML tree, and inserts text into it
```

The result will look like “*&lt;script&gt;alert()&lt;/script&gt;*”.

With <code>html\`…\`</code>, the HTML code is parsed *first*, and then any interpolated `${…}` expressions are computed and inserted into the tree. String values are inserted as text, but you can also nest templates to build a larger document fragment:

```javascript
const username = 'Foo', nested = 'Nested'
user = html`<em>${username}</em>`
message = html`<div>Hello, my name is ${user}, and your name is ${html`<b>${nested}</b>`}</div>`
```
(The result of rendering `message` will look like “Hello, my name is *Foo*, and your name is **Nested**”)

A list of html-templates will result in a list of elements:

```javascript
const users = ['alice', 'bob']
render(elt, html`<ul>${users.map(user => html`<li>${user}</li>`)}</ul>`)
```

The result will be a list of items:

* alice
* bob

`µhtml` will also deal correctly with `${…}`-interpolation in attributes, as long as the value is either `${…}` or text, not a mix of both. For example, <code>html\`&lt;div style="background: ${color}"&gt;&lt;/div&gt;\`</code> will result in an error (check the console!), but <code>html\`&lt;div style="${'background:' + color}"&gt;&lt;/div&gt;\`</code> is ok.

Run `uhtml_demo()` (source code in `script.js`) in the console on the app home page to see the above examples.

# Boilerplate
### Plagiarism / Cheating / Collaboration

* The report should be fully written by you. Any code / text / quotes taken from anywhere else (including your own previous work) must be clearly marked with the source (for example, using BibTeX references or footnotes, and literal quotes shown with different formatting).
* Any tool/library you use (apart from those already in `requirements.txt`) must be mentioned, and if you follow any online guide/tutorial or similarly, you should refer to it in the report.
* You can collaborate on the implementation work (max 3 people per project, make it *very clear* who is responsible for what code), and you may discuss / sit together with / try and figure things out together with other students, but the written report must be *your own work*. Even if you collaborate, all the code should be committed and pushed to your own repository.
* When/if helping each other or asking an AI/LLM, please try to not ask for / give *solutions*, but rather explanations of how things work, or other hint. Explaining how [you think] your [non-functioning] code works can be useful for both you and the [your collaborator](https://rubberduckdebugging.com/).
* As with human collaborators, make it clear if you've “collaborated” with ChatGPT or another AI/LLM tool, including what you've asked for help with and how you used the answer. For an extra +2 bonus points (up to max 30 for the portfolio), add a file `AI_LOG.txt` to the project with the full text of your conversation.
* If possible, try to [ask for help on Discord](https://discord.gg/anubxwQqMf) – there are probably others who wonder about the exact same thing, but are too shy to ask!
* But: *don't* post screenshots/listings with your (almost) complete solution, etc. There are still lots of useful things to ask/answer regarding library function, how does return-oriented-programing work, etc.

### Deadline extensions, etc

*If you got an extension on the previous assignment, you were asked to “deliver a draft of that exercise 64 hours [or however long the extension was] before that deadline, so we know you're on the right track next time!” – committing and pushing your project as you work through the tasks is sufficient to satisfy this requirement.*

If you for some reason see that you can't deliver on time, you can get a deadline extension. You don't have to explain *why* – we trust that you have a sensible reason (and certainly understand if you don't! ;) ). *It's better to spend a bit of extra time and get it right, than to take shortcuts and learn nothing.*

* You can get an (up to) 64 hour extension if you need it. Just inform a TA or Anya.

* If you *really* need a longer extension, please include a summary of whatever you have so far (even if it's nothing) and a brief plan for how you intend to complete the exercise in the remaining time. Unless we have arranged otherwise due to special circumstances, any work done more than 64 hours after the deadline won't be counted. (You don't need to wait for a reply – as long as you asked before the deadline, you can assume that the new deadline will be what you asked for or at least a sensible amount of time after you get a reply.)

* If you've solved the assignment and just think you could do a bit better with a bit more time – don't bother, you probably have more useful stuff to do, and small fixes won't make any practical difference. *Perfection is overrated!*
