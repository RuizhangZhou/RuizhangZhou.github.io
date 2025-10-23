# Blog Setup Guide

Your blog is now ready! Here's how to use it and complete the setup.

## How to Use

### Creating Blog Posts

1. Go to https://github.com/RuizhangZhou/RuizhangZhou.github.io/issues/new
2. Write your post title and content (supports Markdown)
3. Add labels to categorize your post (optional)
4. Click "Submit new issue"
5. Your post will automatically appear on your blog!

### Editing Posts

1. Go to the issue on GitHub
2. Click "Edit" button
3. Make your changes
4. Changes will reflect on the blog immediately

### Deleting Posts

- Close the issue on GitHub to hide it from the blog

## Enable Comments (Giscus Setup)

To enable the comment system, follow these steps:

### 1. Enable GitHub Discussions

1. Go to https://github.com/RuizhangZhou/RuizhangZhou.github.io/settings
2. Scroll down to "Features"
3. Check "Discussions"

### 2. Get Your Repository IDs

1. Go to https://giscus.app
2. Enter your repository: `RuizhangZhou/RuizhangZhou.github.io`
3. The page will show you:
   - Repository ID (format: `R_xxxxx`)
   - Category ID (format: `DIC_xxxxx`)

### 3. Update blog.html

Open `blog.html` and replace these two lines (around line 265):

```javascript
data-repo-id="YOUR_REPO_ID"
data-category-id="YOUR_CATEGORY_ID"
```

With your actual IDs:

```javascript
data-repo-id="R_xxxxx"  // Your actual repo ID
data-category-id="DIC_xxxxx"  // Your actual category ID
```

Save the file and commit the changes.

## Video Posts

To embed videos in your posts:

### YouTube
```markdown
[![Video Title](https://img.youtube.com/vi/VIDEO_ID/0.jpg)](https://www.youtube.com/watch?v=VIDEO_ID)
```

Or simply paste the YouTube link - GitHub will auto-embed it in the issue view.

### Other Platforms

Just paste the link directly in your post, or use HTML:

```html
<iframe width="560" height="315" src="YOUR_VIDEO_URL" frameborder="0" allowfullscreen></iframe>
```

## Tips

- Use labels to organize posts by topic (e.g., "Tech", "Personal", "Tutorial")
- Use GitHub's built-in preview when writing posts
- You can use all GitHub Flavored Markdown features
- Pin important issues to keep them at the top of your blog
- Only you can create issues (posts) - others can only comment via Giscus

## Next Steps

1. Create your first blog post!
2. Enable Discussions and configure Giscus
3. Share your blog URL: https://ruizhangzhou.github.io/blog.html
