from django import forms

from .models import Baho, Fakultet, Fan, Guruh, Menyu, Talaba, Yozuv


class BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs.setdefault("class", css)


class MenyuForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Menyu
        fields = "__all__"


class YozuvForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Yozuv
        fields = ["sarlavha", "matn"]


class FakultetForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Fakultet
        fields = "__all__"


class GuruhForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Guruh
        fields = "__all__"


class FanForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Fan
        fields = "__all__"


class TalabaForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Talaba
        exclude = ["yaratilgan"]
        widgets = {"tugilgan_sana": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}


class BahoForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Baho
        fields = "__all__"
        widgets = {"sana": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}
