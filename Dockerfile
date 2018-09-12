FROM lambci/lambda:build-python3.6

ENV AWS_DEFAULT_REGION ap-southeast-1

COPY . .

CMD echo compressing package $PWD && \
    cat .lambdaignore | xargs zip -9qyr lambda.zip $PWD -x && \
    echo done compress package... && \
    echo uploading file to AWS Lambda FUNCTION_NAME: $FUNCTION_NAME && \
    aws lambda update-function-code --function-name $FUNCTION_NAME --zip-file fileb://lambda.zip && \
    echo done upload file... && \
    echo changing Lambda config of FUNCTION_NAME: $FUNCTION_NAME with HANDLER: $EXE_MODULE && \
    aws lambda update-function-configuration --function-name $FUNCTION_NAME --handler $EXE_MODULE && \
    echo tasks done...