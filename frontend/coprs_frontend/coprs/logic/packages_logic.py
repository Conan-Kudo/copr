import json
import time
from sqlalchemy import or_
from sqlalchemy import and_
from sqlalchemy.sql import false, true

from coprs import app
from coprs import db
from coprs import exceptions
from coprs import models
from coprs import helpers

from coprs.logic import coprs_logic
from coprs.logic import users_logic

from coprs.constants import DEFAULT_BUILD_TIMEOUT

log = app.logger


class PackagesLogic(object):
    @classmethod
    def get_all(cls, copr_id):
        return (models.Package.query
                .filter(models.Package.copr_id == copr_id))

    @classmethod
    def get(cls, copr_id, package_name):
        return models.Package.query.filter(models.Package.copr_id == copr_id,
                                           models.Package.name == package_name)

    @classmethod
    def get_for_webhook_rebuild(cls, copr_id, webhook_secret, clone_url):
        return (models.Package.query.join(models.Copr)
                .filter(models.Copr.webhook_secret == webhook_secret)
                .filter(models.Package.copr_id == copr_id)
                .filter(models.Package.webhook_rebuild == true())
                .filter(models.Package.source_json.contains(clone_url)))

    @classmethod
    def add(cls, user, copr, package_name):
        users_logic.UsersLogic.raise_if_cant_build_in_copr(
            user, copr,
            "You don't have permissions to build in this copr.")

        if cls.exists(copr.id, package_name).all():
            raise exceptions.DuplicateException(
                "Project {}/{} already has a package '{}'"
                .format(copr.owner.name, copr.name, package_name))

        source_type = helpers.BuildSourceEnum("unset")
        source_json = json.dumps({})

        package = models.Package(
            name=package_name,
            copr_id=copr.id,
            source_type=source_type,
            source_json=source_json
        )

        db.session.add(package)

        return package

    @classmethod
    def add_build(cls, package, build, git_hash, version):
        package_build = models.PackageBuild(
            package_id=package.id,
            build_id=build.id,
            git_hash=git_hash,
            version=version
        )
        db.session.add(package_build)
        return package_build

    @classmethod
    def exists(cls, copr_id, package_name):
        return (models.Package.query
                .filter(models.Package.copr_id == copr_id)
                .filter(models.Package.name == package_name))

