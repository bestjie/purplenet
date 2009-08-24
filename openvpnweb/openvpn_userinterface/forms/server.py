from django import forms

from openvpnweb.openvpn_userinterface.models import Server

class CreateServerForm(forms.ModelForm):
    class Meta:
        model = Server
        exclude = ["certificate"]