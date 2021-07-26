import logging
from modules import util
from modules.util import Failed

logger = logging.getLogger("Plex Meta Manager")

builders = ["icheckmovies_list", "icheckmovies_list_details"]
base_url = "https://www.icheckmovies.com/lists/"

class ICheckMovies:
    def __init__(self, config):
        self.config = config

    def _request(self, url, language, xpath):
        return self.config.get_html(url, headers=util.header(language)).xpath(xpath)

    def _parse_list(self, list_url, language):
        imdb_urls = self._request(list_url, language, "//a[@class='optionIcon optionIMDB external']/@href")
        return [t[t.find("/tt") + 1:-1] for t in imdb_urls]

    def get_list_description(self, list_url, language):
        descriptions = self._request(list_url, language, "//div[@class='span-19 last']/p/em/text()")
        return descriptions[0] if len(descriptions) > 0 and len(descriptions[0]) > 0 else None

    def validate_icheckmovies_lists(self, icheckmovies_lists, language):
        valid_lists = []
        for icheckmovies_list in util.get_list(icheckmovies_lists, split=False):
            list_url = icheckmovies_list.strip()
            if not list_url.startswith(base_url):
                raise Failed(f"ICheckMovies Error: {list_url} must begin with: {base_url}")
            elif len(self._parse_list(list_url, language)) > 0:
                valid_lists.append(list_url)
            else:
                raise Failed(f"ICheckMovies Error: {list_url} failed to parse")
        return valid_lists

    def get_items(self, method, data, language):
        pretty = util.pretty_names[method] if method in util.pretty_names else method
        movie_ids = []
        if method == "icheckmovies_list":
            logger.info(f"Processing {pretty}: {data}")
            imdb_ids = self._parse_list(data, language)
            total_ids = len(imdb_ids)
            for i, imdb_id in enumerate(imdb_ids, 1):
                try:
                    util.print_return(f"Converting IMDb ID {i}/{total_ids}")
                    movie_ids.append(self.config.Convert.imdb_to_tmdb(imdb_id))
                except Failed as e:
                    logger.error(e)
            logger.info(util.adjust_space(f"Processed {total_ids} IMDb IDs"))
        else:
            raise Failed(f"ICheckMovies Error: Method {method} not supported")
        logger.debug("")
        logger.debug(f"{len(movie_ids)} TMDb IDs Found: {movie_ids}")
        return movie_ids, []
