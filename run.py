from __future__ import print_function
from pathlib import Path

import os
import sys
import re
import subprocess


class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


prerequisites = [(r'docker-compose', r'docker-compose version (.*),', r'regex', r'1.9'),
                 (r'virtualenv', r'_is_venv', r'function'), ]

sys_env = {
    **os.environ,
}


def w_color(phrase, bc):
    return '{}{}{}'.format(bc, phrase, BColors.ENDC)


def op_print(phrase):
    print('{}{}'.format(w_color('Operation: ', BColors.BOLD), phrase))


def op_print_fail(phrase):
    print('{}{}'.format(w_color('Operation Fail: ', BColors.FAIL), phrase))


def _is_venv():
    return (hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))


def _req_ver(_req, _in_use):
    _reqs = _req.split('.')
    _in_uses = _in_use.split('.')

    res = False
    for index, value in enumerate(_reqs):
        try:
            i_req = int(value)
            i_use = int(_in_uses[index])
        except Exception as e:
            break

        if i_req >= i_use:
            continue

        res = True
        break

    return res


def _req_fail():
    print(w_color('Fail', BColors.FAIL))


def _req_success():
    print(w_color('Success', BColors.OKGREEN))


def print_process(p):
    for line in iter(p.stdout.readline, b''):
        print(w_color('>>> ', BColors.BOLD) + line.rstrip().decode('utf-8'))


def get_sitepackage_path(venv_path):
    return '{}/lib/python3.6/site-packages'.format(venv_path)


def set_env(env_name, env_value):
    sys_env[env_name] = env_value
    # subprocess.Popen(['export {}={}'.format(env_name, env_value)], stdout=subprocess.PIPE,
    #                  stderr=subprocess.STDOUT, shell=True).communicate()


def unset_env(env_name):
    subprocess.Popen(['unset {}'.format(env_name)], stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT, shell=True, env=sys_env).communicate()


def rollback():
    op_print('Rollback process...')

    subprocess.Popen(['rm -rf ./tmp && rm requirements.txt'], stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT, shell=True, env=sys_env).communicate()

    op_print('Done rollback ;)')


def run_w_rollback(func, **kwargs):
    try:
        func(**kwargs)
    except Exception as e:
        op_print_fail(e.__str__())
        rollback()


def cp_venv():
    op_print('Copy python dependencies from venv for mount volume to docker')
    venv_path = os.getenv('VIRTUAL_ENV')
    if not venv_path:
        raise EnvironmentError('No virtual environment active')

    print('VIRENV_PATH: {}'.format(venv_path))
    op_print('Copying...')
    subprocess.Popen(['mkdir tmp && cp -a {}/. tmp/'.format(get_sitepackage_path(venv_path))], stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT, shell=True, env=sys_env).communicate()
    op_print('Done copy site-packages')


def user_input_env(is_build=False):
    while True:
        l_folder = input(w_color('Specify folder which your function live: ', BColors.BOLD))
        full_path = '{}/lambda/{}'.format(os.getcwd(), l_folder)
        if Path(full_path).exists() and Path(full_path).is_dir():
            break

        print('No path found!!, don\'t troll me!!')

    l_module = input(w_color('Specify AWS Lambda module :(default -> lambda_function.lambda_handler) ', BColors.BOLD))
    if not l_module:
        print('No input provided for lambda module... use default(lambda_function.lambda_handler)')
        l_module = 'lambda_function.lambda_handler'

    set_env('LAMBDA_MODULE', l_module)
    set_env('FUNCTION_FOLDER', l_folder)

    if is_build:
        while True:
            l_fname = input(w_color('Specify AWS Lambda function name: ', BColors.BOLD))
            if l_fname:
                break

            print('No default for this ENV!! don\'t you know lambda function?!!')

        set_env('LAMBDA_FUNCTION_NAME', l_fname)


def op_install_local():
    pass


def op_test():
    run_w_rollback(cp_venv)
    run_w_rollback(user_input_env)

    try:
        op_print('Run docker-lambda on test environment...')
        p = subprocess.Popen(['docker-compose up test'], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, shell=True, env=sys_env)

        print_process(p)

        op_print('Reset all docker-compose images')
        p = subprocess.Popen(['docker-compose down --rmi all'], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, shell=True, env=sys_env)

        print_process(p)

    finally:
        rollback()


def op_build():
    pass


def run():
    op_print('checking requirement...')

    pre_res = True
    for req in prerequisites:
        print('{}... '.format(req[0]), end='')
        res_ver, err = subprocess.Popen(['{} --version'.format(req[0])], stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, shell=True, env=sys_env).communicate()

        res_ver = res_ver.decode('utf-8')
        if req[2] == 'regex':
            p = re.compile(req[1])
            m = p.match(res_ver)
            if not m:
                _req_fail()
                pre_res = False
                continue

            if not _req_ver(req[3], m.group(1)):
                _req_fail()
                pre_res = False
                continue

            _req_success()
            continue

        if req[2] == 'function':
            func = req[1]
            res_call = False
            possibles = globals().copy()
            possibles.update(locals())
            method = possibles.get(func)

            if callable(method):
                res_call = method()

            if not res_call:
                _req_fail()
                pre_res = False
                continue

            _req_success()
            continue

    if not pre_res:
        print('Some prerequisite not meet builder requirement, abort process...', BColors.WARNING)
        exit()

    print(w_color('####### Welcome !! #######', BColors.HEADER))
    print('Please select (no.) option below:\n\n'
          '{} Install all dependencies for development\n'
          '{} Run lambda test on local environment\n'
          '{} Build and deploy to AWS Lambda\n'.format(w_color('(1)', BColors.BOLD), w_color('(2)', BColors.BOLD),
                                                       w_color('(3)', BColors.BOLD)))

    while True:
        op_option = input(w_color('Your option: ', BColors.BOLD))
        if op_option in ['1', '2', '3']:
            break

        print('You not select any option available..., do not troll me, damn you!!')

    print('Option {} selected...'.format(op_option))
    op_option = int(op_option)

    if op_option == 1:
        op_install_local()
    elif op_option == 2:
        op_test()
    elif op_option == 3:
        op_build()

    print(w_color('\n####### End operation #######', BColors.HEADER))


if __name__ == '__main__':
    run()
