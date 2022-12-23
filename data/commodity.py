import requests
from bs4 import BeautifulSoup
from .embed_helper import create_embed, add_field
import datetime

BASE_URL = "https://eddb.io"


class Commodity:
    def __init__(self, name, link, require_black_market, threshold):
        self.name = name
        self.link = link
        self.require_black_market = require_black_market
        self.threshold = threshold

        self.last_sent_time = None
        self.last_sent = {}

        self.embed = None
        self.best_loc = {}

    def find_highest(self):
        data = requests.get(self.link).text
        soup = BeautifulSoup(data, "html.parser")

        table = soup.findAll("table")[0]

        for row in table.tbody.findAll("tr"):
            columns = row.find_all("td")
            station = columns[0].text.strip()
            link = columns[0].find("a").get("href")
            system = columns[1].text.strip()
            sell = int(columns[2].text.strip().replace(",", ""))
            compare = columns[3].text.strip()
            demand = columns[4].text.strip()
            pad = columns[5].text.strip()
            time = columns[6].text.strip()

            if sell < self.threshold:
                break
            black_market_present = self.determine_black_market(link)

            if self.require_black_market and not black_market_present:
                continue

            # We have a valid value
            embed = self.create_embed(
                station,
                system,
                sell,
                compare,
                demand,
                pad,
                time,
                link,
                black_market_present,
            )

            # print(station, link, system, sell, compare, demand, pad, time)
            self.embed = embed
            self.best_loc = {
                "station": station,
                "link": link,
                "system": system,
                "sell": sell,
                "compare": compare,
                "demand": demand,
                "pad": pad,
                "time": time,
            }
            break

    def determine_black_market(self, station):
        """Determins if a station has a black market"""
        link = f"{BASE_URL}{station}"
        data = requests.get(link).text
        soup = BeautifulSoup(data, "html.parser")
        return soup.find("span", string="Blackmarket")["class"][0] == "yesNo-yes"

    def create_embed(
        self, station, system, sell, compare, demand, pad, time, link, black_market
    ):
        embed = create_embed(
            f"{self.name}", f"System: {system} -- Station: {station}", "orange"
        )
        add_field(embed, "Price", format(sell, ","), True)
        add_field(embed, "Compare", compare, True)
        add_field(embed, "Demand", demand, True)
        add_field(embed, "Pad", pad, True)
        add_field(embed, "Time", time, True)
        add_field(embed, "Link", f"{BASE_URL}{link}", True)
        add_field(embed, "Black Market", f"{black_market}", False)

        return embed

    def send_change(self):
        self.last_sent_time = int(datetime.datetime.utcnow().timestamp())
        self.last_sent = self.best_loc

    def determine_send(self):
        if not (self.embed and self.best_loc):
            return False

        if self.last_sent_time == None:
            self.send_change()
            return True

        if int(datetime.datetime.utcnow().timestamp()) - self.last_sent >= 3600:
            self.send_change()
            return True

        if self.best_loc["price"] - self.last_sent["price"] >= 90000:
            self.send_change()
            return True

        return False

    def loop(self):
        self.find_highest()
        return self.determine_send()


if __name__ == "__main__":
    x = Commodity(
        "Low Temperature Diamonds", "https://eddb.io/commodity/276", True, 300000
    )
