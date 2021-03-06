# encoding: utf-8
# vim: shiftwidth=4 expandtab
#
# PurpleNet - a Web User Interface for OpenVPN
# Copyright (C) 2009  Santtu Pajukanta
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""
Forms used during the setup process.
"""

from __future__ import with_statement

from django import forms
from django.forms.util import ErrorList
from django.conf import settings
from tempfile import NamedTemporaryFile
from purplenet.openvpn_userinterface.models import *

import os

class WritableDirectoryField(forms.CharField):
    """
    Check that the field contains the name of a directory that is writable.
    """
    def clean(self, value):
        value = super(WritableDirectoryField, self).clean(value)

        if not value:
            raise forms.ValidationError('Enter a valid directory.')

        abspath = os.path.abspath(value)

        if not os.path.isdir(abspath):
            raise forms.ValidationError('Inaccessible or not a directory.')

        try:
            with NamedTemporaryFile(dir=abspath) as f:
                # Oh yeah, I believe you now. We can write here.
                pass
        except IOError:
            raise forms.ValidationError('Directory is not writable by the web server.')

        return abspath

class SetupKeyField(forms.CharField):
    widget = forms.PasswordInput

    def clean(self, value):
        value = super(SetupKeyField, self).clean(value)

        if settings.PURPLENET_SETUP_KEY is None:
            raise forms.ValidationError("Setup is disabled from config")

        if not value == settings.PURPLENET_SETUP_KEY:
            raise forms.ValidationError("The setup key does not match")

        return value

class PasswordField(forms.CharField):
    widget = forms.PasswordInput

class SetupForm(forms.Form):
    setup_key = SetupKeyField(max_length=200,
        label="PURPLENET_SETUP_KEY from settings.py")

    ca_dir = WritableDirectoryField(max_length=200, initial="/var/lib/purplenet/ca",
        label="Base directory for Certificate Authorities")

    root_ca_cn = forms.CharField(max_length=30, initial="Root CA",
        label="Common Name for the root CA")

    server_ca_cn = forms.CharField(max_length=30, initial="Server CA",
        label="Common Name for the server CA")

    client_ca_cn = forms.CharField(max_length=30, initial="Client CA",
        label="Common Name for the client CA")
    
class StandaloneSetupForm(SetupForm):
    superuser_name = forms.CharField(max_length=30, initial="Superuser",
        label="Superuser account name")
    
    password = PasswordField(max_length=2048,
        label="Superuser password")
    
    password_again = PasswordField(max_length=2048,
        label="Superuser password (again)")

    def clean(self):
        cleaned_data = self.cleaned_data
        
        password = cleaned_data.get("password")
        password_again = cleaned_data.get("password_again")
        
        if password and password != password_again:
            msg = "The passwords do not match."
            self._errors["password"] = ErrorList([msg])
            self._errors["password_again"] = ErrorList([msg])
            
            del cleaned_data["password"]
            del cleaned_data["password_again"]
            
        return cleaned_data
    
class ShibbolethSetupForm(SetupForm):
    org_map = forms.CharField(max_length=32768, widget=forms.widgets.Textarea,
        initial="Superusers <- uid=pajukans", label="Organizational mapping")
    
    def clean(self):
        cleaned_data = self.cleaned_data
        
        org_map = cleaned_data.get("org_map")
        
        if org_map:
            try:
                validate_org_map(org_map)
            except OrgMapSyntaxError, e:
                msg = "Syntax error: " + str(e)
                self._errors["org_map"] = ErrorList([msg])
                del cleaned_data["org_map"]
            
        return cleaned_data