import subprocess
from scripts.log import logger


@logger.catch
def run_cmd(cmd, shell=True, timeout=120):
    '''
        Run command with arguments, wait to complete and return ``True`` on success.

    :param cls: The class as implicit first argument.
    :param cmd: Command string to be executed.
    :returns  : ``True`` on success, otherwise ``None``.
    :rtype    : ``bool``
    '''
    logger.debug('Execute command: {0}'.format(cmd))
    status = True
    try:
        out_bytes = subprocess.check_output(
            cmd, shell=shell, stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.CalledProcessError as e:
        out_bytes = e.output       # Output generated before error
        code = e.returncode   # Return code
        logger.error(f"run {cmd} failed,out={out_bytes},code={code}")
        status = False

    return out_bytes, status
