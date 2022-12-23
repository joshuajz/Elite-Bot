import requests
from bs4 import BeautifulSoup
import re
from threading import Thread
from .embed_helper import create_embed, add_field

BASE_URL = "https://eddb.io"


def get_commodities() -> list:
    """Provides a list with all of the commodities's links"""
    link = BASE_URL + "/commodity"
    data = requests.get(link).text
    soup = BeautifulSoup(data, "html.parser")

    # items = soup.findAll("<tr><td><a></a></td></tr>")
    items_raw = soup.findAll("a")
    items = []

    for item in items_raw:
        item_link = item.get("href")
        if re.search("\/commodity\/[0-9]", str(item_link)):
            items.append(BASE_URL + item_link)

    return items


def get_commoditiy(commoditiy: str) -> str:
    link = BASE_URL + "/commodity"
    data = requests.get(link).text
    soup = BeautifulSoup(data, "html.parser")

    item = soup.find("a", string=commoditiy).get("href")

    return BASE_URL + item


def arbitrage_calculator(commodity_link: str):
    def determine_valid_arbitrage(panel):
        trs = panel.find("tbody").findAll("tr")

        for tr in trs:
            tds = tr.findAll("td")

            # Time test
            time = int(
                tds[6]
                .find("span", {"class": "hidden"})
                .text.replace("{", "")
                .replace("}", "")
            )

            hours = time / 60 / 60
            if hours >= 25:
                continue

            # Demand/Supply test
            demand_supply = int(
                tds[4].find("span", {"class": "number"}).text.replace(",", "")
            )
            if demand_supply < 2000:
                continue

            # Pad test
            pad = tds[5].find("span", {"class": "number"}).text
            if pad != "L":
                continue

            system_link = BASE_URL + tds[1].find("a").get("href")
            system = requests.get(system_link).text
            system_soup = BeautifulSoup(system, "html.parser")

            # Distance test
            distance_sol = float(
                system_soup.find("div", {"class": "panel-body"})
                .findAll("td")[3]
                .text.replace("ly", "")
                .replace(",", "")
                .strip()
            )

            if distance_sol > 500:
                continue

            # Check for planetary
            if tr.find("i", {"class": "icon-planet"}):
                continue

            # All tests have passed
            return tr

        return None

    data = requests.get(commodity_link).text
    soup = BeautifulSoup(data, "html.parser")

    if not (
        "Minimum buying stations for" in soup.text
        and "Maximum selling stations for" in soup.text
    ):
        return -1

    panels = soup.findAll("div", {"class": "panel panel-eddb"})
    min_buy_panel = panels[2]
    max_sell_panel = panels[3]

    min_buy_valid = determine_valid_arbitrage(min_buy_panel)
    max_sell_valid = determine_valid_arbitrage(max_sell_panel)

    if not (min_buy_valid and max_sell_valid):
        return -1

    min_buy = int(
        (min_buy_valid.find("span", {"class": "number better"})).text.replace(",", "")
    )

    # max_sell =
    max_sell = int(
        (max_sell_valid.find("span", {"class": "number better"})).text.replace(",", "")
    )

    arbitrage = max_sell - min_buy

    commodity_name = soup.find("h1").findAll(text=True)[1]

    return (arbitrage, min_buy_valid, max_sell_valid, commodity_name)


def arbitrage_helper(commodity: str, max_arbitrage: dict):
    arb = arbitrage_calculator(commodity)
    if type(arb) is tuple and arb[0] > max_arbitrage["difference"]:
        max_arbitrage["difference"] = arb[0]
        max_arbitrage["commodity"] = commodity
        max_arbitrage["min_buy"] = arb[1]
        max_arbitrage["max_sell"] = arb[2]
        max_arbitrage["name"] = arb[3]


def convert_row_text(row):
    tds = row.findAll("td")

    station = tds[0].find("a")
    system = tds[1].find("a")
    row_info = {
        "station_name": station.text,
        "station_link": station.get("href"),
        "system_name": system.text,
        "system_link": system.get("href"),
        "price": tds[2].find("span").text,
        "supply": tds[4].find("span").text,
        "pad": tds[5].find("span").text,
        "time": tds[6].find("span").text.replace("{", "").replace("}", ""),
    }
    return row_info


def arbitrage_embed(max_arbitrage):
    embed = create_embed(
        "Arbitrage Calculation",
        f"**[{max_arbitrage['name']}]({BASE_URL + max_arbitrage['commodity']})**\nDifference: {format(max_arbitrage['difference'], ',')}",
        "cyan",
    )

    add_field(
        embed,
        "Buy",
        f"Station: [{max_arbitrage['min_buy']['station_name']}]({BASE_URL + max_arbitrage['min_buy']['station_link']})\nSystem: [{max_arbitrage['min_buy']['system_name']}]({BASE_URL + max_arbitrage['min_buy']['system_link']})\nPrice: {max_arbitrage['min_buy']['price']}\nSupply: {max_arbitrage['min_buy']['supply']}\nTime: {round(int(max_arbitrage['min_buy']['time']) / 60 / 60, 2)} hrs",
        True,
    )

    add_field(
        embed,
        "Sell",
        f"Station: [{max_arbitrage['max_sell']['station_name']}]({BASE_URL + max_arbitrage['max_sell']['station_link']})\nSystem: [{max_arbitrage['max_sell']['system_name']}]({BASE_URL + max_arbitrage['max_sell']['system_link']})\nPrice: {max_arbitrage['max_sell']['price']}\nSupply: {max_arbitrage['max_sell']['supply']}\nTime: {round(int(max_arbitrage['max_sell']['time']) / 60 / 60, 2)} hrs",
        True,
    )

    return embed


def arbitrage_finder():
    commodities = get_commodities()

    max_arbitrage = {"difference": -1, "commodity": None}
    threads = []

    for commoditiy in commodities:
        thread = Thread(target=arbitrage_helper, args=(commoditiy, max_arbitrage))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    if len(max_arbitrage.keys()) == 5:
        max_arbitrage["min_buy"] = convert_row_text(max_arbitrage["min_buy"])
        max_arbitrage["max_sell"] = convert_row_text(max_arbitrage["max_sell"])

    return arbitrage_embed(max_arbitrage)


if __name__ == "__main__":
    test = arbitrage_finder()
    print(test)
