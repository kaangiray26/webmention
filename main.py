#!env/bin/python3
# *-* coding: utf-8 -*-

import os
import json
import requests
from lxml import etree, html
from urllib.parse import urlparse

class Webmention:
    def __init__(self):
        self.mentions_to_send =[]
        self.namespace = {
            "sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"
        }

        # Check if the files exist
        self.check_files()

        # Get sent mentions
        with open("sent.json", "r", encoding="utf-8") as f:
            self.sent_mentions = json.load(f)["mentions"]

        # Get ignored domains
        with open("ignored.json", "r", encoding="utf-8") as f:
            self.ignored_domains = json.load(f)["domains"]

    def check_files(self):
        # sent.json
        if not os.path.exists("sent.json"):
            with open("sent.json", "w", encoding="utf-8") as f:
                json.dump({
                    "mentions": []
                }, f, indent=4, ensure_ascii=False)

        # ignored.json
        if not os.path.exists("ignored.json"):
            with open("ignored.json", "w", encoding="utf-8") as f:
                json.dump({
                    "domains": []
                }, f, indent=4, ensure_ascii=False)

    def save_state(self):
        # sent.json
        with open("sent.json", "w", encoding="utf-8") as f:
            data = {
                "mentions": self.sent_mentions
            }
            json.dump(data, f, indent=4, ensure_ascii=False)

        # ignored.json
        with open("ignored.json", "w", encoding="utf-8") as f:
            data = {
                "domains": self.ignored_domains
            }
            json.dump(data, f, indent=4, ensure_ascii=False)

    def is_site_ignored(self, url) -> bool:
        # Get the domain
        domain = urlparse(url).netloc
        return domain not in self.ignored_domains

    def send_mentions(self):
        # Send the mentions
        for mention in self.mentions_to_send:
            endpoint = mention["endpoint"]
            source = mention["source"]
            target = mention["target"]
            data = {
                "source": source,
                "target": target
            }
            try:
                with requests.post(endpoint, data=data) as r:
                    print(r.status_code, r.text)
            except Exception as e:
                print("Failed to send mention:", e)
                continue

            # Add the mention to the sent list
            self.sent_mentions.append(target)

    def get_urls_from_sitemap(self) -> list:
        with requests.get("https://www.buzl.uk/sitemap.xml") as r:
            if r.status_code != 200:
                raise Exception("Failed to fetch the sitemap!")

            # Parse the XML
            document = r.text.encode()
            tree = etree.fromstring(document)
            urls = tree.xpath("//sitemap:loc/text()", namespaces=self.namespace)
            return urls

    def get_links_from_url(self, url) -> list:
        try:
            with requests.get(url) as r:
                if r.status_code != 200:
                    print("Failed to fetch:", url)
                    return []

                # Parse the HTML
                document = r.text.encode()
                tree = html.fromstring(document)
                links = tree.xpath("//a[starts-with(@href, 'https://')]/@href")

                # Filter out ignored links
                links = list(filter(self.is_site_ignored, links))
                return links
        except Exception as e:
            print("Failed to get links from URL:", e)
            return []

    def get_webmention_endpoint(self, url):
        # Get the head tag from the URL
        try:
            with requests.get(url) as r:
                if r.status_code != 200:
                    print("Failed to fetch:", url)
                    return None

                # Parse the HTML
                document = r.text
                tree = html.fromstring(document)
                links = tree.xpath(".//link[@rel='webmention']/@href")

                # Check if the link is found
                if len(links):
                    return links[0]

                # Add the domain to the ignored list
                domain = urlparse(url).netloc
                if domain not in self.ignored_domains:
                    self.ignored_domains.append(domain)
                    return None
        except Exception as e:
            print("Failed to get webmention endpoint:", e)
            return None

    def test_file_for_webmention(self, file):
        with open(file, "r", encoding="utf-8") as f:
            document = f.read()
            tree = html.fromstring(document)
            links = tree.xpath(".//link[@rel='webmention']/@href")
            print(links)

    def run(self, save=True):
        # Get the sitemap of the website
        urls = self.get_urls_from_sitemap()

        # Collect links from all URLs as items
        items = []
        for url in urls:
            _links = self.get_links_from_url(url)
            items.append({
                "url": url,
                "links": _links
            })

        # For each item in the list, check the webmention endpoint
        for (index, item) in enumerate(items):
            url = item["url"]
            links = item["links"]

            for link in links:
                endpoint = self.get_webmention_endpoint(link)
                if not endpoint:
                    continue

                # Check if the mention has been sent
                if link in self.sent_mentions:
                    continue

                # Add the message to the mentions_to_send list
                self.mentions_to_send.append({
                    "source": url,
                    "target": link,
                    "endpoint": endpoint
                })

        # Show the mentions to send
        print(f"Sending {len(self.mentions_to_send)} mentions...")
        self.send_mentions()

        # Save state
        if save:
            self.save_state()

if __name__ == "__main__":
    wm = Webmention()
    wm.run()