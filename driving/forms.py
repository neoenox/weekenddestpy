from django import forms


class SrcForm(forms.Form):
    """出発地のフォーム"""

    src = forms.CharField(
        label="出発地",
        max_length=255,
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "名称、座標どちらでも可",
                "class": "form-control col-xl",
            }
        ),
    )
    distance = forms.IntegerField(
        label="所要時間",
        required=True,
        min_value=1,
        widget=forms.TextInput(
            attrs={
                "type": "number",
                "class": "form-control col-3",
                "list": "distanceList",
                "value": "30",
                "min": "1",
            }
        ),
    )
