# coding: utf-8

import base64
import copy
import json
from marshmallow import pprint

import pytest
import sqlalchemy
from coprs.logic.builds_logic import BuildsLogic

from coprs.logic.users_logic import UsersLogic
from coprs.logic.coprs_logic import CoprsLogic

from tests.coprs_test_case import CoprsTestCase, TransactionDecorator


class TestProjectResource(CoprsTestCase):
    put_update_dict = {
        "description": "foo bar",
        "instructions": "cthulhu fhtagn",
        "repos": [
            "http://example.com/repo",
            "copr://foo/bar"
            "copr://g/foo/bar"
        ],
        "disable_createrepo": True,
        "build_enable_net": False,
        "homepage": "http://example.com/foobar",
        "contact": "foo@example.com",
    }

    def test_self(self):
        href = "/api_2/projects"
        r = self.tc.get(href)
        assert r.status_code == 200
        obj = json.loads(r.data)
        assert obj["_links"]["self"]["href"] == href

    def test_create_new(self, f_users, f_mock_chroots, f_users_api):
        self.db.session.add_all([self.u1, self.mc1])
        self.db.session.commit()

        chroot_name = self.mc1.name
        body = {
            "name": "test_copr",
            "chroots": [
                chroot_name,
            ],
            "additional_repos": ["copr://bar/zar", ]
        }

        r = self.request_rest_api_with_auth(
            "/api_2/projects",
            content=body, method="post")
        assert r.status_code == 201
        assert r.headers["Location"].endswith("/api_2/projects/1")

        r2 = self.tc.get("/api_2/projects/1/chroots")
        copr_chroots_dict = json.loads(r2.data)
        assert len(copr_chroots_dict["chroots"]) == 1
        assert copr_chroots_dict["chroots"][0]["chroot"]["name"] == chroot_name

    def test_get_one_not_found(self, f_users, f_mock_chroots, f_db):
        r = self.tc.get("/api_2/projects/1")
        assert r.status_code == 404

    def test_get_one(self, f_users, f_mock_chroots, f_coprs, f_db):

        p_id_list = [p.id for p in self.basic_coprs_list]
        for p_id in p_id_list:
            href = "/api_2/projects/{}".format(p_id)
            r = self.tc.get(href)
            assert r.status_code == 200
            obj = json.loads(r.data)

            assert obj["project"]["id"] == p_id
            assert obj["_links"]["self"]["href"] == href

    def test_get_one_with_chroots(self, f_users, f_mock_chroots, f_coprs, f_db):

        p_id_list = [p.id for p in self.basic_coprs_list]
        for p_id in p_id_list:
            href = "/api_2/projects/{}?show_chroots=True".format(p_id)
            r = self.tc.get(href)
            assert r.status_code == 200
            obj = json.loads(r.data)

            assert obj["project"]["id"] == p_id
            assert obj["_links"]["self"]["href"] == href
            project = CoprsLogic.get_by_id(p_id).one()
            assert len(obj["project_chroots"]) == len(project.copr_chroots)

    def test_get_one_with_builds(
            self, f_users, f_mock_chroots,
            f_coprs, f_builds, f_db):

        p_id_list = [p.id for p in self.basic_coprs_list]
        for p_id in p_id_list:
            href = "/api_2/projects/{}?show_builds=True".format(p_id)
            r = self.tc.get(href)
            assert r.status_code == 200
            obj = json.loads(r.data)

            assert obj["project"]["id"] == p_id
            assert obj["_links"]["self"]["href"] == href
            project = CoprsLogic.get_by_id(p_id).one()
            builds = BuildsLogic.get_multiple_by_copr(project).all()
            assert len(obj["project_builds"]) == len(builds)

    def test_delete_not_found(
            self, f_users, f_mock_chroots,
            f_users_api, f_db):

        href = "/api_2/projects/{}".format("1")

        r0 = self.request_rest_api_with_auth(
            href,
            method="delete"
        )
        assert r0.status_code == 404

    def test_delete_ok(
            self, f_users, f_mock_chroots,
            f_coprs, f_users_api, f_db):

        href = "/api_2/projects/{}".format(self.c1.id)

        r0 = self.request_rest_api_with_auth(
            href,
            method="delete"
        )
        assert r0.status_code == 204
        assert self.tc.get(href).status_code == 404

    def test_delete_fail_unfinished_build(
            self, f_users, f_mock_chroots,
            f_coprs, f_builds, f_users_api, f_db):

        href = "/api_2/projects/{}".format(self.c1.id)

        r0 = self.request_rest_api_with_auth(
            href,
            method="delete"
        )
        assert r0.status_code == 400

    def test_delete_fail_unfinished_project_action(
            self, f_users, f_mock_chroots,
            f_coprs, f_users_api, f_db):

        CoprsLogic.create_delete_action(self.c1)
        self.db.session.commit()
        href = "/api_2/projects/{}".format(self.c1.id)
        r0 = self.request_rest_api_with_auth(
            href,
            method="delete"
        )
        assert r0.status_code == 400

    def test_delete_wrong_user(
            self, f_users, f_mock_chroots,
            f_coprs, f_users_api, f_db):

        login = self.u2.api_login
        token = self.u2.api_token

        href = "/api_2/projects/{}".format(self.c1.id)

        r0 = self.request_rest_api_with_auth(
            href,
            method="delete",
            login=login, token=token,
        )
        assert r0.status_code == 403

    def test_project_put_ok(
            self, f_users, f_mock_chroots,
            f_coprs, f_users_api, f_db):

        href = "/api_2/projects/{}".format(self.c1.id)
        r0 = self.request_rest_api_with_auth(
            href,
            method="put",
            content=self.put_update_dict
        )
        assert r0.status_code == 201

        r1 = self.tc.get(r0.headers["Location"])
        obj = json.loads(r1.data)
        updated_project = obj["project"]
        for k, v in self.put_update_dict.items():
            assert updated_project[k] == v

    def test_project_put_wrong_user(
            self, f_users, f_mock_chroots,
            f_coprs, f_users_api, f_db):
        login = self.u2.api_login
        token = self.u2.api_token

        href = "/api_2/projects/{}".format(self.c1.id)
        r0 = self.request_rest_api_with_auth(
            href,
            method="put",
            content=self.put_update_dict,
            login=login, token=token,
        )
        assert r0.status_code == 403

    def test_project_put_not_found(
            self, f_users, f_mock_chroots, f_users_api, f_db):

        href = "/api_2/projects/1"
        r0 = self.request_rest_api_with_auth(
            href,
            method="put",
            content=self.put_update_dict,
        )
        assert r0.status_code == 404

    def test_project_put_bad_values(
            self, f_users, f_mock_chroots,
            f_coprs, f_users_api, f_db):
        href = "/api_2/projects/{}".format(self.c1.id)
        cases = []

        def add_case(field, value):
            t = copy.deepcopy(self.put_update_dict)
            t[field] = value
            cases.append(t)

        add_case("repos", "foobar")
        add_case("repos", 1)
        add_case("contact", "adsg")
        add_case("contact", "1")
        add_case("homepage", "sdg")

        for test_case in cases:
            r0 = self.request_rest_api_with_auth(
                href,
                method="put",
                content=test_case
            )
            assert r0.status_code == 400

    def test_project_put_ok_values(
            self, f_users, f_mock_chroots,
            f_coprs, f_users_api, f_db):
        href = "/api_2/projects/{}".format(self.c1.id)
        cases = []

        def add_case(field, value):
            t = copy.deepcopy(self.put_update_dict)
            t[field] = value
            cases.append(t)

        add_case("repos", [])
        add_case("repos", None)
        add_case("contact", "")
        add_case("contact", None)
        add_case("contact", "foo@bar.com")
        add_case("homepage", "http://foo.org/bar/xdeeg?sdfg")

        for test_case in cases:
            r0 = self.request_rest_api_with_auth(
                href,
                method="put",
                content=test_case
            )
            assert r0.status_code == 201