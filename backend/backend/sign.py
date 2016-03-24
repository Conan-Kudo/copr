#!/usr/bin/env python
# coding: utf-8

"""
Wrapper for /bin/sign from obs-sign package
"""

from subprocess import Popen, PIPE
import json

import os
from requests import request

from .exceptions import CoprSignError, CoprSignNoKeyError, \
    CoprKeygenRequestError


SIGN_BINARY = "/bin/sign"
DOMAIN = "fedorahosted.org"


def create_gpg_email(username, projectname):
    """
    Creates canonical name_email to identify gpg key
    """

    return "{}#{}@copr.{}".format(username, projectname, DOMAIN)


def get_pubkey(username, projectname, outfile=None):
    """
    Retrieves public key for user/project from signer host.

    :param outfile: [optional] file to write obtained key
    :return: public keys

    :raises CoprSignError: failed to retrieve key, see error message
    :raises CoprSignNoKeyError: if there are no such user in keyring
    """
    usermail = create_gpg_email(username, projectname)
    cmd = ["sudo", SIGN_BINARY, "-u", usermail, "-p"]

    try:
        handle = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = handle.communicate()
    except Exception as e:
        raise CoprSignError("Failed to get user pubkey"
                            " due to: {}".format(e))

    if handle.returncode != 0:
        if "unknown key:" in stderr:
            raise CoprSignNoKeyError(
                "There are no gpg keys for user {} in keyring".format(username),
                returncode=handle.returncode,
                cmd=cmd, stdout=stdout, stderr=stderr)
        raise CoprSignError(
            msg="Failed to get user pubkey\n"
                "sign stdout: {}\n sign stderr: {}\n".format(stdout, stderr),
            returncode=handle.returncode,
            cmd=cmd, stdout=stdout, stderr=stderr)

    if outfile:
        with open(outfile, "w") as handle:
            handle.write(stdout)

    return stdout


def _sign_one(path, email):
    cmd = ["sudo", SIGN_BINARY, "-u", email, "-r", path]

    try:
        handle = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = handle.communicate()
    except Exception as e:
        err = CoprSignError(
            msg="Failed to  invoke sign {} by user {} with error {}"
            .format(path, email, e, cmd=None, stdout=None, stderr=None))

        raise err

    if handle.returncode != 0:
        err = CoprSignError(
            msg="Failed to sign {} by user {}".format(path, email),
            returncode=handle.returncode,
            cmd=cmd, stdout=stdout, stderr=stderr)

        raise err

    return stdout, stderr


def sign_rpms_in_dir(username, projectname, path, opts, log):
    """
    Signs rpms using obs-signd.

    If some some pkgs failed to sign, entire build marked as failed,
    but we continue to try sign other pkgs.

    :param username: copr username
    :param projectname: copr projectname
    :param path: directory with rpms to be signed
    :param Munch opts: backend config

    :type log: logging.Logger

    :raises: :py:class:`backend.exceptions.CoprSignError` failed to sign at least one package
    """
    rpm_list = [
        os.path.join(path, filename)
        for filename in os.listdir(path)
        if filename.endswith(".rpm")
    ]

    if not rpm_list:
        return

    try:
        get_pubkey(username, projectname)
    except CoprSignNoKeyError:
        create_user_keys(username, projectname, opts)

    errors = []  # tuples (rpm_filepath, exception)
    for rpm in rpm_list:
        try:
            _sign_one(rpm, create_gpg_email(username, projectname))
            log.info("signed rpm: {}".format(rpm))

        except CoprSignError as e:
            log.exception("failed to sign rpm: {}".format(rpm))
            errors.append((rpm, e))

    if errors:
        raise CoprSignError("Rpm sign failed, affected rpms: {}"
                            .format([err[0] for err in errors]))


def create_user_keys(username, projectname, opts):
    """
    Generate a new key-pair at sign host

    :param username:
    :param projectname:
    :param opts: backend config

    :return: None
    """
    data = json.dumps({
        "name_real": "{}_{}".format(username, projectname),
        "name_email": create_gpg_email(username, projectname)
    })

    keygen_url = "http://{}/gen_key".format(opts.keygen_host)
    query = dict(url=keygen_url, data=data, method="post")
    try:
        response = request(**query)
    except Exception as e:
        raise CoprKeygenRequestError(
            msg="Failed to create key-pair for user: {},"
                " project:{} with error: {}"
            .format(username, projectname, e), request=query)

    if response.status_code >= 400:
        raise CoprKeygenRequestError(
            msg="Failed to create key-pair for user: {}, project:{}, status_code: {}, response: {}"
            .format(username, projectname, response.status_code, response.text),
            request=query, response=response)
