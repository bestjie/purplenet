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
Implementation of the certificate authority generation script. Command line
boilerplate resides in bin/mkca.
"""

from __future__ import absolute_import

from .helpers import FileExists, mkdir_check, enum_check, write_file, coalesce
from .enums import Exit, CAType, SignMode
from . import helpers, data
from . import openssl as openssl

from itertools import count

import sys, os
import logging
import random

OPENSSL_CONFIG_TEMPLATE_NAME = "mkca/openssl.cnf"

# Make sure these correspond to your configuration template.
# TODO Should these be variables in the template?
NEW_CERTS_DIR_NAME = "new_certs"
DATABASE_FILE_NAME = "index.txt"
CERT_SERIAL_FILE_NAME = "cert-serial"
CRL_SERIAL_FILE_NAME = "crl-serial"
OPENSSL_CONFIG_FILE_NAME = "openssl.cnf"
CA_KEY_FILE_NAME = "ca.key"
CA_CSR_FILE_NAME = "ca.csr"
CA_CERT_FILE_NAME = "ca.crt"

MIN_SERIAL = 0
MAX_SERIAL = 2**31-1

log = None

def mkca(dir, common_name, ca_type=CAType.CLIENT, 
        sign_mode=SignMode.SELF_SIGN, copy_dir=None,
        config=None, force=False):
    global log
    log = logging.getLogger("libpurplenet")

    dir = os.path.abspath(dir)
    new_certs_dir = os.path.join(dir, NEW_CERTS_DIR_NAME)
    database_file = os.path.join(dir, DATABASE_FILE_NAME)
    cert_serial_file = os.path.join(dir, CERT_SERIAL_FILE_NAME)
    crl_serial_file = os.path.join(dir, CRL_SERIAL_FILE_NAME)
    openssl_config_file = os.path.join(dir, OPENSSL_CONFIG_FILE_NAME)
    key_file = os.path.join(dir, CA_KEY_FILE_NAME)
    csr_file = os.path.join(dir, CA_CSR_FILE_NAME)
    cert_file = os.path.join(dir, CA_CERT_FILE_NAME)

    config = coalesce(config, data.MKCA_CONFIG)

    assert ((sign_mode != SignMode.CSR_ONLY) or
        (sign_mode == SignMode.CSR_ONLY and copy_dir is None)), \
        "copy_dir makes no sense with sign_mode == SignMode.CSR_ONLY"

    log.debug("sign_mode = %s", sign_mode)
    log.debug("ca_type = %s", ca_type)
    log.debug("force = %s", force)
    log.debug("dir = %s", dir)
    log.debug("copy_dir = %s", copy_dir)
    log.debug("config = %s", config)

    # Make directories
    mkdir_check(dir, force)
    mkdir_check(new_certs_dir, force)

    # Create an empty database file
    write_file(database_file, '', force)
    
    # Generate random serials for certs and CRLs and write them down
    cert_serial = random.randint(MIN_SERIAL, MAX_SERIAL)
    crl_serial = random.randint(MIN_SERIAL, MAX_SERIAL)
    write_file(cert_serial_file, '%08x' % cert_serial, force)
    write_file(crl_serial_file, '%08x' % crl_serial, force)

    # Initialize the context with type-specific values from
    # data.py and fill in the rest of the gaps.
    ctx = dict(data.config_data[ca_type], dir=dir)

    # Render the OpenSSL configuration file from a template
    helpers.render_to_file(openssl_config_file,
        OPENSSL_CONFIG_TEMPLATE_NAME, ctx, force)

    # Create the CA key and certificate
    if sign_mode == SignMode.SELF_SIGN:
        key, cert = openssl.create_self_signed_keypair(
            common_name=common_name, config=config)
        csr = None
    elif sign_mode == SignMode.CSR_ONLY:
        key = openssl.generate_rsa_key(config=config)
        cert = None
        csr = openssl.create_csr(key, common_name=common_name, config=config)
    elif sign_mode == SignMode.USE_CA:
        key = openssl.generate_rsa_key(config=config)
        csr = openssl.create_csr(key, common_name=common_name, config=config)
        cert = openssl.sign_certificate(csr, config=config) 
    else:
        raise AssertionError("Unknown signing mode %s in mkca",
            sign_mode)

    # Write key, csr and/or cert files
    write_file(key_file, key, force, mode=0600)
    if cert is not None:
        write_file(cert_file, cert, force)
    if csr is not None:
        write_file(csr_file, csr, force)

    # Write hash-named copy if requested
    if cert is not None and copy_dir is not None:
        hash = openssl.get_certificate_hash(cert, config=config)

        for ind in count():
            filename = os.path.join(copy_dir, "%s.%s" % (hash, ind))
            try:
                write_file(filename, cert, force=False)
                break
            except FileExists, e:
                log.info("Hash collision detected! Please disregard the above"
                    + " error message about not overwriting. Everything is"
                    + " under control.")
                continue
