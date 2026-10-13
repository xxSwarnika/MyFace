import { render, html } from './_uhtml.js';
import { show_flash } from './_flashes.js';


function isSafeUrl(url) {
    try {
        const u = new URL (url, window.location.origin);
        return u.protocol === 'http:' || u.protocol === 'https:';
    } catch {
        return false;
    }
}

const SAFE_HEX_COLOR = /^#(?:[0-9a-f]{3}){1,2}$/i;
function safeColor(c) {
    return typeof c === 'string' && SAFE_HEX_COLOR.test(c) ? c : '#000';
}

async function getBuddyStatus(userId) {
    return await fetch_json(`/buddies/${Number(userId)}/status`);
}

/**
 * Format a key-value field
 *
 * TODO: check security!
 *
 * @param {*} key The key
 * @param {*} value The value
 * @param {*} options Object with options {optional: bool, className: string, long: bool}
 * @returns HTML text
 */
export function format_field(key, value, options = {}) {
    if (value === undefined || (options.optional && !value)) return '';
    let classNames = 'field';
    if (options.className)
        // if we need extra styling
        classNames += ` ${options.className}`;
    if (options.long)
        // if the value is a longer text
        classNames += ' long';
    const valueNode = options.long 
    ? html `<div class="value">${value || ''}</div>` 
    : html `<span class="value">${value || ''}</span>`;
    return html `<li class=${classNames}>
    <span class="key">${key}</span>${valueNode}
    </li>`;
}

/**
 * Display a user as a HTML element
 *
 * TODO: check security!
 *
 * @param {*} user A user object
 * @param {*} elt An optional element to render the user into
 * @returns elt or a new element
 */
export function format_profile(user, elt) {
    if (!elt) elt = document.createElement('div');
    elt.classList.add('user'); // set CSS class
    if (user.id == current_user_id) elt.classList.add('me');
    elt.dataset.userId = user.id;
    
    let colorValue = undefined;
    if (user.color !== undefined){
        const c = safeColor(user.color);
        colorValue = html`
        <span>${c}</span>
        <div class ="color-sample" style =${`background: ${c}`}></div>
        `;
    }

    const imgSrc =
        user.picture_url && isSafeUrl(user.picture_url)
        ? user.picture_url
        : './static/unknown.png';
    
    render(
        elt,
         html`
            <img src=${imgSrc} alt =${user.username + "'s profile picture"} referrerpolicy="no-referrer" />
             <ul class="data">
                ${format_field('Username', user.username, { className: 'username' })}
                ${format_field('Name', user.name, { className: 'more' })}
                ${format_field('Birth date', user.birthdate, { className: 'more' })}
                ${format_field('Favourite colour', colorValue, { className: 'more' })}
                ${format_field('About', user.about, { long: true, className: 'more' })}
            </ul>

            <div class="controls">
                ${window.current_user_id == user.id
                ? ''
                : html`<button type="button" data-user-id=${user.id} data-action="add_buddy">Add buddy</button>`}
            </div>
        `
    );
    // note: fields that are undefined are ignored
    // note: the fields marked `classname: 'more'` will be hidden (using CSS) until the user clicks on the element and opens the profile

    return elt;
}

async function updateBuddyControls(container, targetUserId){
    const controls = container.querySelector('.controls');
    if (!controls) return;

    const status = await getBuddyStatus(targetUserId);
    if (!status) return;

    const showAddButton = !status.i_granted; // I haven't added them yet
    const badge = status.mutual
        ? html`<span class="badge" title="You are mutual buddies">🥳 mutual</span>`
        : status.one_way_from_user
        ? html`<span class="badge" title="They added you">🤗 granted by user</span>`
        : '';

    const button = showAddButton
        ? html`<button type="button" data-user-id=${targetUserId} data-action="add_buddy">
                Add buddy
            </button>`
        : '';

    render(controls, html`${badge} ${button}`);
}

/**
 * Perform an action, such as a button click.
 *
 * Get the action to perform and any arguments from the 'data-*' attributes on the button element.
 *
 * @param {*} element A button element with `data-action="…"` set
 * @returns true if action was performed
 */
export async function do_action(element) {
    if (element.dataset.action === 'add_buddy') {
        element.disabled = true;
    try {
        const result = await fetch_json(`/buddies/${Number(element.dataset.userId)}`, 'POST');
        if (result) {
            const card = element.closest('.user');
            if (card && card.dataset.userId) {
                await updateBuddyControls(card, Number(card.dataset.userId));
            }
            show_flash('Buddy added wii');
          }
        } finally {
        element.disabled = false;
        }   
        return true;
    }
    return false;
}

//////////////////////////////////////////////////////////////////////////////////////////////
//
// Examples
//
//////////////////////////////////////////////////////////////////////////////////////////////

/** demo of uhtml templates */
export function uhtml_demo() {
    const main = document.querySelector('main');
    /** render demo examples on page */
    function show_demo(name, template) {
        console.log(name, template);
        const elt = document.createElement('div');
        main.appendChild(elt);
        render(
            elt,
            html`<h3>${name}</h3>
                ${template}`
        );
        return elt;
    }

    // uhtml example 1
    const unsafe_data = '<script>alert()</script>';
    // safely inserted as a string
    const simple_tmpl = html`<em>${unsafe_data}</em>`;
    show_demo('Unsafe data (simple_tmpl)', simple_tmpl);

    // uhtml example 2
    const username = 'foo',
        nested = 'nested';
    const user = html`<em>${username}</em>`;
    // nested templates are inserted as HTML elements
    const message_tmpl = html`<div>Hello, my name is ${user}, and your name is ${html`<b>${nested}</b>`}</div>`;
    show_demo('Nested templates (message_tmpl)', message_tmpl);

    // uhtml example 3
    const users = ['alice', 'bob'];
    // you can also use lists
    const users_tmpl = html`<ul>
        ${users.map((user) => html`<li>${user}</li>`)}
    </ul>`;
    const users_elt = show_demo('Template with list (users_tmpl)', users_tmpl);
    users_elt.addEventListener('click', () => {
        users.push('eve');
        render(
            users_elt,
            html`<ul>
                ${users.map((user) => html`<li>${user}</li>`)}
            </ul>`
        );
    });

    // uhtml example 4
    const color = 'red';
    // attributes require special care
    const attr_tmpl = html`<div class="color-sample" style="${'background:' + color}"></div>`;
    show_demo('Template with attributes (attr_tmpl)', attr_tmpl);

    // uhtml example 5
    // this won't work
    const attr_tmpl_err = html`<div class="color-sample" style="background: ${color}"></div>`;
    try {
        show_demo("This shouldn't work (attr_tmpl_err)", attr_tmpl_err);
    } catch (e) {
        console.error(e);
    }
}

window.uhtml_demo = uhtml_demo;

// example of how to create elements manually
export function createElement_demo() {
    const main = document.querySelector('main');

    function element(tag, { cssClass, child } = {}) {
        const elt = document.createElement(tag);
        if (cssClass) elt.className = cssClass;
        if (typeof child === 'string' || typeof child === 'number') elt.innerText = `${child}`;
        else if (child) elt.appendChild(child);
        return elt;
    }

    const fields = [
        { key: 'Name', value: 'alice' },
        { key: 'Favourite color', value: 'pink' },
    ];
    const outerDiv = element('ul', { cssClass: 'data' });
    fields.forEach((field) => {
        const item = element('li', { cssClass: 'field' });
        item.appendChild(element('span', { cssClass: 'key', child: field.key }));
        item.appendChild(element('span', { cssClass: 'value', child: field.value }));
        outerDiv.appendChild(item);
    });
    main.appendChild(element('h3', { child: 'createElement demo' }));
    main.appendChild(outerDiv);
}
window.createElement_demo = createElement_demo;

//////////////////////////////////////////////////////////////////////////////////////////////
//
// Utility functions – you don't need to check these for vulnerabilities!
//
//////////////////////////////////////////////////////////////////////////////////////////////

/**
 * Wrapper around fetch() for JSON data
 *
 * @param {*} path The path (or URL)
 * @param {*} method Request method, defaults to GET
 * @param {*} headers Additional headers
 * @returns The response data, as an object, or null if the request failed
 */
export async function fetch_json(path, method = 'GET', headers = {}) {
    try{
        const resp = await fetch(path, {
            method,
            credentials: 'same-origin',
            headers: {
                accept: 'application/json',
                ...headers,
            },
        });

        const ct = resp.headers.get('content-type') || '';
        if (resp.ok) {
            return ct.startsWith('application/json') ? await resp.json() : {} ;
        }

        if (ct.startsWith('application/json')) {
        const result = await resp.json();
        const err = result.error;
        if (err) {
            const flash_inner = show_flash(`${err.code} ${err.name}`, 'error');
            if (err.exception === 'CSRFError') {
                const link = document.createElement('a');
                link.innerText = `${err.exception}: ${err.description}`;
                link.href =
                    'https://git.app.uib.no/inf226/25h/inf226-25h/-/wikis/lectures/Cross-site,-same-site,-origins-and-cookies#csrf-token';
                link.target = '_blank';
                flash_inner.appendChild(document.createElement('br'));
                flash_inner.appendChild(link);
                }
            }
        } else {
            show_flash(`${resp.status} ${resp.statusText}`);
        }
    } catch (e) {
        console.error('Network error:', e);
        show_flash('Network error', 'error');
    }
    return null;
}

/**
 * Get list of users from server
 *
 * @returns A list of simple user objects (only id and username)
 */
export async function list_users() {
    return (await fetch_json('/users/')) || [];
}

/**
 * Get a user profile from the server
 * @param {*} userId The numeric user id
 * @returns A user object
 */
export async function get_profile(userId) {
    const defaults = { 
        name: '?', 
        birthdate: '?',
        color: 'none', 
        picture_url: './static/unknown.png',
        about: '',
    };
    const user = await fetch_json(`/users/${Number(userId)}`);
    // by setting fields to default values, we can tell the difference between a loaded profile and
    // the minimal one we get from list_users(), where everything except id and username is undefined.
    return { ...defaults, ...user };
}
