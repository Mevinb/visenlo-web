'use strict';

const toggle = document.querySelector('.menu-toggle');
const navigation = document.querySelector('#site-nav');
function setMenu(open) {
  toggle.setAttribute('aria-expanded', String(open));
  navigation.classList.toggle('is-open', open);
  toggle.querySelector('span').textContent = open ? '−' : '+';
}
toggle.addEventListener('click', () => setMenu(toggle.getAttribute('aria-expanded') !== 'true'));
navigation.querySelectorAll('a').forEach(link => link.addEventListener('click', () => setMenu(false)));
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
    setMenu(false);
    toggle.focus();
  }
});
document.addEventListener('click', event => {
  if (!event.target.closest('.site-header')) setMenu(false);
});

const tabs = Array.from(document.querySelectorAll('[role="tab"]'));
function selectTab(tab, focus = false) {
  tabs.forEach(item => {
    const selected = item === tab;
    item.classList.toggle('active', selected);
    item.setAttribute('aria-selected', String(selected));
    item.tabIndex = selected ? 0 : -1;
    const panel = document.getElementById(item.dataset.panel);
    panel.hidden = !selected;
    panel.classList.toggle('active', selected);
  });
  if (focus) tab.focus();
}
tabs.forEach((tab, index) => {
  tab.addEventListener('click', () => selectTab(tab));
  tab.addEventListener('keydown', event => {
    const directions = { ArrowRight: 1, ArrowLeft: -1 };
    let next;
    if (event.key in directions) next = (index + directions[event.key] + tabs.length) % tabs.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = tabs.length - 1;
    if (next !== undefined) {
      event.preventDefault();
      selectTab(tabs[next], true);
    }
  });
});
// Platform detection changes the instructions only; the download is always the full source ZIP.
const platform = navigator.userAgentData?.platform || navigator.platform || '';
if (/linux/i.test(platform) && !/android/i.test(navigator.userAgent)) selectTab(document.querySelector('#linux-tab'));
else if (/mac/i.test(platform) && navigator.maxTouchPoints <= 1) selectTab(document.querySelector('#mac-tab'));

const status = document.querySelector('#copy-status');
async function copyCommand(text) {
  if (navigator.clipboard && window.isSecureContext) {
    try { await navigator.clipboard.writeText(text); return true; } catch { /* Try the selection fallback. */ }
  }
  const previousFocus = document.activeElement;
  const field = document.createElement('textarea');
  field.value = text;
  field.setAttribute('readonly', '');
  field.style.cssText = 'position:fixed;top:-1000px;left:-1000px';
  document.body.appendChild(field);
  field.select();
  let copied = false;
  try { copied = document.execCommand('copy'); } catch { /* Show the selectable command. */ }
  field.remove();
  previousFocus?.focus();
  return copied;
}
document.querySelectorAll('.copy').forEach(button => {
  button.addEventListener('click', async () => {
    const copied = await copyCommand(button.dataset.copy);
    button.textContent = copied ? 'Copied' : 'Select command';
    button.classList.toggle('copied', copied);
    status.textContent = copied ? 'Launch command copied to clipboard.' : 'Could not copy automatically. The command is selected; copy it with your keyboard.';
    if (!copied) {
      const range = document.createRange();
      range.selectNodeContents(button.closest('.code-block').querySelector('code'));
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
    }
    window.setTimeout(() => {
      button.textContent = 'Copy';
      button.classList.remove('copied');
    }, 2200);
  });
});
document.querySelector('#year').textContent = new Date().getFullYear();
