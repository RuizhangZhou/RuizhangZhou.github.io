# Portfolio design

The redesign uses static HTML, CSS and a small native JavaScript file. It does not require WordPress, a PHP server, a database, a paid page builder or an additional production framework.

The homepage combines a real portrait, selected work, contribution details, personal background and a small interactive illustration of the LLM Gateway retry boundary. Light and dark themes, responsive navigation, native project dialogs and restrained motion are included. Reduced-motion preferences are respected. The routing example makes no network or model-provider requests.

English and German homepages are separate static pages. Six static engineering-note pages contain three articles in both languages. They were prepared for this portfolio from the public project descriptions. Existing blog labels distinguishing personal posts from AI-generated notes remain in place.

The original supporting pages and GitHub Issues blog remain accessible. The blog's Markdown sanitization, search, filters and pagination code are preserved. The existing GitHub Actions workflow can continue compiling the Typst CVs and publishing the repository through GitHub Pages without a new build step.

The new Manrope and Instrument Serif fonts are served locally; their licenses are in the asset directory. The pre-existing blog retains its existing external rendering and commenting dependencies.

The portfolio is intended to be published at rick-zhou.com. Custom-domain configuration requires both GitHub Pages settings and IONOS DNS. A CNAME file alone does not configure a Pages site deployed with a custom GitHub Actions workflow. Keep domain-email MX and TXT records when changing website DNS.
