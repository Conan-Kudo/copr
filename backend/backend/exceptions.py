class MockRemoteError(Exception):
    def __init__(self, msg):
        super(MockRemoteError, self).__init__(msg)
        self.msg = msg

    def __str__(self):
        return self.msg


class BuilderError(MockRemoteError):
    def __init__(self, msg, returncode=None, stdout=None, stderr=None):
        super(BuilderError, self).__init__(msg)

        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        result = "BuildError: {}".format(self.msg)
        if self.returncode:
            result += "; return code: {}".format(self.returncode)
        if self.stdout:
            result += "; stdout: {}".format(self.stdout)
        if self.stderr:
            result += "; stderr: {}".format(self.stderr)
        return result


class AnsibleCallError(BuilderError):
    pass


class CoprSignError(MockRemoteError):
    """
    Related to invocation of /bin/sign

    has additional  fields:
    :ivar cmd: command which was executed
    :ivar stdout: message content
    :ivar stderr: error message
    """

    def __init__(self, msg, cmd=None, stdout=None, stderr=None,
                 returncode=None):

        super(CoprSignError, self).__init__(msg)
        self.cmd = cmd
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        out = super(CoprSignError, self).__str__()
        if self.cmd:
            out += ("\n"
                    "return code {} after invocation of: {} \n"
                    "stderr: {}\n"
                    "stdout: {}\n").format(
                        self.returncode, self.cmd, self.stdout, self.stderr)
        return out


class CoprSignNoKeyError(CoprSignError):
    pass


class CoprKeygenRequestError(MockRemoteError):
    """
    Errors during request to copr-keygen service

    has additional  fields:
    :ivar request: tuple of parameters for request.request
    :ivar response: requests.Response
    """

    def __init__(self, msg, request=None, response=None):
        super(CoprKeygenRequestError, self).__init__(msg)
        self.request = request
        self.response = response

    def __str__(self):
        out = super(CoprKeygenRequestError, self).__str__()
        out += "\nrequest to copr-keygen: {}\n".format(self.request)
        if self.response:
            out += "status code: {}\n" "response content: {}\n" \
                .format(self.response.status_code, self.response.content)
        return out


class CoprBackendError(Exception):
    def __init__(self, msg):
        super(CoprBackendError, self).__init__()
        self.msg = msg

    def __str__(self):
        return self.msg


class CoprJobGrabError(CoprBackendError):
    pass


class CoprWorkerError(CoprBackendError):
    pass


class CoprSpawnFailError(CoprBackendError):
    pass


class VmError(CoprBackendError):
    """
    Error related to VM manage
    """
    pass


class VmDescriptorNotFound(VmError):
    pass


class NoVmAvailable(VmError):
    pass

class VmSpawnLimitReached(VmError):
    """
    Couldn't spawn more VM due to the given limits
    """
    pass

class CmdError(CoprBackendError):
    def __init__(self, msg, cmd, exit_code=None, stdout=None, stderr=None):
        super(CmdError, self).__init__(msg)

        self.cmd = cmd
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        out = super(CmdError, self).__str__()
        if self.cmd:
            out += ("\n"
                    "return code {} after invocation of: {} \n"
                    "stderr: {}\n"
                    "stdout: {}\n").format(
                        self.exit_code, self.cmd, self.stdout, self.stderr)
        return out


class CreateRepoError(CmdError):
    pass
