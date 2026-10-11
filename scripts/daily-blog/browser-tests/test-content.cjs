const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const { test } = require('node:test');
const { JSDOM } = require('jsdom');
const createDOMPurify = require('dompurify');
const { marked } = require('marked');

const root = resolve(__dirname, '../../..');
const page = readFileSync(resolve(root, 'blog.html'), 'utf8');
const sanitizer = readFileSync(resolve(root, 'js/blog-content.js'), 'utf8');

function render(markdown) {
  const dom = new JSDOM('', { runScripts: 'outside-only' });
  dom.window.DOMPurify = createDOMPurify(dom.window);
  dom.window.eval(sanitizer);
  dom.window.document.body.innerHTML = dom.window.sanitizePostContent(marked.parse(markdown));
  return dom.window.document.body;
}

test('page uses the tested sanitizer before insertion, with the tested pinned library', () => {
  assert.match(page, /dompurify@3\.4\.16\/dist\/purify\.min\.js/);
  assert.match(page, /integrity="sha384-[^"]+"/);
  assert.match(page, /src="js\/blog-content\.js"/);
  assert.match(page, /const content = sanitizePostContent\(marked\.parse\(preprocessMath/);
});

test('raw HTML scripts, event handlers, javascript links and embeds are stripped', () => {
  const body = render('<script>alert(1)</script><img src=x onerror="alert(1)">\n' +
    '<a href="javascript:alert(1)">click</a><iframe srcdoc="bad"></iframe>' +
    '<svg onload="alert(1)"></svg><math><mtext onclick="alert(1)">x</mtext></math>');
  assert.equal(body.querySelector('script, iframe, svg, math'), null);
  for (const node of body.querySelectorAll('*')) {
    for (const attr of node.attributes) {
      assert.ok(!attr.name.startsWith('on'));
      assert.ok(!attr.value.toLowerCase().startsWith('javascript:'));
    }
  }
});

test('CSS and form/clobbering payloads cannot alter the surrounding page', () => {
  const body = render('<style>body{display:none}</style><form id="main"><input name="location"></form>' +
    '<p id="main" name="DOMPurify" style="position:fixed">safe</p>');
  assert.equal(body.querySelector('style, form, input, [style], [id], [name]'), null);
  assert.match(body.textContent, /safe/);
});

test('normal Markdown tables, links, code and math delimiters remain readable', () => {
  const body = render('# Heading\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n' +
    '[Source](https://example.org)\n\n`<script>`\n\n$$x^2 + y^2$$');
  assert.equal(body.querySelector('h1').textContent, 'Heading');
  assert.equal(body.querySelectorAll('td').length, 2);
  assert.equal(body.querySelector('a').getAttribute('href'), 'https://example.org');
  assert.equal(body.querySelector('code').textContent, '<script>');
  assert.match(body.textContent, /\$\$x\^2 \+ y\^2\$\$/);
});

test('missing sanitizer fails closed instead of falling back to unsafe HTML', () => {
  const dom = new JSDOM('', { runScripts: 'outside-only' });
  dom.window.eval(sanitizer);
  assert.throws(() => dom.window.sanitizePostContent('<img onerror="bad">'), /unavailable/);
});
