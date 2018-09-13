### Easy Python AWS Lambda

References repo -> [docker-lambda][4] by lambci, [python-amazonlinux][5] by RealSalmon.

This Python repo will help you to develop, test (on virtual AWS Lambda via docker) and build/deploy to AWS Lambda easily.

### Prerequisites
- **Working on Max OSX only.**
- Minimum 4GB disk space required (reserved for docker images).
- Python version 3.6 (manage python version very very easy by using [pyenv]).
- Python Virtualenv either use [virtualenv][0] or [pyenv-virtualenv][1].
- Docker Compose version >= 1.9.
- AWS IAM with Lambda & S3 Roles apply (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are required).
- Indeed!!, some Python knowledge.

### Setup
- Checks and satisfied prerequisites.
- Activated virtualenv for this repo (on local) follow these step -> [virtualenv][2] or [pyenv-virtualenv][3] (depend on virtualenv management you use).
- Let's Rock!!

### Get started...
See /lambda/example directory for an example usage.

You can create new directory beneath /lambda for any lambda module. All dir will have their own python dependencies (list by requirements.txt and **can't use a specific version** for now).

Lambda module and its handler function could be named in your favour, the script will ask for them later.

Try it by simple run...
```
python run.py
```

You will see 3 options available if pass python and virtualenv prerequisite checked.

1. Install all python dependencies to your virtualenv for development process (better for working with IDE Autocomplete) which defined in each lambda module directory (by using requirements.txt)
2. Run test function on AWS Lambda environment (operate by docker). When you run this option, event.json will be inject for testing the handler.
3. Build and deploy to AWS Lambda. **S3 Bucket is needed**, the script will upload the zip file to S3 (named s3://<bucket-name>/lambda/<function-name>-\<timestamp>.zip) and lambda will pull from it to replace function. Also please make sure **_all of your python dependencies should not produce a very large zip file_** because of the limit of Lambda for Compress package is just 50MB. See details [AWS Lambda Limit][6]

After choose the option... follow the step to proceed and that's it.

[pyenv]: https://github.com/pyenv/pyenv
[0]: https://github.com/pypa/virtualenv
[1]: https://github.com/pyenv/pyenv-virtualenv
[2]: https://virtualenv.pypa.io/en/stable/userguide/#usage
[3]: https://github.com/pyenv/pyenv-virtualenv#usage
[4]: https://github.com/lambci/docker-lambda
[5]: https://github.com/RealSalmon/docker-amazonlinux-python
[6]: https://docs.aws.amazon.com/lambda/latest/dg/limits.html