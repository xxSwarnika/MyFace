/** flashes.ts – © 2025 Anya Helene Bagge

    Shows Flask "flashes" (e.g., info messages like "Logged in" or "Error doing something")
    in a nice on-screen box for a little while before fading them out.
*/
const fade_after = 3000;
const hide_after = 3000;
const hide_time = 1500;
const remove_after = 1000;
const start_time = Date.now();
const set_timer = (() => {
    let timer = -1;
    let next_wake = Infinity;
    function handler() {
        timer = -1;
        prune_flashes();
    }
    function set_timer(wake_time) {
        if (wake_time < next_wake) {
            const now = Date.now();
            if (wake_time < now) {
                prune_flashes();
            }
            else {
                if (timer >= 0)
                    window.clearTimeout(timer);
                timer = window.setTimeout(handler, wake_time - now);
            }
        }
    }
    return set_timer;
})();
function refresh_keep() {
    let keep = false;
    const flashes = document.getElementById('flashes');
    if (!flashes)
        return;
    for (let i = flashes.children.length - 1; i >= 0; i--) {
        const elt = flashes.children.item(i);
        if (elt.dataset.stage == 'keep')
            keep = true;
        else if (keep && elt.dataset.stage == 'hide')
            elt.dataset.stage = 'fade';
        if (keep && elt.classList.contains('keep-height')) {
            set_message_stage(elt, elt.dataset.stage || 'show');
        }
        elt.classList.toggle('keep-height', keep);
    }
}
const stages = {
    new: 'show',
    keep: 'show',
    show: 'fade',
    fade: 'hide',
    hide: 'remove',
    remove: 'removed',
};
function set_message_stage(flash, stage) {
    let timeout = 0;
    if (stage != flash.dataset.stage) {
        switch (stage) {
            case 'removed':
                flash.style.removeProperty('max-height');
                const flash_log = document.querySelector('#flash-log');
                if (flash_log) {
                    flash_log.appendChild(flash);
                }
                else {
                    flash.remove();
                }
                return 0;
            case 'remove':
                flash.dataset.stage = 'remove';
                timeout = remove_after;
                break;
            case 'hide':
                flash.style.setProperty('transition-duration', '0s');
                flash.style.setProperty('max-height', 'fit-content');
                flash.style.setProperty('max-height', getComputedStyle(flash).height);
                getComputedStyle(flash).height; // force restyle
                flash.style.removeProperty('transition-duration');
                flash.dataset.stage = 'hide';
                timeout = hide_time;
                break;
            case 'fade':
                flash.dataset.stage = 'fade';
                timeout = hide_after;
                break;
            case 'keep':
                if (flash.dataset.stage != 'keep')
                    flash.dataset.oldStage = flash.dataset.stage;
                flash.dataset.stage = 'keep';
                timeout = hide_after;
                break;
            case 'show':
            default:
                flash.dataset.stage = 'show';
                if (flash.classList.contains('error'))
                    timeout = fade_after * 2;
                else if (flash.classList.contains('warning'))
                    timeout = fade_after * 1.5;
                else
                    timeout = fade_after;
                break;
        }
    }
    else {
        timeout = parseInt(flash.dataset.timeout || '0');
    }
    console.log('setting', stage, flash);
    flash.dataset.timeout = `${timeout}`;
    flash.dataset.t0 = `${Date.now()}`;
    return timeout;
}
function prune_flashes() {
    let soonest = Infinity;
    const now = Date.now();
    refresh_keep();
    document.querySelectorAll('#flashes .flash').forEach((elt, i) => {
        const flash = elt;
        let t0 = parseInt(flash.dataset.t0 || `${now}`);
        let timeout = parseInt(flash.dataset.timeout || '0');
        if (t0 + timeout <= now && !flash.classList.contains('keep-height')) {
            timeout = set_message_stage(flash, stages[flash.dataset.stage || 'new']);
            flash.dataset.timeout = `${timeout + i * 500}`;
        }
        if (now + timeout > now && now + timeout < soonest)
            soonest = now + timeout;
    });
    if (soonest < Infinity) {
        console.assert(soonest > now, soonest, now);
        //console.log('pruning done, will wake again in', soonest - now, ' ms');
        set_timer(soonest);
    }
}
function pointerenter_handler(ev) {
    if (ev.target) {
        const flash = ev?.target;
        set_message_stage(flash, 'keep');
    }
}
function pointerleave_handler(ev) {
    if (ev.target) {
        const flash = ev?.target;
        if (flash.dataset.stage === 'keep') {
            set_message_stage(flash, flash.dataset.oldStage || 'show');
        }
        prune_flashes();
    }
}
function close_flash(flash) {
    flash.dataset.timeout = `${hide_time}`;
    flash.dataset.t0 = `${Date.now()}`;
    set_message_stage(flash, 'hide');
    prune_flashes();
}
const flash_added = (flash, i, parent) => {
    flash.addEventListener('pointerenter', pointerenter_handler);
    flash.addEventListener('pointerleave', pointerleave_handler);
    set_message_stage(flash, 'show');
    prune_flashes();
};
export function activate_flashes() {
    document.querySelectorAll('.flash').forEach((e, i, p) => flash_added(e, i, p));
}
let i = 0;
/** Show a new flash on the screen
 * @param content The message to be flashed
 * @param category the category for the message. The following values are recommended: 'message' for any kind of message, 'error' for errors, 'info' for information messages and 'warning' for warnings. However any kind of string can be used as category.
 */
export function show_flash(content /*|Hole*/, category = 'message') {
    const flashes = document.querySelector('#flashes');
    if (!flashes)
        return;
    let s = content;
    console.log('show_flash', content);
    if (typeof content !== 'string' && !(content instanceof Node)) {
        // && !(content instanceof Hole)) {
        s = content.message;
        if (Array.isArray(content.args) && content.args.length > 0) {
            s = `${s}: ${content.args.map((a) => `${a}`).join(', ')}`;
        }
    }
    const elt = document.createElement('li');
    elt.classList.add('flash');
    const inner = document.createElement('div');
    inner.classList.add('flash-inner');
    if (content instanceof HTMLBodyElement) {
        while (content.firstChild != null)
            inner.appendChild(content.firstChild);
    }
    else if (content instanceof HTMLElement) {
        inner.appendChild(content);
    }
    else {
        inner.innerText = `${s}`;
    }
    elt.appendChild(inner);
    elt.classList.add(category);
    const button = document.createElement('button');
    button.type = 'button';
    button.addEventListener('click', () => close_flash(elt));
    button.ariaLabel = 'Close';
    button.ariaDescription = 'Close this message';
    button.innerText = '🗙';
    inner.appendChild(button);
    flashes.appendChild(elt);
    flash_added(elt, i++);
    return inner;
}
globalThis.flashes = {
    activate_flashes,
    show_flash,
};
if (document.readyState === 'loading') {
    // Loading hasn't finished yet
    document.addEventListener('DOMContentLoaded', activate_flashes);
}
else {
    // `DOMContentLoaded` has already fired
    activate_flashes();
}
