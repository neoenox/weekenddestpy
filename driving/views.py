import random

from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from geopy.distance import geodesic

from driving.forms import SrcForm
from driving.models import Dest, geoCash, routeCash
from driving.utils.api import ApiError
from driving.utils.geo import Geo
from driving.utils.route import Route
from driving.utils.wiki import Wiki


@require_http_methods(["GET"])
def driving_index(request):
    """検索画面"""

    form = SrcForm(request.GET or None)
    if not request.GET:
        return render(request, "driving/index.html", {"form": form})

    if not form.is_valid():
        return render(request, "driving/index.html", {"form": form})

    src_param = form.cleaned_data["src"]
    distance_param = form.cleaned_data["distance"]

    try:
        src = _resolve_source(src_param)

        candidates = []
        destinations = list(Dest.objects.all())
        for destination in destinations:
            distance = geodesic(
                (float(src[0]), float(src[1])),
                (float(destination.latitude), float(destination.longitude)),
            ).km
            if distance_param * 0.9 <= distance <= distance_param:
                candidates.append(destination)

        if not candidates:
            candidates = destinations

        if not candidates:
            form.add_error(None, "目的地データがありません。管理者にお問い合わせください。")
            return render(request, "driving/index.html", {"form": form})

        choice = random.choice(candidates)
        route_cache = routeCash.objects.filter(
            src=src[0] + "," + src[1],
            dest=choice.latitude + "," + choice.longitude,
        ).first()

        if route_cache is not None:
            highway = route_cache.highway
            localway = route_cache.localway
        else:
            route_response = Route().getRoute(
                [
                    {
                        "src": src_param,
                        "dest": choice.latitude + "," + choice.longitude,
                        "place_name": choice.name,
                    }
                ]
            )
            route_item = route_response["result"][0]["distance"]
            highway = route_item["highway"]
            localway = route_item["localway"]
            routeCash.objects.create(
                src=src[0] + "," + src[1],
                dest=choice.latitude + "," + choice.longitude,
                highway=highway,
                localway=localway,
            )

        wiki_summary = Wiki().getWiki(choice.name)
        params = {
            "name": choice.name,
            "src": src[0] + "," + src[1],
            "dest": choice.latitude + "," + choice.longitude,
            "highway": highway,
            "localway": localway,
            "wiki": wiki_summary or "",
        }
        return render(request, "driving/list.html", params)
    except (ApiError, KeyError, IndexError, TypeError, ValueError):
        form.add_error(
            None,
            "外部サービスから経路情報を取得できませんでした。時間をおいて再度お試しください。",
        )
        return render(request, "driving/index.html", {"form": form})


def _resolve_source(src_param):
    geocash = geoCash.objects.filter(src=src_param).first()
    if geocash is not None:
        return [geocash.latitude, geocash.longitude]

    geo_response = Geo().getGeo(src_param)
    geo_result = geo_response["result"]
    latitude = str(geo_result["latitude"])
    longitude = str(geo_result["longitude"])
    # Validate that coordinates are numeric before persisting the cache.
    float(latitude)
    float(longitude)

    geoCash.objects.create(
        src=src_param,
        latitude=latitude,
        longitude=longitude,
    )
    return [latitude, longitude]
