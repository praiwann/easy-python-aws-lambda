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
    LCYAN = '\033[1;36m'
    ORANGE = '\033[0;33m'


prerequisites = [(r'docker-compose', r'docker-compose version (.*),', r'regex', r'1.9'),
                 (r'virtualenv', r'_is_venv', r'function'), ]

sys_env = {
    **os.environ,
}


def w_color(phrase, bc):
    return '{}{}{}'.format(bc, phrase, BColors.ENDC)


def op_print(phrase):
    print('{}{}'.format(w_color('Operation: ', BColors.LCYAN), phrase))


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


def _check_aws_env():
    l_envs = [('AWS_ACCESS_KEY_ID', os.getenv('AWS_ACCESS_KEY_ID')),
              ('AWS_SECRET_ACCESS_KEY', os.getenv('AWS_SECRET_ACCESS_KEY')),
              ('AWS_ACCOUNT_ID', os.getenv('AWS_ACCOUNT_ID')),
              ('AWS_REGION', os.getenv('AWS_REGION'))]

    print('')
    for l_env in l_envs:
        print('{}... '.format(l_env[0]), end='')
        _req_success() if l_env[1] else _req_fail()

    print('')


def _req_fail():
    print(w_color('Fail', BColors.FAIL))


def _req_success():
    print(w_color('Success', BColors.OKGREEN))


def print_process(p):
    for line in iter(p.stdout.readline, b''):
        print(w_color('>>> ', BColors.BOLD) + line.rstrip().decode('utf-8'))


def set_env(env_name, env_value):
    sys_env[env_name] = env_value


def rollback():
    op_print('Rollback process...')

    op_print('Reset tmp folder')
    subprocess.Popen(['rm -rf ./tmp && rm requirements.txt'], stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT, shell=True, env=sys_env).communicate()

    op_print('Done rollback ;)')


def run_w_rollback(func, **kwargs):
    try:
        func(**kwargs)
    except Exception as e:
        op_print_fail(e.__str__())
        rollback()


def mk_dir():
    op_print('Initiated temporary folder...')

    if Path('{}/tmp'.format(os.getcwd())).exists() and Path('{}/tmp'.format(os.getcwd())).is_dir():
        subprocess.Popen(['rm -rf ./tmp'], stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, shell=True, env=sys_env).communicate()

    subprocess.Popen(['mkdir tmp'], stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT, shell=True, env=sys_env).communicate()

    op_print('Done create temporary folder')


def cp_lfunc():
    op_print('Copy specify lambda function to temp folder')
    l_folder = sys_env.get('FUNCTION_FOLDER')
    if not l_folder:
        raise EnvironmentError('No lambda function specify')

    op_print('Copying...')
    subprocess.Popen(['cp -a {}/lambda/{}/. tmp/'.format(os.getcwd(), l_folder)],
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, env=sys_env).communicate()
    op_print('Done copy lambda function')


def user_input_env(is_build=False):
    sub_folders = [f.name for f in os.scandir('{}/lambda/'.format(os.getcwd())) if f.is_dir()]

    print(w_color('\nList all available function...\n', BColors.UNDERLINE))
    [print('{} {}'.format(w_color('({})'.format(index), BColors.BOLD), folder)) for index, folder in
     enumerate(sub_folders)]
    print('')

    while True:
        l_folder_raw = input(w_color('Specify folder index (or name) which your function live: ', BColors.BOLD))

        try:
            l_folder_index = int(l_folder_raw)
            l_folder = sub_folders[l_folder_index]
        except Exception as e:
            l_folder = l_folder_raw

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


def op_docker_down():
    op_print('Reset all docker-compose images')
    p = subprocess.Popen(['docker-compose down --rmi all'], stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, shell=True, env=sys_env)

    print_process(p)


def op_install_local():
    op_print('Scan all requirements...')
    sub_folders = [f.name for f in os.scandir('{}/lambda/'.format(os.getcwd())) if f.is_dir()]

    reqs = []
    for folder in sub_folders:
        req_path = '{}/lambda/{}/requirements.txt'.format(os.getcwd(), folder)
        if Path(req_path).exists():
            with open(req_path) as req:
                e_reqs = req.read().splitlines()
                reqs.extend(e_reqs)

    if len(reqs):
        op_print('Install all dependencies for local development...')
        p = subprocess.Popen(['pip install --upgrade {}'.format(' '.join(reqs))], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, shell=True, env=sys_env)

        print_process(p)

    op_print('Done install requirements...')


def op_test():
    run_w_rollback(user_input_env)
    run_w_rollback(cp_lfunc)

    try:
        op_print('Run dependencies installer...')
        p = subprocess.Popen(['docker-compose up install'], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, shell=True, env=sys_env)

        print_process(p)

        op_print('Run docker-lambda on test environment...')
        p = subprocess.Popen(['docker-compose up test'], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, shell=True, env=sys_env)

        print_process(p)

    finally:
        op_docker_down()
        rollback()


def op_build():
    run_w_rollback(user_input_env, is_build=True)
    run_w_rollback(cp_lfunc)

    try:
        op_print('Run dependencies installer...')
        p = subprocess.Popen(['docker-compose up install'], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, shell=True, env=sys_env)

        print_process(p)

        op_print('Run docker-lambda build and deploy to AWS')
        p = subprocess.Popen(['docker-compose up build'], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, shell=True, env=sys_env)

        print_process(p)

    finally:
        op_docker_down()
        rollback()


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
