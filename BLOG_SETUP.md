# Blog Setup Guide

Your blog is now ready! Here's how to use it and complete the setup.

## How to Use

### Creating Blog Posts

1. Click "New Post" button on the blog page, or go to: https://github.com/RuizhangZhou/RuizhangZhou.github.io/issues/new?labels=blog
2. Write your post title and content (supports Markdown)
3. **IMPORTANT**: Make sure the issue has the `blog` label (it will be pre-filled if you use the link above)
4. Add additional labels to categorize your post (optional, e.g., "Tech", "Tutorial")
5. Click "Submit new issue"
6. Your post will automatically appear on your blog!

**Note**: Only issues with the `blog` label will appear on your blog. This means you can still use regular GitHub Issues for development work without them showing up on your blog.

### Editing Posts

1. Go to the issue on GitHub
2. Click "Edit" button
3. Make your changes
4. Changes will reflect on the blog immediately

### Deleting Posts

- Close the issue on GitHub to hide it from the blog

## Comments System (Giscus)

The comment system is already configured! Here's how it works:

### How to Comment

1. Open any blog post
2. Scroll down to the "Comments" section
3. The Giscus widget will load automatically (may take a few seconds)
4. Readers need to sign in with their GitHub account to comment
5. You (as the repo owner) will receive notifications for new comments

### If Comments Don't Show Up

Check that GitHub Discussions is enabled:

1. Go to https://github.com/RuizhangZhou/RuizhangZhou.github.io/settings
2. Scroll down to "Features" section
3. Make sure "Discussions" is checked
4. If it wasn't enabled, enable it and refresh your blog post

The comment system uses:
- **Repository ID**: R_kgDOOZBw_Q (already configured)
- **Category ID**: DIC_kwDOOZBw_c4Cw-HI (already configured)

### Privacy

- Commenters must have a GitHub account
- Comments are stored in GitHub Discussions (public)
- You can moderate/delete comments in your repository's Discussions tab

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

- **Always add the `blog` label** to issues you want to appear on your blog
- Regular development issues (without `blog` label) won't appear on your blog
- Use additional labels to organize posts by topic (e.g., "Tech", "Personal", "Tutorial")
- Use GitHub's built-in preview when writing posts
- You can use all GitHub Flavored Markdown features
- Pin important issues to keep them at the top
- Close an issue to hide the post from your blog (like a draft or delete)
- Only you can create issues (posts) - others can only comment via Giscus

## Next Steps

1. Enable GitHub Discussions (if not already enabled):
   - Go to https://github.com/RuizhangZhou/RuizhangZhou.github.io/settings
   - Check "Discussions" under Features
2. Create your first blog post with the `blog` label!
3. Share your blog URL: https://ruizhangzhou.github.io/blog.html

## FAQ

**Q: Why don't I see a comment box?**
A: Make sure GitHub Discussions is enabled. The Giscus widget may also take a few seconds to load.

**Q: Can I still use GitHub Issues for development?**
A: Yes! Only issues with the `blog` label will appear on your blog. All other issues work normally.

**Q: How do I delete a blog post?**
A: Close the corresponding GitHub issue. Closed issues won't appear on the blog.

**Q: Can anonymous users comment?**
A: No, commenters need a GitHub account. This helps prevent spam.
