import argparse
from pathlib import Path
from typing import ClassVar

import googlemaps
import requests
import yaml
from bs4 import BeautifulSoup


class BoligInfo:
    _destinations: ClassVar[dict[str, str]] = {
        "durup": "Søndervang 4, 7870 Roslev, Denmark",
        "hobro": "Søndertoften 24, 9500 Hobro, Denmark",
        "net": "Gasværksvej 20, 9000 Aalborg, Denmark",
        "wrist": "Stigsborgvej 60, 9400 NørresundbyS, Denmark",
    }

    def __init__(self, args: argparse.Namespace) -> None:
        config_path = Path(args.config_path)
        with config_path.open() as file:
            prime_service = yaml.safe_load(file)

        self.api = prime_service["api"]

        if args.new_address is not None:
            self._add_new_addresses(args.new_address)

        self.info: dict[str, None | str] = {
            "address": None,
            "price": None,
            "house_area": None,
            "total_area": None,
        }
        self.distances: dict[str, str] = {}

        self._get_bolig_info(args.url)
        self._get_dist()

    def _get_bolig_info(self, url: str) -> None:
        # Making a GET request
        request = requests.get(url)

        soup = BeautifulSoup(request.content, "html.parser")
        address_result = soup.find("h1", class_="text-blue-900 space-y-1")
        if address_result is not None:
            self.info["address"] = address_result.text

        price_result = soup.find(
            "h2", class_="text-[28px] text-blue-900 font-bold xl:text-3xl"
        )
        if price_result is not None:
            self.info["price"] = price_result.text

        total_area_result = soup.find_all(
            "span",
            class_="text-blue-900 whitespace-nowrap text-xs leading-normal sm:text-sm",
        )[1]
        if total_area_result is not None:
            self.info["total_area"] = total_area_result.text

        house_area_result = soup.find_all(
            "span",
            class_="text-blue-900 whitespace-nowrap text-xs leading-normal sm:text-sm border-dashed border-b border-blue-900 pb-0.5 cursor-pointer",
        )[0]
        if house_area_result is not None:
            self.info["house_area"] = house_area_result.text

    def _get_dist(self) -> None:
        gmaps = googlemaps.Client(key=self.api)
        result = gmaps.distance_matrix(
            origins=[self.info["address"]],
            destinations=list(self._destinations.values()),
            mode="driving",
        )
        distances = {}

        for i, element in enumerate(result["rows"][0]["elements"]):
            distances[list(self._destinations.keys())[i]] = element["duration"]["text"]

        self.distances = distances

    def _add_new_addresses(self, adresses: list) -> None:
        for i, a in enumerate(adresses):
            self._destinations[f"new_address_{i}"] = a

    def print_info(self) -> None:
        print("----Gener----\n")
        for k, v in self.info.items():
            if k != "distances":
                print(f"{k}: {v}\n")
        print("\n ----Distances----")
        for k, v in self.distances.items():
            print(f"{k} ({self._destinations[k]}): {v}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Bolig Scraper",
        description="Scrape a side to boligsiden.dk and logs the distance to different addresses",
    )

    parser.add_argument("url", type=str)
    parser.add_argument(
        "-c", "--config_path", default="/home/jam/privat/bolig_scraper/config/api.yaml"
    )
    parser.add_argument("-n", "--new_address", nargs="+", default=None)

    bolig_info = BoligInfo(parser.parse_args())
    bolig_info.print_info()
