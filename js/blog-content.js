/* Issue bodies and generated articles are untrusted, even in our own repo. */
function sanitizePostContent(html) {
  if (typeof DOMPurify === 'undefined' || !DOMPurify.isSupported) {
    throw new Error('Safe content renderer unavailable');
  }
  // Math is rendered by trusted KaTeX afterwards, not accepted as raw SVG/MathML.
  return DOMPurify.sanitize(html, {
    USE_PROFILES: { html: true },
    FORBID_TAGS: ['style', 'form', 'input', 'button', 'select', 'textarea'],
    FORBID_ATTR: ['style', 'id', 'name'],
  });
}
