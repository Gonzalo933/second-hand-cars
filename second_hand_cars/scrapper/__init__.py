import re
from datetime import datetime, timedelta
import scrapy
from scrapy.crawler import CrawlerProcess


class QuotesSpider(scrapy.Spider):
    name = "cars"

    def start_requests(self):
        start_urls = "https://www.coches.net/segunda-mano/"
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.5",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Cookie": "D_IID=E9DCA4E3-9821-377D-A87E-23C73A3FF25C; D_UID=5FDAFA9B-64BC-3AAE-836A-66C75B74250D; D_ZID=B3B72092-4204-3807-88C8-C253979B5189; D_ZUID=453113F1-7DF6-3989-854C-B7E3A2CE71E5; D_HID=8E3C9272-FE12-3AB8-BE85-F1A28612970E; D_SID=188.26.205.37:xLadW58vsN5LkfVSmfDhfO18l5LMVeYP6da5Ptp8+fw; cfg=1; euconsent-v2=CO6qZxNO6qZxNCBALAENA5CoAP_AAH_AAAiQGvNd_X_fb2_j-_5999t0eY1f9_6_v2wzjgeds-8Nyd_X_L8X62MyvB36pq4KuR4Eu3LBAQFlHOHcTQmQ4IkVqTLsbk2Mq7NKJ7LEilMbM2dYGHtPn9XTuZKY707s___z_3-_-___77f_r-3_3_A14Akw1L4CDMSxgJJo0qhRAhCuJDoAQAUUIwtElhASuCnZXAR6ggQAIDUBGBECDEFGLIIAAAAAkoiAEgPBAIgCIBAACAFaAhAARIAgsAJAwCAAUA0LACKIJQJCDI4KjlECAqRaKCeSMCSC52MMIAAA.YAAAAAAAAAAA; usunico=02/10/2020:18-00119915:604; useragent=0; ASP.NET_SessionId=g3xnljmbme3bwoo3pva2hl5q; ajs_anonymous_id=%22edd8821e-421c-420f-8d99-16ca494ad07d%22; SessionASM=02/10/2020:18-00119915:604343294",
            "Host": "www.coches.net",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0",
        }
        yield scrapy.http.Request(start_urls, method="GET", headers=headers, dont_filter=False)

    def parse(self, response):
        for car in response.css("div.mt-SerpList-item"):
            try:
                car_attributes = car.css(
                    "div.mt-Card-body div.mt-CardAd a.mt-CardAd-link div.mt-CardAd-middle ul.mt-CardAd-attributesList"
                )
                yield {
                    "model": car.css(
                        "div.mt-Card-body div.mt-CardAd a.mt-CardAd-link h2.mt-CardAd-title span.mt-CardAd-titleHiglight::text"
                    )
                    .get("")
                    .strip(),
                    "price": car.css(
                        "div.mt-Card-body div.mt-CardAd a.mt-CardAd-link div.mt-CardAd-top div.mt-AdPrice div.mt-AdPrice-amount strong::text"
                    )
                    .get("")
                    .strip()
                    .replace("€", "")
                    .replace(".", ""),
                    "location": car_attributes.xpath("li[1]/text()").get("").strip(),
                    "fuel_type": car.xpath("li[2]/text()").get("").strip(),
                    "year": car.xpath("li[3]/text()").get("").strip(),
                    "km": car.xpath("li[4]/text()")
                    .get("")
                    .strip()
                    .replace(".", "")
                    .replace("km", ""),
                    "date_posted": self._convert_to_datetime(
                        car.css(
                            "div.mt-CardAd a.mt-CardAd-link div.mt-CardAd-extras span.mt-CardAd-date::text"
                        )
                        .get("")
                        .strip()
                    ),
                }
            except AttributeError:
                continue

        next_page = response.css(
            'a.mt-Pagination-link.mt-Pagination-link--next::attr("href")'
        ).get()
        if next_page is not None:
            yield response.follow(next_page, self.parse)

    @staticmethod
    def _convert_to_datetime(text):
        publish_date = None
        try:
            # Match against: Ahora
            if re.match(r"^Ahora$", text):
                return datetime.now()
        except Exception:
            pass
        try:
            # Match against: Hace 2 min.
            matches = re.search(r"^\w+ (\d+) min\.$", text)
            mins_since_published = int(matches.group(1))
            return datetime.now() - timedelta(minutes=mins_since_published)
        except Exception:
            pass
        try:
            # Match against: Hoy 12:32
            # Note: coches.net shows 06:00 and 18:00 as 06:00 ...
            matches = re.search(r"^Hoy (\d+)\:(\d+)$", text)
            hour = int(matches.group(1))
            minute = int(matches.group(2))
            return datetime.now().replace(hour=hour, minute=minute)
        except Exception:
            pass
        try:
            # Match against: Ayer 12:32
            # Note: coches.net shows 06:00 and 18:00 as 06:00 ...
            matches = re.search(r"^Ayer (\d+)\:(\d+)$", text)
            hour = int(matches.group(1))
            minute = int(matches.group(2))
            return datetime.now().replace(hour=hour, minute=minute) - timedelta(days=1)
        except Exception:
            pass
        try:
            # Match against: 30/09 04:50
            # Note: coches.net shows 06:00 and 18:00 as 06:00 ...
            matches = re.search(r"^(\d+)\/(\d+) (\d+)\:(\d+)$", text)
            return datetime.now().replace(
                day=int(matches.group(1)),
                month=int(matches.group(2)),
                hour=int(matches.group(3)),
                minute=int(matches.group(4)),
            )
        except Exception:
            pass

        # TODO: There is no data from last year so I cannot build a parser for > year old ads.
        return publish_date


process = CrawlerProcess(
    settings={
        "FEEDS": {"items.json": {"format": "json"}},
        "USER_AGENT": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0",
        "DOWNLOAD_DELAY": 2,
    }
)

process.crawl(QuotesSpider)
process.start()  # the script will block here until the crawling is finished
