from driving.utils.api import Api, ApiError


class Wiki(Api):
    def getWiki(self, title):
        try:
            res = super().get(
                "https://ja.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&exintro&explaintext",
                {"titles": title},
            )
            pages = res["query"]["pages"]
        except (ApiError, KeyError, TypeError):
            return None

        for value in pages.values():
            return value.get("extract")
        return None
