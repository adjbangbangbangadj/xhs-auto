"""
Disabled experimental MCP server for Xiaohongshu (小红书) content publishing.

Phase 1 does not use this package. It is not imported or called by pipeline,
app.py, or web_app.py. The active project boundary remains: generate content
packages only, then publish manually after human review.

Provides tools for:
- xhs_login: QR-code login & cookie persistence
- xhs_check_login: Verify authentication status
- xhs_publish_post: Publish a single post with title, content, images, tags
- xhs_publish_from_file: Parse reviewed markdown and publish
- xhs_batch_publish: Batch publish all reviewed posts
"""
