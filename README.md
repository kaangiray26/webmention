# webmention-action
Automatically send webmentions using GitHub Actions

## About
For this action to work, you need to have a webmention.io account and a token. You can get a token by signing up at [webmention.io](https://webmention.io) and then going to the settings page. Also, you need to have a `sitemap.xml` in your website so that the action can find all the URLs to parse and collect links.

## How does it work?
This action will trigger when there is a deployment in the repository. Once the action is triggered, it will get the `sitemap.xml` file from your website, parse it, and collect all the URLs. Then, for each URL, it will get the content of the page, find all the links, and send a webmention to each link. After sending all the webmentions, it will create a release with the checked URLs to save the latest state of the webmentions, so that it doesn't send the same webmention again in a future deployment.