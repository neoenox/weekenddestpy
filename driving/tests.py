from unittest.mock import Mock, patch

import requests
from django.test import TestCase
from django.urls import reverse

from driving.models import Dest
from driving.utils.api import Api, ApiError


class DrivingViewTests(TestCase):
    def test_invalid_distance_is_reported_by_form(self):
        with patch("driving.views.Geo.getGeo") as get_geo:
            response = self.client.get(
                reverse("driving:driving_index"),
                {"src": "Tokyo", "distance": "abc"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"]["distance"].errors)
        get_geo.assert_not_called()

    @patch(
        "driving.views.Geo.getGeo",
        return_value={"result": {"latitude": 35.0, "longitude": 139.0}},
    )
    def test_empty_destination_table_returns_form_error(self, _get_geo):
        response = self.client.get(
            reverse("driving:driving_index"),
            {"src": "Tokyo", "distance": "30"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "目的地データがありません")

    @patch("driving.views.Geo.getGeo", side_effect=ApiError("upstream failed"))
    def test_upstream_api_error_returns_form_error(self, _get_geo):
        Dest.objects.create(
            name="Somewhere",
            latitude="35.1",
            longitude="139.1",
            address="address",
        )

        response = self.client.get(
            reverse("driving:driving_index"),
            {"src": "Tokyo", "distance": "30"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "外部サービスから経路情報を取得できませんでした")


class ApiTests(TestCase):
    @patch("driving.utils.api.requests.get")
    def test_get_uses_timeout_and_raises_for_http_failure(self, get):
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError("503")
        get.return_value = response

        with self.assertRaises(ApiError):
            Api().get("https://example.test", {"q": "x"})

        get.assert_called_once_with(
            "https://example.test",
            params={"q": "x"},
            timeout=Api.TIMEOUT,
        )

    @patch("driving.utils.api.requests.post")
    def test_post_uses_timeout_and_rejects_non_object_json(self, post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = []
        post.return_value = response

        with self.assertRaises(ApiError):
            Api().post("https://example.test", {"routes": []})
